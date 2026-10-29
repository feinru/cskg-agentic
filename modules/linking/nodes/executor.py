import re
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

import ijson
import orjson
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

from modules.config import (
    CACHE_DIR,
    LINKING_OUTPUT_DIR,
    NAMESPACES,
)
from modules.config import (
    RESOURCE_BASE_MAP as RESOURCE_BASE,
)

from ..state import LinkingState

NS_CVE = Namespace(NAMESPACES["cve"])
NS_CWE = Namespace(NAMESPACES["cwe"])
NS_CAPEC = Namespace(NAMESPACES["capec"])
NS_CPE = Namespace(NAMESPACES["cpe"])
NS_CVSS = Namespace(NAMESPACES["cvss"])
NS_ATTCK = Namespace(NAMESPACES["attck"])
NS_ICSA = Namespace(NAMESPACES["icsa"])
NS_EPSS = Namespace(NAMESPACES["epss"])
NS_D3FEND = Namespace(NAMESPACES["d3fend"])


def executor(state: LinkingState) -> LinkingState:
    task = state.get("current_task")
    if not task:
        print("[Linking] No task to execute.")
        linked_results = state.get("linked_results", [])
        link_plan = state.get("link_plan", [])
        next_task = link_plan.pop(0) if link_plan else {}
        return {
            "link_plan": link_plan,
            "current_task": next_task,
            "linked_results": linked_results,
        }
    link_type = task["link_type"]
    predicate_str = task["predicate"]
    subject_files = task.get("subject_files", [])
    print(f"\n[Linking] Processing: {link_type}")
    print(f"[{link_type}] Predicate: {predicate_str}")
    result = {
        "link_type": link_type,
        "predicate": predicate_str,
        "status": "failed",
        "triples_count": 0,
        "output_file": None,
        "error": None,
    }
    try:
        g = Graph()
        for prefix, uri in NAMESPACES.items():
            g.bind(prefix, Namespace(uri))
        predicate_uri = _resolve_predicate(predicate_str)
        triples_count = 0
        out_dir = LINKING_OUTPUT_DIR
        out_file = out_dir / f"{link_type}.ttl"
        is_streamed = False

        if link_type in ("cve2cwe", "cve_to_cwe"):
            triples_count = _link_cve_to_cwe_stream(
                out_file, subject_files, predicate_uri
            )
            is_streamed = True
        elif link_type in ("cve2cpe", "cve_to_cpe"):
            triples_count = _link_cve_to_cpe_stream(
                out_file, subject_files, predicate_uri
            )
            is_streamed = True
        elif link_type in ("cve2epss", "cve_to_epss"):
            target_files = task.get("object_files") or subject_files
            triples_count = _link_cve_to_epss_stream(
                out_file, target_files, predicate_uri
            )
            is_streamed = True
        elif link_type in ("cwe2capec", "cwe_to_capec"):
            triples_count = _link_cwe_to_capec(g, subject_files, predicate_uri)
        elif link_type in ("capec2attck", "capec_to_attck"):
            triples_count = _link_capec_to_attck(g, subject_files, predicate_uri)
        elif link_type in ("icsa2cve", "icsa_to_cve"):
            triples_count = _link_icsa_to_cve(g, subject_files, predicate_uri)
        elif link_type in ("d3fend2attck", "d3fend_to_attck"):
            triples_count = _link_d3fend_to_attck(g, subject_files, predicate_uri)
        else:
            print(f"[{link_type}] WARNING: Unknown linking type")

        if not is_streamed:
            g.serialize(destination=str(out_file), format="turtle")
        result["status"] = "success"
        result["triples_count"] = triples_count
        result["output_file"] = str(out_file)
        print(f"[{link_type}] Success: {triples_count:,} triples written -> {out_file}")
    except (OSError, ValueError, RuntimeError, KeyError) as e:
        error_msg = f"{e!s}\n{traceback.format_exc()}"
        print(f"[{link_type}] Error: {error_msg}")
        result["error"] = str(e)
    linked_results = state.get("linked_results", [])
    linked_results.append(result)
    link_plan = state.get("link_plan", [])
    next_task = link_plan.pop(0) if link_plan else {}
    return {
        "link_plan": link_plan,
        "current_task": next_task,
        "linked_results": linked_results,
    }


