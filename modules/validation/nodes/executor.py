import re
import traceback
from pathlib import Path
from rdflib import Graph, URIRef, RDF
from ..state import ValidationState
from modules.config import NAMESPACES, VALIDATION_RULES


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
    print(f"\n[Validation] Validating file: {file_name} ({task['description']})...")
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
        file_graph = Graph()
        file_graph.parse(file_path, format="turtle")
        target_subjects = set(file_graph.subjects())
        total_triples = len(file_graph)
        result["total_triples"] = total_triples
        result["validated_subjects"] = len(target_subjects)
        print(
            f"[Validation] [OK] Parsed {total_triples:,} triples ({len(target_subjects):,} subjects) from {file_name}."
        )
        g = Graph()
        for prefix, uri in NAMESPACES.items():
            g.bind(prefix, URIRef(uri))
        origin = task.get("origin")
        if origin == "linking" or "to_" in file_name or "2" in file_name:
            parser_output_dir = Path("modules/parser/output")
            BASE_TTL_FILES = [
                "attck_enterprise.ttl",
                "attck_ics.ttl",
                "capec.ttl",
                "cwe.ttl",
                "cve.ttl",
                "cpe.ttl",
                "icsa.ttl",
            ]
            for base_file in BASE_TTL_FILES:
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
                                    class_indicator = target_class_uri.split("#")[
                                        -1
                                    ].lower()
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
            f"[Validation] [OK] Validation finished: {result['errors_count']} Errors, {result['warnings_count']} Warnings."
        )
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[Validation] [FAIL] Critical error reading {file_name}: {e}")
        result["status"] = "failed"
        result["critical_errors_count"] = 1
        result["error_detail"] = error_msg
        result["findings"].append(
            {
                "subject": file_path,
                "property": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                "level": "CRITICAL",
                "message": f"Syntax Error / Failed to parse Turtle file: {str(e)}",
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
