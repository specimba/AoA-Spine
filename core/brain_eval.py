from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def score_response(example: dict[str, Any], response_text: str) -> dict[str, Any]:
    lowered = response_text.lower().strip()
    checks = {
        "forbidden_signals_absent": not any(signal.lower() in lowered for signal in example.get("forbidden_signals", [])),
        "required_signals_present": all(
            any(option.lower() in lowered for option in group)
            for group in example.get("required_signal_groups", [])
        ),
    }
    return {"passed": all(checks.values()), "checks": checks}


def run_golden_eval(dataset_path: Path, predictions: dict[str, str]) -> dict[str, Any]:
    with open(dataset_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    results = [
        {"id": seed["id"], **score_response(seed, predictions.get(seed["id"], ""))}
        for seed in data.get("seeds", [])
    ]
    passed = sum(1 for result in results if result["passed"])
    total = len(results)
    return {
        "total": total,
        "passed": passed,
        "pass_rate": round((passed / total) * 100, 2) if total else 0.0,
        "results": results,
    }
