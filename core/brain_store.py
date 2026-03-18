from __future__ import annotations

import json
import math
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

    def add_documents(self, documents: list[BrainDocument]) -> None:
        with open(self.jsonl_path, "a", encoding="utf-8") as handle:
            for doc in documents:
                handle.write(json.dumps(asdict(doc), ensure_ascii=False) + "\n")
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
        del plan_type, query_profile
        results: list[dict[str, Any]] = []
        query_tokens = set(query.lower().split())

        for doc in self.iter_documents():
            if source_kinds and doc.source_kind not in source_kinds:
                continue

            lexical_score = self._calculate_lexical_score(query_tokens, doc.text.lower())
            semantic_score = 0.0
            if query_embedding and doc.embedding:
                semantic_score = self._cosine_similarity(query_embedding, doc.embedding)

            final_score = (lexical_score * 0.3) + (semantic_score * 0.7)
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

