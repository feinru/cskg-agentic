import re
import traceback
from pathlib import Path

from rdflib import RDF, Graph, URIRef

from modules.config import NAMESPACES, VALIDATION_RULES

from ..state import ValidationState


def executor(state: ValidationState) -> ValidationState:
    task = state.get("current_task")
    if not task:
        print("[Validation] No active validation task.")
        validation_results = state.get("validation_results", [])
        validation_plan = state.get("validation_plan", [])
        next_task = validation_plan.pop(0) if validation_plan else {}
        return {
            "validation_plan": validation_plan,
            "current_task": next_task,
            "validation_results": validation_results,
        }
    file_name = task["file_name"]
    file_path = task["file_path"]
    link_type = task["link_type"]
    print(f"\n[Validation] Processing: {link_type}")
    result = {
        "file_name": file_name,
        "file_path": file_path,
        "link_type": link_type,
        "status": "failed",
        "total_triples": 0,
        "validated_subjects": 0,
        "critical_errors_count": 0,
        "errors_count": 0,
        "warnings_count": 0,
        "findings": [],
        "error_detail": None,
    }
    try:
        p = Path(file_path)
        file_size_mb = p.stat().st_size / (1024 * 1024)
        file_graph = Graph()

        if file_size_mb > 20.0:
            sample_lines = []
            total_triples_est = 0
            with open(p, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if idx < 25000:
                        sample_lines.append(line)
                    if ";" in line or line.strip().endswith("."):
                        total_triples_est += 1

            while sample_lines and not sample_lines[-1].strip().endswith("."):
                sample_lines.pop()

            file_graph.parse(data="".join(sample_lines), format="turtle")
            target_subjects = set(file_graph.subjects())
            total_triples = max(len(file_graph), total_triples_est)
            result["total_triples"] = total_triples
            result["validated_subjects"] = len(target_subjects)
            print(
                f"[{link_type}] Sampled: {len(file_graph):,} triples ({len(target_subjects):,} subjects, est. {total_triples:,} total)"
            )
        else:
            file_graph.parse(file_path, format="turtle")
            target_subjects = set(file_graph.subjects())
            total_triples = len(file_graph)
            result["total_triples"] = total_triples
            result["validated_subjects"] = len(target_subjects)
            print(
                f"[{link_type}] Parsed: {total_triples:,} triples ({len(target_subjects):,} subjects)"
            )
        g = Graph()
        for prefix, uri in NAMESPACES.items():
            g.bind(prefix, URIRef(uri))
        origin = task.get("origin")
        if origin == "linking" or "to_" in file_name or "2" in file_name:
            parser_output_dir = Path("modules/parser/output")
            link_prefix = file_name.replace(".ttl", "").lower()
            relevant_bases = set()
            if "cwe" in link_prefix:
                relevant_bases.add("cwe.ttl")
            if "capec" in link_prefix:
                relevant_bases.add("capec.ttl")
            if "attck" in link_prefix or "attack" in link_prefix:
                relevant_bases.update(
                    [
                        "attck_enterprise.ttl",
                        "attck_ics.ttl",
                        "attck_mobile.ttl",
                    ]
                )
            if "icsa" in link_prefix:
                relevant_bases.add("icsa.ttl")
            if "epss" in link_prefix and file_size_mb < 50.0:
                relevant_bases.add("epss.ttl")
            if "d3fend" in link_prefix:
                relevant_bases.add("d3fend.ttl")

            for base_file in sorted(relevant_bases):
                base_path = parser_output_dir / base_file
                if base_path.exists():
                    g.parse(str(base_path), format="turtle")
        for triple in file_graph:
            g.add(triple)
        for subj in sorted(target_subjects):
            if not isinstance(subj, URIRef):
                continue
            types = list(g.objects(subj, RDF.type))
            if not types:
                result["findings"].append(
                    {
                        "subject": str(subj),
                        "property": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                        "level": "WARNING",
                        "message": "Entity lacks formal class declaration (rdf:type).",
                        "rule": "Ontology Conformance Check",
                    }
                )
                result["warnings_count"] += 1
                continue
            for subj_type in types:
                type_str = str(subj_type)
                if type_str in VALIDATION_RULES:
                    rules = VALIDATION_RULES[type_str]
                    if "mandatory_properties" in rules:
                        for prop_uri, prop_rule in rules[
                            "mandatory_properties"
                        ].items():
                            pred_ref = URIRef(prop_uri)
                            values = list(g.objects(subj, pred_ref))
                            if not values:
                                severity = prop_rule.get("severity", "WARNING")
                                result["findings"].append(
                                    {
                                        "subject": str(subj),
                                        "property": prop_uri,
                                        "level": severity,
                                        "message": f"Missing mandatory property: {prop_rule.get('description', '')}",
                                        "rule": "Missing Mandatory Triple Detection",
                                    }
                                )
                                if severity == "ERROR":
                                    result["errors_count"] += 1
                                else:
                                    result["warnings_count"] += 1
                            elif "regex" in prop_rule:
                                pattern = prop_rule["regex"]
                                for val in values:
                                    val_str = str(val)
                                    if not re.match(pattern, val_str):
                                        result["findings"].append(
                                            {
                                                "subject": str(subj),
                                                "property": prop_uri,
                                                "level": "ERROR",
                                                "message": f"Literal format anomaly '{val_str}' does not match regex '{pattern}'. {prop_rule.get('description', '')}",
                                                "rule": "Format Regex & Value Check",
                                            }
                                        )
                                        result["errors_count"] += 1
                    if "links" in rules:
                        for prop_uri, link_rule in rules["links"].items():
                            pred_ref = URIRef(prop_uri)
                            links = list(g.objects(subj, pred_ref))
                            if not links:
                                if origin != "parser":
                                    severity = link_rule.get("severity", "WARNING")
                                    result["findings"].append(
                                        {
                                            "subject": str(subj),
                                            "property": prop_uri,
                                            "level": severity,
                                            "message": f"Missing relation to class {link_rule['target_class'].split('#')[-1]}: {link_rule.get('description', '')}",
                                            "rule": "Missing Relationship Link",
                                        }
                                    )
                                    if severity == "ERROR":
                                        result["errors_count"] += 1
                                    else:
                                        result["warnings_count"] += 1
                            else:
                                target_class_uri = link_rule["target_class"]
                                for target in links:
                                    target_str = str(target)
                                    target_types = list(g.objects(target, RDF.type))
                                    has_proper_type = (
                                        URIRef(target_class_uri) in target_types
                                    )
                                    raw_indicator = target_class_uri.split("#")[
                                        -1
                                    ].lower()
                                    class_indicator = (
                                        "attack"
                                        if "attack" in raw_indicator
                                        else raw_indicator
                                    )
                                    has_proper_uri_prefix = (
                                        f"/{class_indicator}/" in target_str
                                        or f"#{class_indicator}" in target_str
                                    )
                                    if not has_proper_type and (
                                        not has_proper_uri_prefix
                                    ):
                                        result["findings"].append(
                                            {
                                                "subject": str(subj),
                                                "property": prop_uri,
                                                "level": link_rule.get(
                                                    "severity", "WARNING"
                                                ),
                                                "message": f"Broken Link or reference anomaly: Object '{target_str}' is not of type {class_indicator.upper()}.",
                                                "rule": "Broken Link & Target Type Check",
                                            }
                                        )
                                        if link_rule.get("severity") == "ERROR":
                                            result["errors_count"] += 1
                                        else:
                                            result["warnings_count"] += 1
        result["status"] = "success"
        print(
            f"[{link_type}] Result: {result['errors_count']} Errors, {result['warnings_count']} Warnings"
        )
    except (OSError, ValueError, RuntimeError, KeyError) as e:
        error_msg = f"{e!s}\n{traceback.format_exc()}"
        print(f"[{link_type}] Error: Critical failure reading {file_name}: {e}")
        result["status"] = "failed"
        result["critical_errors_count"] = 1
        result["error_detail"] = error_msg
        result["findings"].append(
            {
                "subject": file_path,
                "property": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                "level": "CRITICAL",
                "message": f"Syntax Error / Failed to parse Turtle file: {e!s}",
                "rule": "RDF Syntax Parser Check",
            }
        )
    validation_results = state.get("validation_results", [])
    validation_results.append(result)
    validation_plan = state.get("validation_plan", [])
    next_task = validation_plan.pop(0) if validation_plan else {}
    return {
        "validation_plan": validation_plan,
        "current_task": next_task,
        "validation_results": validation_results,
    }