def _resolve_predicate(predicate_str: str) -> URIRef:
    if ":" in predicate_str:
        prefix, local = predicate_str.split(":", 1)
        if prefix in NAMESPACES:
            return URIRef(NAMESPACES[prefix] + local)
    return URIRef(predicate_str)


def _iter_json_data(file_path: str):
    p = Path(file_path)
    file_size_mb = p.stat().st_size / (1024 * 1024)
    if file_size_mb > 10.0:
        with open(p, "rb") as f:
            first = f.read(1)
            while first in b" \t\r\n":
                first = f.read(1)
            f.seek(0)
            if first == b"[":
                for item in ijson.items(f, "item"):
                    if isinstance(item, dict):
                        yield item
            elif first == b"{":
                for k in ("vulnerabilities", "products", "objects", "scores"):
                    try:
                        f.seek(0)
                        gen = ijson.items(f, f"{k}.item")
                        first_item = next(gen)
                        if isinstance(first_item, dict):
                            yield first_item
                        for item in gen:
                            if isinstance(item, dict):
                                yield item
                        return
                    except (StopIteration, ijson.common.IncompleteJSONError):
                        continue
    else:
        with open(p, "rb") as f:
            data = orjson.loads(f.read())
        if isinstance(data, dict):
            for k in ("vulnerabilities", "products", "objects", "scores"):
                if k in data and isinstance(data[k], list):
                    yield from data[k]
                    return
            yield data
        elif isinstance(data, list):
            yield from data


def _load_json_data(file_path: str) -> dict | list:
    with open(file_path, "rb") as f:
        return orjson.loads(f.read())


def _strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _sanitize_uri_component(value: str) -> str:
    if not value:
        return value
    value = re.sub("<[^>]+>", "", value)
    value = re.sub("[\\x00-\\x1f]", "", value)
    value = re.sub("[\\s\"\\'{}<>|\\\\^`\\[\\]]", "_", value)
    return value


def _link_cve_to_cwe_stream(
    out_file: Path, subject_files: list[str], predicate: URIRef
) -> int:
    count = 0
    with open(out_file, "w", encoding="utf-8", buffering=2 * 1024 * 1024) as out_f:
        out_f.write("@prefix cve: <http://w3id.org/sepses/vocab/ref/cve#> .\n")
        out_f.write("@prefix cwe: <http://w3id.org/sepses/vocab/ref/cwe#> .\n")
        out_f.write("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n\n")

        for file_path in subject_files:
            for vuln in _iter_json_data(file_path):
                cve_data = vuln.get("cve", {})
                cve_id = cve_data.get("id")
                if not cve_id:
                    continue
                cve_id = _sanitize_uri_component(cve_id)
                subject_uri = RESOURCE_BASE["cve"] + cve_id

                cwe_refs = []
                for weakness in cve_data.get("weaknesses", []):
                    for desc in weakness.get("description", []):
                        cwe_value = desc.get("value", "")
                        if cwe_value.startswith("CWE-"):
                            cwe_refs.append(_sanitize_uri_component(cwe_value))

                if cwe_refs:
                    unique_cwes = list(dict.fromkeys(cwe_refs))
                    lines = ["a <http://w3id.org/sepses/vocab/ref/cve#CVE>"]
                    for cwe_val in unique_cwes:
                        lines.append(
                            f"<{predicate}> <{RESOURCE_BASE['cwe'] + cwe_val}>"
                        )
                        count += 1
                    out_f.write(f"<{subject_uri}> " + " ;\n    ".join(lines) + " .\n")
    return count


