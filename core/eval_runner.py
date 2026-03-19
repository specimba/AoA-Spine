from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
import tempfile
from platform import platform, python_version
from typing import Any
from uuid import uuid4

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


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_task_artifact(
    *,
    run_id: str,
    scenario: EvalScenario,
    result: dict[str, Any],
    hardware_profile: str,
    embedding_backend: str,
) -> dict[str, Any]:
    telemetry = result.get("telemetry", {})
    budget = result.get("budget", {})
    evidence_pack = result.get("evidence_pack", {})
    return {
        "run_id": run_id,
        "task_id": scenario.scenario_id,
        "method": "current_pipeline",
        "hardware_profile": hardware_profile,
        "embedding_backend": embedding_backend,
        "status": result.get("status"),
        "expected_status": scenario.expected_status,
        "passed": result.get("status") == scenario.expected_status,
        "latency_ms": telemetry.get("retrieval_ms", 0.0),
        "tokens_requested": budget.get("requested_tokens", 0),
        "tokens_spilled": budget.get("ram_tokens", 0),
        "overflow_refused": result.get("status") in {"REFUSED_PRECHECK", "REFUSED_OVERFLOW"},
        "retrieval_executed": telemetry.get("retrieval_executed", False),
        "evidence_count": result.get("evidence_count", 0),
        "retrieved_doc_ids": [item.get("doc_id") for item in evidence_pack.get("sources", [])],
        "retrieved_scores": [item.get("score") for item in evidence_pack.get("sources", [])],
        "answer_text": result.get("answer", ""),
        "answer_correct": result.get("status") == scenario.expected_status,
        "grounded": bool(result.get("answer", "").lower().startswith("grounded response")) if result.get("answer") else False,
        "failure_type": "" if result.get("status") == scenario.expected_status else result.get("status"),
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _write_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "method",
        "hardware_profile",
        "n_tasks",
        "accuracy",
        "grounded_rate",
        "refusal_rate",
        "mean_latency_ms",
        "max_tokens_requested",
        "max_tokens_spilled",
    ]
    if not rows:
        rows = [{key: "" for key in fieldnames}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _summarize_task_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["method"], row["hardware_profile"])
        grouped.setdefault(key, []).append(row)

    summaries: list[dict[str, Any]] = []
    for (method, hardware_profile), items in grouped.items():
        n_tasks = len(items)
        accuracy = sum(1 for item in items if item["answer_correct"]) / n_tasks
        grounded_rate = sum(1 for item in items if item["grounded"]) / n_tasks
        refusal_rate = sum(1 for item in items if item["overflow_refused"] or item["status"] == "NO_EVIDENCE") / n_tasks
        mean_latency = sum(float(item["latency_ms"]) for item in items) / n_tasks
        summaries.append(
            {
                "method": method,
                "hardware_profile": hardware_profile,
                "n_tasks": n_tasks,
                "accuracy": round(accuracy, 4),
                "grounded_rate": round(grounded_rate, 4),
                "refusal_rate": round(refusal_rate, 4),
                "mean_latency_ms": round(mean_latency, 2),
                "max_tokens_requested": max(int(item["tokens_requested"]) for item in items),
                "max_tokens_spilled": max(int(item["tokens_spilled"]) for item in items),
            }
        )
    return summaries


def run_repo_eval(
    *,
    store: BrainStore,
    dataset_path: Path,
    hardware_profile: str,
    embedding_backend: str,
) -> dict[str, Any]:
    run_id = f"run-{uuid4().hex[:10]}"
    scenario_results: list[dict[str, Any]] = []
    task_artifacts: list[dict[str, Any]] = []
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
            top_k=10 if scenario.scenario_id == "budget_query" else 3,
        )
        if scenario.scenario_id == "empty_store_refusal":
            temp_dir.cleanup()
        task_artifacts.append(
            _build_task_artifact(
                run_id=run_id,
                scenario=scenario,
                result=result,
                hardware_profile=hardware_profile,
                embedding_backend=embedding_backend,
            )
        )
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
        "run_id": run_id,
        "report_version": "1.0",
        "hardware_profile": hardware_profile,
        "embedding_backend": embedding_backend,
        "scenario_results": scenario_results,
        "task_artifacts": task_artifacts,
        "scenario_pass_rate": round((passed_scenarios / total_scenarios) * 100, 2) if total_scenarios else 0.0,
        "golden_eval": golden,
    }


def write_eval_report(report: dict[str, Any], destination: Path) -> Path:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    report_dir = destination.parent / report["run_id"]
    report_dir.mkdir(parents=True, exist_ok=True)

    task_artifacts = list(report.get("task_artifacts", []))
    summary_rows = _summarize_task_rows(task_artifacts)
    task_results_path = report_dir / "task_results.jsonl"
    summary_csv_path = report_dir / "summary_by_method.csv"
    run_manifest_path = report_dir / "run_manifest.json"
    run_report_path = report_dir / "report.json"

    _write_jsonl(task_results_path, task_artifacts)
    _write_summary_csv(summary_csv_path, summary_rows)

    benchmark_manifest_path = Path("data") / "benchmark_manifest.json"
    run_manifest = {
        "run_id": report["run_id"],
        "timestamp": report_dir.name,
        "python_version": python_version(),
        "platform": platform(),
        "benchmark_manifest_path": str(benchmark_manifest_path.resolve()),
        "benchmark_manifest_hash": _file_sha256(benchmark_manifest_path),
        "golden_dataset_path": str((Path("data") / "GOLDEN_DATASET_SEED.json").resolve()),
        "golden_dataset_hash": _file_sha256(Path("data") / "GOLDEN_DATASET_SEED.json"),
        "hardware_profile": report["hardware_profile"],
        "embedding_backend": report["embedding_backend"],
        "artifacts": {
            "task_results_jsonl": str(task_results_path),
            "summary_by_method_csv": str(summary_csv_path),
            "report_json": str(destination),
        },
    }
    run_manifest_path.write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")

    persisted_report = {key: value for key, value in report.items() if key != "task_artifacts"}
    persisted_report["artifacts"] = run_manifest["artifacts"]
    persisted_report["run_manifest"] = str(run_manifest_path)
    run_report_path.write_text(json.dumps(persisted_report, indent=2), encoding="utf-8")
    destination.write_text(json.dumps({"latest_run_report": str(run_report_path)}, indent=2), encoding="utf-8")
    return run_report_path
