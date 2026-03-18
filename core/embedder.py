from __future__ import annotations

import hashlib


class HashingEmbedder:
    """Deterministic local hash-based vectorizer for dry runs."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            base = [byte / 255.0 for byte in digest]
            repeated = (base * ((256 // len(base)) + 1))[:256]
            vectors.append(repeated)
        return vectors


class OllamaEmbedder:
    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model
        self.dimensions = 256

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * self.dimensions for _ in texts]

