import json
import traceback
from pathlib import Path
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF
from modules.config import VOCAB_NS, RESOURCE_BASE, PARSER_OUTPUT_DIR
from ..state import ParserState
from ..parsers.jparser import JSONParser
from ..parsers.xparser import XMLParser
from ..mapper import OntologyMapper


def build_subject_uri(source_key: str, entity_id: str, mapped: dict = None) -> str:
    uri_key = mapped.get("__uri_key__") if mapped else None
    if uri_key:
        if source_key.startswith("attck"):
            return f"{RESOURCE_BASE}attack/{uri_key}"
        return f"{RESOURCE_BASE}{source_key}/{uri_key}"
    if source_key.startswith("attck"):
        slug = entity_id.replace("attack-pattern--", "")
        return f"{RESOURCE_BASE}attack/{slug}"
    return f"{RESOURCE_BASE}{source_key}/{entity_id}"


def executor(state: ParserState) -> ParserState:
    task = state.get("current_task")
    if not task:
        print("[Parser] No task to execute.")
        parsed_results = state.get("parsed_results", [])
        parse_plan = state.get("parse_plan", [])
        next_task = parse_plan.pop(0) if parse_plan else {}
        return {
            "parse_plan": parse_plan,
            "current_task": next_task,
            "parsed_results": parsed_results,
        }
    source = task["source"]
    file_path = task["file_path"]
    parser_type = task["parser_type"]
    print(f"[Parser] Parsing {source} using {parser_type} parser...")
    result = {
        "source": source,
        "status": "failed",
        "entities_count": 0,
        "error": None,
        "output_file": None,
    }
    try:
        if parser_type == "json":
            parser = JSONParser(source, file_path)
        elif parser_type == "xml":
            parser = XMLParser(source, file_path)
        else:
            raise ValueError(f"Unknown parser type: {parser_type}")
        raw_entities = parser.parse()
        print(f"[Parser] Extracted {len(raw_entities)} raw entities from {source}.")
        source_key = source.lower()
        out_dir = PARSER_OUTPUT_DIR
        mapper = OntologyMapper()
        vocab_uri = VOCAB_NS.get(
            source_key, f"http://w3id.org/sepses/vocab/ref/{source_key}#"
        )
        SEPSES = Namespace(vocab_uri)
        g = Graph()
        g.bind(source_key if not source_key.startswith("attck") else "attck", SEPSES)
        skipped = 0
        for entity in raw_entities:
            mapped = mapper.map_entity(source, entity)
            if not mapped:
                skipped += 1
                continue
            entity_id = (
                mapped.get("sepses:id")
                or mapped.get("sepses:cveID")
                or mapped.get("sepses:cpe23Uri")
            )
            if not entity_id:
                skipped += 1
                continue
            subject = URIRef(build_subject_uri(source_key, str(entity_id), mapped))
            rdf_type = mapped.get("@type", "").replace("sepses:", "")
            if rdf_type:
                g.add((subject, RDF.type, SEPSES[rdf_type]))
            for key, value in mapped.items():
                if key.startswith("@") or not key.startswith("sepses:"):
                    continue
                pred_name = key.replace("sepses:", "")
                if isinstance(value, list):
                    for v in value:
                        if v:
                            if pred_name == "hasCWE" and str(v).startswith("sepses:"):
                                cwe_val = str(v).replace("sepses:", "")
                                g.add(
                                    (
                                        subject,
                                        SEPSES[pred_name],
                                        URIRef(
                                            f"http://w3id.org/sepses/resource/cwe/{cwe_val}"
                                        ),
                                    )
                                )
                            else:
                                g.add((subject, SEPSES[pred_name], Literal(str(v))))
                else:
                    g.add((subject, SEPSES[pred_name], Literal(str(value))))
        print(
            f"[Parser] Built RDF graph: {len(g)} triples ({skipped} entities skipped)."
        )
        out_ttl = out_dir / f"{source}.ttl"
        g.serialize(destination=str(out_ttl), format="turtle")
        print(f"[Parser] TTL saved to {out_ttl}.")
        result["status"] = "success"
        result["entities_count"] = len(raw_entities) - skipped
        result["output_file"] = str(out_ttl)
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[Parser] Error processing {source}: {error_msg}")
        result["error"] = str(e)
    parsed_results = state.get("parsed_results", [])
    parsed_results.append(result)
    parse_plan = state.get("parse_plan", [])
    next_task = parse_plan.pop(0) if parse_plan else {}
    return {
        "parse_plan": parse_plan,
        "current_task": next_task,
        "parsed_results": parsed_results,
    }
