from pathlib import Path

from core.brain_ingest import build_documents
from core.brain_store import BrainStore, BrainStoreConfig
from core.eval_runner import run_repo_eval, write_eval_report


def test_write_eval_report_creates_manifest_and_task_artifacts(tmp_path: Path):
    store = BrainStore(BrainStoreConfig(db_path=tmp_path / "db"))
    docs = build_documents(Path(__file__).resolve().parents[1] / "core")
    store.add_documents(docs[:10], reset=True)

    report = run_repo_eval(
        store=store,
        dataset_path=Path(__file__).resolve().parents[1] / "data" / "GOLDEN_DATASET_SEED.json",
        hardware_profile="8gb",
        embedding_backend="hash",
    )
    report_path = write_eval_report(report, tmp_path / "reports" / "eval-report.json")
    run_dir = report_path.parent

    assert report_path.exists()
    assert (run_dir / "task_results.jsonl").exists()
    assert (run_dir / "summary_by_method.csv").exists()
    assert (run_dir / "run_manifest.json").exists()
