from __future__ import annotations

import json
import math
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:
    import lancedb
except Exception:
    lancedb = None


@dataclass
class BrainDocument:
    doc_id: str
    text: str
    source_path: str
    source_kind: str
    title: str
    source_area: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None


@dataclass
class BrainStoreConfig:
    db_path: Path
    collection_name: str = "sequence_memory"
    embedding_model: str = "nomic-embed-text"


class BrainStore:
    def __init__(self, config: BrainStoreConfig):
        self.config = config
        self.config.db_path.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.config.db_path / f"{self.config.collection_name}.jsonl"
        self._lancedb_path = self.config.db_path / "lancedb"

    def describe(self) -> dict[str, Any]:
        return {
            "db_path": str(self.config.db_path),
            "collection_name": self.config.collection_name,
            "lancedb_enabled": lancedb is not None,
            "document_count": sum(1 for _ in self.iter_documents()),
        }

    def iter_documents(self) -> Iterable[BrainDocument]:
        if not self.jsonl_path.exists():
            return iter(())
        return self._iter_document_stream()

    def _iter_document_stream(self) -> Iterable[BrainDocument]:
        with open(self.jsonl_path, "r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                yield BrainDocument(**json.loads(line))

    def get_documents(self) -> list[BrainDocument]:
        return list(self.iter_documents())

    def reset(self) -> None:
        if self.jsonl_path.exists():
            self.jsonl_path.unlink()
        if self._lancedb_path.exists():
            shutil.rmtree(self._lancedb_path)

    def add_documents(self, documents: list[BrainDocument], *, reset: bool = False) -> None:
        existing_docs = [] if reset else self.get_documents()
        merged_docs = self._merge_documents(existing_docs, documents)
        self._write_documents(merged_docs)
        self._mirror_into_lancedb(documents)

    def search_documents(
        self,
        query: str,
        top_k: int = 5,
        source_kinds: set[str] | None = None,
        query_embedding: list[float] | None = None,
        plan_type: str | None = None,
        query_profile: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        query_tokens = set(query.lower().split())
        must_terms = set((query_profile or {}).get("must_terms", []))
        boost_terms = set((query_profile or {}).get("boost_terms", []))
        downweight_areas = set((query_profile or {}).get("downweight_areas", []))

        for doc in self.iter_documents():
            if source_kinds and doc.source_kind not in source_kinds:
                continue

            lexical_score = self._calculate_lexical_score(query_tokens, doc.text.lower())
            semantic_score = 0.0
            if query_embedding and doc.embedding:
                semantic_score = self._cosine_similarity(query_embedding, doc.embedding)

            metadata_text = " ".join(
                [
                    doc.source_path.lower(),
                    doc.title.lower(),
                    doc.source_area.lower(),
                    " ".join(str(value).lower() for value in doc.metadata.values()),
                ]
            )
            must_coverage = sum(1 for term in must_terms if term in doc.text.lower() or term in metadata_text)
            must_bonus = 0.25 * (must_coverage / max(len(must_terms), 1)) if must_terms else 0.0
            boost_bonus = 0.10 * sum(1 for term in boost_terms if term in metadata_text)
            source_area_bias = self._source_area_bias(plan_type, doc)
            if doc.source_area in downweight_areas:
                source_area_bias -= 0.30

            final_score = (lexical_score * 0.45) + (semantic_score * 0.55) + must_bonus + boost_bonus + source_area_bias
            results.append({"document": doc, "score": final_score})

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[: top_k * 3]

    def _calculate_lexical_score(self, query_tokens: set[str], doc_text: str) -> float:
        if not query_tokens:
            return 0.0
        doc_tokens = set(doc_text.split())
        overlap = query_tokens.intersection(doc_tokens)
        return len(overlap) / len(query_tokens)

    @staticmethod
    def _source_area_bias(plan_type: str | None, document: BrainDocument) -> float:
        if plan_type == "code_lookup" and document.source_area == "runtime":
            return 0.22
        if plan_type == "code_lookup" and document.source_area == "docs":
            return 0.04
        if plan_type in {"policy_lookup", "doc_lookup", "mission_lookup"} and document.source_area == "docs":
            return 0.08
        if document.source_area == "tests":
            return -0.20
        return 0.0

    def _merge_documents(
        self,
        existing_docs: list[BrainDocument],
        new_docs: list[BrainDocument],
    ) -> list[BrainDocument]:
        merged: dict[str, BrainDocument] = {doc.doc_id: doc for doc in existing_docs}
        for doc in new_docs:
            merged[doc.doc_id] = doc
        return list(merged.values())

    def _write_documents(self, documents: list[BrainDocument]) -> None:
        with open(self.jsonl_path, "w", encoding="utf-8") as handle:
            for doc in documents:
                handle.write(json.dumps(asdict(doc), ensure_ascii=False) + "\n")

    @staticmethod
    def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a * a for a in v1))
        mag2 = math.sqrt(sum(b * b for b in v2))
        return dot / (mag1 * mag2) if mag1 > 0 and mag2 > 0 else 0.0

    def _mirror_into_lancedb(self, documents: list[BrainDocument]) -> None:
        if lancedb is None or not documents:
            return
        db = lancedb.connect(str(self._lancedb_path))
        del db
