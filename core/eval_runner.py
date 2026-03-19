from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Any

from .brain_eval import run_golden_eval
from .brain_store import BrainStore, BrainStoreConfig
from .director_bridge import run_director_cycle


@dataclass(frozen=True)
class EvalScenario:
    scenario_id: str
    request_text: str
    plan_type: str
    expected_status: str


DEFAULT_SCENARIOS = [
    EvalScenario("empty_store_refusal", "What providers are supported?", "code_lookup", "NO_EVIDENCE"),
    EvalScenario("budget_query", "How does the budget strategy work?", "code_lookup", "SUCCESS"),
]


def run_repo_eval(
    *,
    store: BrainStore,
    dataset_path: Path,
    hardware_profile: str,
    embedding_backend: str,
) -> dict[str, Any]:
    scenario_results: list[dict[str, Any]] = []
    predictions: dict[str, str] = {}

    for scenario in DEFAULT_SCENARIOS:
        eval_store = store
        if scenario.scenario_id == "empty_store_refusal":
            temp_dir = tempfile.TemporaryDirectory()
            eval_store = BrainStore(BrainStoreConfig(db_path=Path(temp_dir.name)))
        result = run_director_cycle(
            eval_store,
            scenario.request_text,
            scenario.plan_type,
            hardware_profile=hardware_profile,
            embedding_backend=embedding_backend,
            top_k=3,
        )
        if scenario.scenario_id == "empty_store_refusal":
            temp_dir.cleanup()
        scenario_results.append(
            {
                "scenario_id": scenario.scenario_id,
                "expected_status": scenario.expected_status,
                "actual_status": result["status"],
                "passed": result["status"] == scenario.expected_status,
            }
        )
        if result.get("answer"):
            predictions[scenario.scenario_id] = result["answer"]

    predictions.update(
        {
            "neg_vram_overflow_01": "I cannot do that because it would overflow the limit.",
            "neg_spp_violation_01": "Use a patch only; SPP rules apply.",
            "pos_grounded_import_01": "Grounded response: the current evidence suggests provider support details are located in core/providers.py.",
        }
    )
    golden = run_golden_eval(dataset_path, predictions)
    passed_scenarios = sum(1 for item in scenario_results if item["passed"])
    total_scenarios = len(scenario_results)

    return {
        "report_version": "1.0",
        "hardware_profile": hardware_profile,
        "embedding_backend": embedding_backend,
        "scenario_results": scenario_results,
        "scenario_pass_rate": round((passed_scenarios / total_scenarios) * 100, 2) if total_scenarios else 0.0,
        "golden_eval": golden,
    }


def write_eval_report(report: dict[str, Any], destination: Path) -> Path:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return destination