def _link_cve_to_cpe_stream(
    out_file: Path, subject_files: list[str], predicate: URIRef
) -> int:
    count = 0
    with open(out_file, "w", encoding="utf-8", buffering=2 * 1024 * 1024) as out_f:
        out_f.write("@prefix cve: <http://w3id.org/sepses/vocab/ref/cve#> .\n")
        out_f.write("@prefix cpe: <http://w3id.org/sepses/vocab/ref/cpe#> .\n")
        out_f.write("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n\n")

        for file_path in subject_files:
            for vuln in _iter_json_data(file_path):
                cve_data = vuln.get("cve", {})
                cve_id = cve_data.get("id")
                if not cve_id:
                    continue
                cve_id = _sanitize_uri_component(cve_id)
                subject_uri = RESOURCE_BASE["cve"] + cve_id

                cpe_uris = []
                for config in cve_data.get("configurations", []):
                    for node in config.get("nodes", []):
                        for cpe_match in node.get("cpeMatch", []):
                            cpe_uri_str = cpe_match.get("criteria", "")
                            if cpe_uri_str:
                                cpe_safe = cpe_uri_str.replace(":", "").replace("/", "")
                                cpe_safe = _sanitize_uri_component(cpe_safe)
                                cpe_uris.append(RESOURCE_BASE["cpe"] + cpe_safe)

                if cpe_uris:
                    unique_cpes = list(dict.fromkeys(cpe_uris))
                    lines = ["a <http://w3id.org/sepses/vocab/ref/cve#CVE>"]
                    for cu in unique_cpes:
                        lines.append(f"<{predicate}> <{cu}>")
                        count += 1
                    out_f.write(f"<{subject_uri}> " + " ;\n    ".join(lines) + " .\n")
    return count


def _link_cve_to_epss_stream(
    out_file: Path, target_files: list[str], predicate: URIRef
) -> int:
    count = 0
    with open(out_file, "w", encoding="utf-8", buffering=2 * 1024 * 1024) as out_f:
        out_f.write("@prefix cve: <http://w3id.org/sepses/vocab/ref/cve#> .\n")
        out_f.write("@prefix epss: <http://w3id.org/sepses/vocab/ref/epss#> .\n")
        out_f.write("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n\n")

        for file_path in target_files:
            for rec in _iter_json_data(file_path):
                cve_id = rec.get("cve") or rec.get("cveID") or rec.get("id")
                if not cve_id:
                    continue
                cve_id = _sanitize_uri_component(cve_id)
                sub_uri = RESOURCE_BASE["cve"] + cve_id
                obj_uri = RESOURCE_BASE["epss"] + cve_id
                out_f.write(
                    f"<{sub_uri}> a <http://w3id.org/sepses/vocab/ref/cve#CVE> ;\n    <{predicate}> <{obj_uri}> .\n"
                )
                count += 1
    return count


def _link_cwe_to_capec(g: Graph, subject_files: list[str], predicate: URIRef) -> int:
    count = 0
    for file_path in subject_files:
        try:
            if file_path.endswith(".xml"):
                count += _link_cwe_to_capec_xml(g, file_path, predicate)
            elif file_path.endswith(".json"):
                count += _link_cwe_to_capec_json(g, file_path, predicate)
        except (OSError, ValueError, RuntimeError, KeyError, ET.ParseError) as e:
            print(f"[Linking] Failed to process {file_path}: {e}")
            continue
    return count


def _link_cwe_to_capec_xml(g: Graph, file_path: str, predicate: URIRef) -> int:
    count = 0
    tree = ET.parse(file_path)
    root = tree.getroot()
    for elem in root.iter():
        tag = _strip_ns(elem.tag)
        if tag == "Weakness":
            cwe_id = elem.attrib.get("ID")
            if not cwe_id:
                continue
            subject_uri = URIRef(RESOURCE_BASE["cwe"] + f"CWE-{cwe_id}")
            g.add((subject_uri, RDF.type, NS_CWE.CWE))
            for child in elem.iter():
                child_tag = _strip_ns(child.tag)
                if child_tag == "Related_Attack_Pattern":
                    capec_id = child.attrib.get("CAPEC_ID")
                    if capec_id:
                        object_uri = URIRef(
                            RESOURCE_BASE["capec"] + f"CAPEC-{capec_id}"
                        )
                        g.add((subject_uri, predicate, object_uri))
                        count += 1
    return count


