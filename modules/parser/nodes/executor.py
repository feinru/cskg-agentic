import json
import re
import traceback
from typing import Any

from modules.config import PARSER_OUTPUT_DIR, RESOURCE_BASE, VOCAB_NS

from ..mapper import OntologyMapper
from ..parsers.jparser import JSONParser
from ..parsers.xparser import XMLParser
from ..state import ParserState


def _format_literal(pred_name: str, value: Any) -> str:
    if value is None:
        return '""'
    if pred_name in ("baseScore", "epssScore", "epssPercentile"):
        try:
            val_float = float(value)
            return f'"{val_float}"^^<http://www.w3.org/2001/XMLSchema#decimal>'
        except (ValueError, TypeError):
            pass
    elif pred_name in ("published", "lastModified"):
        val_str = str(value).strip()
        if re.match(
            r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})?$",
            val_str,
        ):
            return f'"{val_str}"^^<http://www.w3.org/2001/XMLSchema#dateTime>'
    elif pred_name == "isSubtechnique":
        bool_str = "true" if value and str(value).lower() in ("true", "1") else "false"
        return f'"{bool_str}"^^<http://www.w3.org/2001/XMLSchema#boolean>'

    return json.dumps(str(value))


def build_subject_uri(
    source_key: str, entity_id: str, mapped: dict | None = None
) -> str:
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
    print(f"\n[Parser] Processing: {source}")
    print(f"[{source}] Parsing using {parser_type} parser...")
    result = {
        "source": source,
        "status": "failed",
        "entities_count": 0,
        "error": None,
        "output_file": None,
    }
    try:
        if parser_type == "ttl":
            import shutil

            out_dir = PARSER_OUTPUT_DIR
            out_ttl = out_dir / f"{source}.ttl"
            shutil.copyfile(file_path, out_ttl)
            triple_est = 0
            with open(out_ttl, "r", encoding="utf-8") as f:
                triple_est = sum(
                    1
                    for line in f
                    if line.strip().endswith(".") and not line.strip().startswith("@")
                )
            print(
                f"[{source}] Stream copied and registered {triple_est:,} TTL triples -> {out_ttl}"
            )
            result["status"] = "success"
            result["entities_count"] = triple_est
            result["output_file"] = str(out_ttl)
            parsed_results = state.get("parsed_results", [])
            parsed_results.append(result)
            parse_plan = state.get("parse_plan", [])
            next_task = parse_plan.pop(0) if parse_plan else {}
            return {
                "parse_plan": parse_plan,
                "current_task": next_task,
                "parsed_results": parsed_results,
            }
        elif parser_type == "json":
            parser = JSONParser(source, file_path)
        elif parser_type == "xml":
            parser = XMLParser(source, file_path)
        else:
            raise ValueError(f"Unknown parser type: {parser_type}")
        source_key = source.lower()
        out_dir = PARSER_OUTPUT_DIR
        out_ttl = out_dir / f"{source}.ttl"
        mapper = OntologyMapper()
        vocab_uri = VOCAB_NS.get(
            source_key, f"http://w3id.org/sepses/vocab/ref/{source_key}#"
        )
        prefix_name = source_key if not source_key.startswith("attck") else "attck"

        total_extracted = 0
        skipped = 0
        triples_count = 0

        with open(out_ttl, "w", encoding="utf-8", buffering=2 * 1024 * 1024) as out_f:
            out_f.write(f"@prefix {prefix_name}: <{vocab_uri}> .\n")
            out_f.write(
                "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n"
            )
            out_f.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n")

            for entity in parser.parse_iter():
                total_extracted += 1
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

                subject_uri = build_subject_uri(source_key, str(entity_id), mapped)
                rdf_type = mapped.get("@type", "").replace("sepses:", "")

                lines = []
                if rdf_type:
                    lines.append(f"a <{vocab_uri}{rdf_type}>")
                    triples_count += 1

                for key, value in mapped.items():
                    if key.startswith("@") or not key.startswith("sepses:"):
                        continue
                    pred_name = key.replace("sepses:", "")
                    pred_uri = f"{vocab_uri}{pred_name}"
                    if isinstance(value, list):
                        for v in value:
                            if v:
                                if pred_name == "hasCWE" and str(v).startswith(
                                    "sepses:"
                                ):
                                    cwe_val = str(v).replace("sepses:", "")
                                    lines.append(
                                        f"<{pred_uri}> <http://w3id.org/sepses/resource/cwe/{cwe_val}>"
                                    )
                                else:
                                    lines.append(f"<{pred_uri}> {_format_literal(pred_name, v)}")
                                triples_count += 1
                    else:
                        lines.append(f"<{pred_uri}> {_format_literal(pred_name, value)}")
                        triples_count += 1

                if lines:
                    out_f.write(f"<{subject_uri}> " + " ;\n    ".join(lines) + " .\n")

                if total_extracted % 250000 == 0:
                    print(
                        f"[{source}] Streamed {total_extracted:,} entities ({triples_count:,} triples written)..."
                    )

        print(f"[{source}] Extracted {total_extracted:,} raw entities from {source}.")
        print(
            f"[{source}] Built RDF stream: {triples_count:,} triples ({skipped:,} entities skipped)."
        )
        print(f"[{source}] TTL saved to {out_ttl}.")
        result["status"] = "success"
        result["entities_count"] = total_extracted - skipped
        result["output_file"] = str(out_ttl)
    except (OSError, ValueError, RuntimeError, KeyError) as e:
        error_msg = f"{e!s}\n{traceback.format_exc()}"
        print(f"[{source}] Error processing: {error_msg}")
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
