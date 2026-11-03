"""Read-only comparison of teacher submissions. No weight editing or SQL execution."""
from pathlib import Path
import json
import logging
import sys
import numpy as np
import sqlglot
from sqlglot import exp

HERE = Path(__file__).resolve().parent
SQL = HERE.parent
logging.getLogger("sqlglot").setLevel(logging.CRITICAL)


def score(text, case):
    result = {"parseable_select": False, "schema_match": False, "parse_error": None}
    try:
        nodes = sqlglot.parse(text, read="sqlite", error_level=sqlglot.ErrorLevel.RAISE)
        assert len(nodes) == 1 and isinstance(nodes[0], exp.Select), "Not one SELECT statement"
        node = nodes[0]
        result["parseable_select"] = True
        tables = [t.name for t in node.find_all(exp.Table)]
        columns = [c.name if isinstance(c, exp.Column) else None for c in node.expressions]
        prohibited = any(node.args.get(k) for k in ["where", "group", "having", "qualify", "order", "limit", "offset", "joins", "distinct"])
        result["schema_match"] = bool(tables == [case["table"]] and columns == case["columns"] and not prohibited
                                     and all(isinstance(c, exp.Column) and not c.table for c in node.expressions))
    except (sqlglot.errors.SqlglotError, AssertionError, ValueError) as exc:
        result["parse_error"] = str(exc).splitlines()[0][:250] or type(exc).__name__
    return result


def summarize(folder):
    payload = json.loads((folder / "generator_weights_output.json").read_text(encoding="utf-8"))
    weights = np.asarray(payload["weights"], dtype=np.float64)
    raw = json.loads((folder / "raw_outputs.json").read_text(encoding="utf-8"))
    items = []
    for output in raw["outputs"]:
        item = {"case": output["case"], "prompt": output["request"]["prompt"],
                "raw_output": output["raw_output"], "terminated_with_eos": output["terminated_with_eos"],
                "inference_error": output["inference_error"], **score(output["raw_output"], output["case"])}
        item["desired_output"] = 'select ' + ','.join('"' + c + '"' for c in item["case"]["columns"]) + ' from "' + item["case"]["table"] + '";'
        items.append(item)
    return {"folder": str(folder), "n_values": int(weights.size), "all_finite": bool(np.isfinite(weights).all()),
            "min": float(weights.min()), "max": float(weights.max()), "max_abs": float(np.abs(weights).max()),
            "zero_count": int(np.count_nonzero(weights == 0)), "zero_fraction": float(np.mean(weights == 0)),
            "distinct_values": int(np.unique(weights).size), "n_cases": len(items),
            "schema_matches": sum(x["schema_match"] for x in items),
            "parseable_selects": sum(x["parseable_select"] for x in items),
            "unreadable_or_nonselect": sum(not x["parseable_select"] for x in items),
            "wrong_readable_selects": sum(x["parseable_select"] and not x["schema_match"] for x in items),
            "eos_count": sum(x["terminated_with_eos"] for x in items),
            "inference_errors": sum(x["inference_error"] is not None for x in items), "items": items}


if __name__ == "__main__":
    previous = summarize(SQL / "round-03-astra" / "attempt-02")
    current = summarize(HERE)
    assert [x["case"]["id"] for x in previous["items"]] == [x["case"]["id"] for x in current["items"]]
    report = {"scoring": "SQLGlot 30.11.0 SQLite parser and conservative SELECT AST comparison only; no database execution or output repair.",
              "candidate_values_modified": False, "previous": previous, "current": current}
    (HERE / "comparison_summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: {k: v for k, v in report[key].items() if k != "items"} for key in ("previous", "current")}, indent=2))
    print(json.dumps(current["items"][:4], indent=2, ensure_ascii=False))