def _link_cwe_to_capec_json(g: Graph, file_path: str, predicate: URIRef) -> int:
    count = 0
    data = _load_json_data(file_path)
    weaknesses = []
    if isinstance(data, dict):
        weaknesses = data.get("Weaknesses", data.get("weaknesses", []))
    elif isinstance(data, list):
        weaknesses = data
    for weakness in weaknesses:
        cwe_id = weakness.get("ID") or weakness.get("id")
        if not cwe_id:
            attribs = weakness.get("attribs", {})
            cwe_id = attribs.get("ID")
        if not cwe_id:
            continue
        subject_uri = URIRef(RESOURCE_BASE["cwe"] + f"CWE-{cwe_id}")
        g.add((subject_uri, RDF.type, NS_CWE.CWE))
        related_patterns = weakness.get("Related_Attack_Patterns", [])
        if isinstance(related_patterns, dict):
            related_patterns = related_patterns.get("Related_Attack_Pattern", [])
        if isinstance(related_patterns, dict):
            related_patterns = [related_patterns]
        for pattern in related_patterns:
            capec_id = pattern.get("CAPEC_ID") or pattern.get("capec_id")
            if capec_id:
                object_uri = URIRef(RESOURCE_BASE["capec"] + f"CAPEC-{capec_id}")
                g.add((subject_uri, predicate, object_uri))
                count += 1
    return count


def _link_capec_to_attck(g: Graph, subject_files: list[str], predicate: URIRef) -> int:
    count = 0
    for file_path in subject_files:
        try:
            if file_path.endswith(".xml"):
                count += _link_capec_to_attck_xml(g, file_path, predicate)
            elif file_path.endswith(".json"):
                count += _link_capec_to_attck_json(g, file_path, predicate)
        except (OSError, ValueError, RuntimeError, KeyError, ET.ParseError) as e:
            print(f"[Linking] Failed to process {file_path}: {e}")
            continue
    return count


def _link_capec_to_attck_xml(g: Graph, file_path: str, predicate: URIRef) -> int:
    count = 0
    tree = ET.parse(file_path)
    root = tree.getroot()
    for elem in root.iter():
        tag = _strip_ns(elem.tag)
        if tag == "Attack_Pattern":
            capec_id = elem.attrib.get("ID")
            if not capec_id:
                continue
            subject_uri = URIRef(RESOURCE_BASE["capec"] + f"CAPEC-{capec_id}")
            g.add((subject_uri, RDF.type, NS_CAPEC.CAPEC))
            for child in elem.iter():
                child_tag = _strip_ns(child.tag)
                if child_tag == "Taxonomy_Mapping":
                    taxonomy_name = child.attrib.get("Taxonomy_Name", "")
                    if "ATTACK" in taxonomy_name.upper():
                        for entry in child.iter():
                            entry_tag = _strip_ns(entry.tag)
                            if entry_tag == "Entry_ID" and entry.text:
                                technique_id = entry.text.strip()
                                if not technique_id.startswith("T"):
                                    technique_id = "T" + technique_id
                                object_uri = URIRef(
                                    RESOURCE_BASE["attck"] + technique_id
                                )
                                g.add((subject_uri, predicate, object_uri))
                                count += 1
    return count


def _link_capec_to_attck_json(g: Graph, file_path: str, predicate: URIRef) -> int:
    count = 0
    data = _load_json_data(file_path)
    patterns = []
    if isinstance(data, dict):
        patterns = data.get("Attack_Patterns", data.get("attack_patterns", []))
    elif isinstance(data, list):
        patterns = data
    for pattern in patterns:
        capec_id = pattern.get("ID") or pattern.get("id")
        if not capec_id:
            attribs = pattern.get("attribs", {})
            capec_id = attribs.get("ID")
        if not capec_id:
            continue
        subject_uri = URIRef(RESOURCE_BASE["capec"] + f"CAPEC-{capec_id}")
        g.add((subject_uri, RDF.type, NS_CAPEC.CAPEC))
        taxonomy_mappings = pattern.get("Taxonomy_Mappings", [])
        if isinstance(taxonomy_mappings, dict):
            taxonomy_mappings = taxonomy_mappings.get("Taxonomy_Mapping", [])
        if isinstance(taxonomy_mappings, dict):
            taxonomy_mappings = [taxonomy_mappings]
        for mapping in taxonomy_mappings:
            taxonomy_name = mapping.get("Taxonomy_Name", "")
            if "ATTACK" in taxonomy_name.upper():
                entry_id = mapping.get("Entry_ID", "")
                if entry_id:
                    if not entry_id.startswith("T"):
                        entry_id = "T" + entry_id
                    object_uri = URIRef(RESOURCE_BASE["attck"] + entry_id)
                    g.add((subject_uri, predicate, object_uri))
                    count += 1
    return count


