from pathlib import Path

from core.brain_evidence import build_agent_packet, build_evidence_pack
from core.brain_ingest import build_documents
from core.brain_store import BrainDocument, BrainStore, BrainStoreConfig


def test_brain_store_upserts_existing_doc_id(tmp_path: Path):
    store = BrainStore(BrainStoreConfig(db_path=tmp_path))

    original = BrainDocument(
        doc_id="same-doc",
        text="original text",
        source_path="core/example.py",
        source_kind="code",
        title="example.py",
        source_area="runtime",
        metadata={"chunk": 0},
    )
    updated = BrainDocument(
        doc_id="same-doc",
        text="updated text",
        source_path="core/example.py",
        source_kind="code",
        title="example.py",
        source_area="runtime",
        metadata={"chunk": 0, "rev": 2},
    )

    store.add_documents([original])
    store.add_documents([updated])

    docs = store.get_documents()
    assert len(docs) == 1
    assert docs[0].text == "updated text"
    assert docs[0].metadata["rev"] == 2


def test_brain_store_reset_replaces_existing_collection(tmp_path: Path):
    store = BrainStore(BrainStoreConfig(db_path=tmp_path))
    first = BrainDocument(
        doc_id="doc-one",
        text="first",
        source_path="docs/one.md",
        source_kind="doc",
        title="one.md",
        source_area="docs",
    )
    second = BrainDocument(
        doc_id="doc-two",
        text="second",
        source_path="docs/two.md",
        source_kind="doc",
        title="two.md",
        source_area="docs",
    )

    store.add_documents([first])
    store.add_documents([second], reset=True)

    docs = store.get_documents()
    assert [doc.doc_id for doc in docs] == ["doc-two"]


def test_build_documents_includes_source_area_and_chunk_metadata(tmp_path: Path):
    runtime_file = tmp_path / "core" / "service.py"
    runtime_file.parent.mkdir(parents=True, exist_ok=True)
    runtime_file.write_text("def useful_function():\n    return 42\n", encoding="utf-8")

    docs_file = tmp_path / "README.md"
    docs_file.write_text("Project notes", encoding="utf-8")

    documents = build_documents(tmp_path)
    runtime_doc = next(doc for doc in documents if Path(doc.source_path).as_posix() == "core/service.py")
    docs_doc = next(doc for doc in documents if Path(doc.source_path).as_posix() == "README.md")

    assert runtime_doc.source_area == "runtime"
    assert runtime_doc.metadata["chunk"] == 0
    assert runtime_doc.metadata["chunk_count"] >= 1
    assert runtime_doc.metadata["chunk_end"] > runtime_doc.metadata["chunk_start"]
    assert docs_doc.source_area == "docs"


def test_build_evidence_pack_returns_basic_grounding_fields():
    document = BrainDocument(
        doc_id="abc123",
        text="This is an evidence snippet that supports the answer.",
        source_path="core/module.py",
        source_kind="code",
        title="module.py",
        source_area="runtime",
        metadata={"chunk": 0, "chunk_start": 0, "chunk_end": 52},
    )

    pack = build_evidence_pack([{"document": document, "score": 0.875}], top_k=1, excerpt_chars=20)

    assert pack["evidence_count"] == 1
    assert pack["sources"][0]["doc_id"] == "abc123"
    assert pack["sources"][0]["source_area"] == "runtime"
    assert pack["sources"][0]["score"] == 0.875
    assert pack["sources"][0]["excerpt"] == "This is an evidence"


def test_build_agent_packet_wraps_evidence_with_contract_fields():
    evidence_pack = {
        "evidence_count": 1,
        "sources": [{"doc_id": "abc123", "source_path": "core/module.py"}],
        "evidence_token_count": 12,
    }
    packet = build_agent_packet(
        request_text="Explain the module",
        plan_type="code_lookup",
        evidence_pack=evidence_pack,
        owner_lane="director",
        target_lane="implementation",
        routing_reason="grounded_answer_ready",
        confidence=0.8,
        evidence_sufficient=True,
    )

    assert packet["packet_version"] == "1.0"
    assert packet["owner_lane"] == "director"
    assert packet["target_lane"] == "implementation"
    assert packet["ownership_locked"] is True
    assert packet["evidence_sufficient"] is True
    assert packet["evidence_count"] == 1
