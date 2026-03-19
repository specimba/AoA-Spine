from pathlib import Path

from core.brain_retrieve import RetrievalPlan, execute_retrieval_plan
from core.brain_eval import run_golden_eval
from core.brain_ingest import build_documents
from core.brain_store import BrainDocument, BrainStore, BrainStoreConfig
from core.director_bridge import run_director_cycle
from core.eval_runner import run_repo_eval
from core.embedder import HashingEmbedder
from core.vram_optimizer import VRAMOptimizer


def test_build_documents_finds_python_files():
    docs = build_documents(Path(__file__).resolve().parents[1] / "core")
    assert docs
    assert any(doc.source_kind == "code" for doc in docs)


def test_director_cycle_returns_no_evidence_for_empty_store(tmp_path: Path):
    store = BrainStore(BrainStoreConfig(db_path=tmp_path))
    result = run_director_cycle(store, "What providers are supported?", "code_lookup")
    assert result["status"] == "NO_EVIDENCE"
    assert result["telemetry"]["evidence_count"] == 0
    assert "trace" in result
    assert result["packet"]["evidence_sufficient"] is False


def test_director_cycle_returns_success_with_trace(tmp_path: Path):
    store = BrainStore(BrainStoreConfig(db_path=tmp_path))
    docs = build_documents(Path(__file__).resolve().parents[1] / "core")
    store.add_documents(docs[:8])
    result = run_director_cycle(
        store,
        "How does the budget strategy work?",
        "code_lookup",
        hardware_profile="8gb",
        top_k=3,
    )
    assert result["status"] == "SUCCESS"
    assert result["evidence_count"] > 0
    assert result["telemetry"]["retrieval_executed"] is True
    assert result["trace"]["preflight"]["budget"]["safety_gate"] is True
    assert result["packet"]["ownership_locked"] is True
    assert result["packet"]["primary_owner"] == result["packet"]["target_lane"]


def test_director_cycle_preflight_refuses_oversized_request(tmp_path: Path):
    store = BrainStore(BrainStoreConfig(db_path=tmp_path))
    request_text = "token " * 12000
    result = run_director_cycle(
        store,
        request_text,
        "code_lookup",
        hardware_profile="micro",
        top_k=10,
    )
    assert result["status"] == "REFUSED_PRECHECK"
    assert result["telemetry"]["retrieval_executed"] is False


def test_vram_optimizer_refuses_overflow():
    optimizer = VRAMOptimizer("4gb")
    result = optimizer.get_budget_map(50000)
    assert result["safety_gate"] is False


def test_vram_optimizer_exposes_supported_profiles():
    profiles = VRAMOptimizer.supported_profiles()
    assert "4gb" in profiles
    assert "8gb" in profiles
    assert "cpu-only" in profiles


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


def test_hashing_embedder_preserves_local_similarity():
    embedder = HashingEmbedder()
    query_vector, similar_vector, different_vector = embedder.embed_texts(
        [
            "provider support for spotify youtube imports",
            "spotify youtube provider integration import path",
            "gpu kv cache overflow budget policy",
        ]
    )

    similar_score = sum(a * b for a, b in zip(query_vector, similar_vector))
    different_score = sum(a * b for a, b in zip(query_vector, different_vector))
    assert similar_score > different_score


def test_execute_retrieval_plan_prefers_relevant_code_chunk(tmp_path: Path):
    store = BrainStore(BrainStoreConfig(db_path=tmp_path))
    store.add_documents(
        [
            BrainDocument(
                doc_id="doc-code",
                text="def get_supported_providers(): return ['spotify', 'youtube']",
                source_path="core/providers.py",
                source_kind="code",
                title="providers.py",
            ),
            BrainDocument(
                doc_id="doc-guide",
                text="The release checklist covers packaging and smoke tests.",
                source_path="README.md",
                source_kind="doc",
                title="README.md",
            ),
        ]
    )

    results = execute_retrieval_plan(
        store,
        RetrievalPlan(
            plan_type="code_lookup",
            query="What providers are supported?",
            top_k=1,
            embedding_backend="hash",
        ),
    )

    assert results
    assert results[0]["document"].source_path == "core/providers.py"


def test_eval_runner_produces_summary(tmp_path: Path):
    store = BrainStore(BrainStoreConfig(db_path=tmp_path))
    docs = build_documents(Path(__file__).resolve().parents[1] / "core")
    store.add_documents(docs[:10], reset=True)
    report = run_repo_eval(
        store=store,
        dataset_path=Path(__file__).resolve().parents[1] / "data" / "GOLDEN_DATASET_SEED.json",
        hardware_profile="8gb",
        embedding_backend="hash",
    )
    assert report["report_version"] == "1.0"
    assert "golden_eval" in report