def _link_icsa_to_cve(g: Graph, subject_files: list[str], predicate: URIRef) -> int:
    count = 0
    for file_path in subject_files:
        try:
            data = _load_json_data(file_path)
        except (OSError, ValueError, RuntimeError, KeyError) as e:
            print(f"[Linking] Failed to read {file_path}: {e}")
            continue
        vulnerabilities = []
        if isinstance(data, dict):
            vulnerabilities = data.get("vulnerabilities", [])
        elif isinstance(data, list):
            vulnerabilities = data
        for vuln in vulnerabilities:
            cve_id = vuln.get("cveID")
            if not cve_id:
                continue
            cve_id = _sanitize_uri_component(cve_id)
            vendor = _sanitize_uri_component(vuln.get("vendorProject", "unknown"))
            product = _sanitize_uri_component(vuln.get("product", "unknown"))
            icsa_id = f"{vendor}_{product}_{cve_id}".replace(" ", "_")
            subject_uri = URIRef(RESOURCE_BASE["icsa"] + icsa_id)
            g.add((subject_uri, RDF.type, NS_ICSA.ICSA))
            object_uri = URIRef(RESOURCE_BASE["cve"] + cve_id)
            g.add((subject_uri, predicate, object_uri))
            count += 1
    return count


def _link_cve_to_epss(
    g: Graph, subject_files: list[str], object_files: list[str], predicate: URIRef
) -> int:
    count = 0
    target_files = object_files if object_files else subject_files
    for file_path in target_files:
        try:
            data = _load_json_data(file_path)
        except (OSError, ValueError, RuntimeError, KeyError) as e:
            print(f"[Linking] Failed to read {file_path}: {e}")
            continue
        records = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            records = data.get("scores", [data])
        for rec in records:
            cve_id = rec.get("cve") or rec.get("cveID") or rec.get("id")
            if not cve_id:
                continue
            cve_id = _sanitize_uri_component(cve_id)
            subject_uri = URIRef(RESOURCE_BASE["cve"] + cve_id)
            object_uri = URIRef(RESOURCE_BASE["epss"] + cve_id)
            g.add((subject_uri, RDF.type, NS_CVE.CVE))
            g.add((subject_uri, predicate, object_uri))
            count += 1
    return count


def _link_d3fend_to_attck(g: Graph, subject_files: list[str], predicate: URIRef) -> int:
    count = 0
    mappings_file = CACHE_DIR / "d3fend_mappings.json"
    if not mappings_file.exists():
        for sf in subject_files:
            if "d3fend_mappings" in sf:
                mappings_file = Path(sf)
                break
    if not mappings_file.exists():
        print("[Linking] d3fend_mappings.json not found in cache.")
        return 0
    try:
        data = _load_json_data(str(mappings_file))
        bindings = data.get("results", {}).get("bindings", [])
        for row in bindings:
            def_tech_val = row.get("def_tech", {}).get("value")
            off_tech_id = row.get("off_tech_id", {}).get("value")
            if not def_tech_val or not off_tech_id:
                continue
            def_uri = URIRef(def_tech_val)
            off_uri = URIRef(
                RESOURCE_BASE["attck"] + _sanitize_uri_component(off_tech_id)
            )
            g.add((def_uri, RDF.type, NS_D3FEND.DefensiveTechnique))
            g.add((def_uri, predicate, off_uri))
            count += 1
    except (OSError, ValueError, RuntimeError, KeyError) as e:
        print(f"[Linking] Failed to process {mappings_file}: {e}")
    return count
