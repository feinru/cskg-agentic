import traceback
from pathlib import Path

from pyshacl import validate
from rdflib import RDF, Graph, Namespace

from modules.config import SHACL_SHAPES_DIR
from ..state import ValidationState

SH = Namespace("http://www.w3.org/ns/shacl#")

_SHACL_SHAPES_GRAPH: Graph | None = None


def get_shacl_shapes_graph() -> Graph:
    global _SHACL_SHAPES_GRAPH
    if _SHACL_SHAPES_GRAPH is None:
        shapes_g = Graph()
        for shape_file in sorted(SHACL_SHAPES_DIR.glob("*.ttl")):
            shapes_g.parse(str(shape_file), format="turtle")
        _SHACL_SHAPES_GRAPH = shapes_g
    return _SHACL_SHAPES_GRAPH


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
    print(f"\n[Validation] W3C SHACL validating: {link_type} ({file_name})")

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

        if file_size_mb > 15.0:
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

        shapes_graph = get_shacl_shapes_graph()
        conforms, results_graph, results_text = validate(
            data_graph=file_graph,
            shacl_graph=shapes_graph,
            inference="none",
            abort_on_first_error=False,
        )

        for res in results_graph.subjects(RDF.type, SH.ValidationResult):
            sev = results_graph.value(res, SH.resultSeverity)
            focus_node = results_graph.value(res, SH.focusNode)
            result_path = results_graph.value(res, SH.resultPath)
            result_msg = results_graph.value(res, SH.resultMessage)
            source_shape = results_graph.value(res, SH.sourceShape)
            source_constraint = results_graph.value(res, SH.sourceConstraintComponent)

            if sev == SH.Violation:
                result["errors_count"] += 1
                level = "ERROR"
            elif sev == SH.Warning:
                result["warnings_count"] += 1
                level = "WARNING"
            else:
                level = "INFO"

            if len(result["findings"]) < 200:
                result["findings"].append(
                    {
                        "subject": str(focus_node) if focus_node else str(file_path),
                        "property": str(result_path) if result_path else "",
                        "level": level,
                        "message": str(result_msg) if result_msg else "SHACL constraint violation",
                        "rule": str(source_shape or source_constraint or "W3C SHACL Shape"),
                    }
                )

        result["status"] = "success"
        print(
            f"[{link_type}] SHACL Conforms: {conforms} | {result['errors_count']} Violations, {result['warnings_count']} Warnings"
        )

    except (OSError, ValueError, RuntimeError, KeyError) as e:
        error_msg = f"{e!s}\n{traceback.format_exc()}"
        print(f"[{link_type}] Error: Critical validation failure on {file_name}: {e}")
        result["status"] = "failed"
        result["critical_errors_count"] = 1
        result["error_detail"] = error_msg
        result["findings"].append(
            {
                "subject": file_path,
                "property": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                "level": "CRITICAL",
                "message": f"Syntax Error / Failed to parse or validate Turtle graph: {e!s}",
                "rule": "W3C SHACL Validation Parser",
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
