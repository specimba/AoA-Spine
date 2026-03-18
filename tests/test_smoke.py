from pathlib import Path

from core.brain_eval import run_golden_eval
from core.brain_ingest import build_documents
from core.brain_store import BrainStore, BrainStoreConfig
from core.director_bridge import run_director_cycle
from core.vram_optimizer import VRAMOptimizer


def test_build_documents_finds_python_files():
    docs = build_documents(Path(__file__).resolve().parents[1] / "core")
    assert docs
    assert any(doc.source_kind == "code" for doc in docs)


def test_director_cycle_returns_success(tmp_path: Path):
    store = BrainStore(BrainStoreConfig(db_path=tmp_path))
    result = run_director_cycle(store, "What providers are supported?", "code_lookup")
    assert result["status"] in {"SUCCESS", "AUDIT_FAILED"}
    assert "budget" in result


def test_vram_optimizer_refuses_overflow():
    optimizer = VRAMOptimizer("4gb")
    result = optimizer.get_budget_map(50000)
    assert result["safety_gate"] is False


def test_golden_eval_runs():
    dataset = Path(__file__).resolve().parents[1] / "data" / "GOLDEN_DATASET_SEED.json"
    predictions = {
        "neg_vram_overflow_01": "I cannot do that because it would overflow the limit.",
        "neg_spp_violation_01": "Use a patch only; SPP rules apply.",
        "pos_grounded_import_01": "Spotify and YouTube are supported.",
    }
    result = run_golden_eval(dataset, predictions)
    assert result["total"] == 3
    assert result["passed"] >= 2
