from __future__ import annotations

import hashlib
import math
import re

TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_./:-]*")


def _tokenize(text: str) -> list[str]:
    lowered = text.lower()
    matches = TOKEN_PATTERN.findall(lowered)
    tokens: list[str] = []
    for token in matches:
        tokens.append(token)
        if "_" in token:
            tokens.extend(part for part in token.split("_") if part)
        camel_parts = re.findall(r"[a-z]+|[A-Z][a-z]*|\d+", token)
        if len(camel_parts) > 1:
            tokens.extend(part.lower() for part in camel_parts if part)
    return tokens


def _stable_index(token: str, salt: str, dimensions: int) -> int:
    digest = hashlib.blake2b(f"{salt}:{token}".encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dimensions


def _stable_sign(token: str) -> float:
    digest = hashlib.blake2b(f"sign:{token}".encode("utf-8"), digest_size=2).digest()
    return 1.0 if digest[0] % 2 == 0 else -1.0


class HashingEmbedder:
    """Deterministic local feature-hashing embedder for offline retrieval."""

    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            tokens = _tokenize(text)
            if not tokens:
                vectors.append(vector)
                continue

            for token in tokens:
                vector[_stable_index(token, "token", self.dimensions)] += _stable_sign(token)

                for size in (3, 4):
                    if len(token) < size:
                        continue
                    for index in range(len(token) - size + 1):
                        gram = token[index : index + size]
                        vector[_stable_index(gram, f"char{size}", self.dimensions)] += 0.35 * _stable_sign(gram)

            magnitude = math.sqrt(sum(value * value for value in vector))
            if magnitude > 0:
                vector = [value / magnitude for value in vector]

            vectors.append(vector)
        return vectors


class OllamaEmbedder:
    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model
        self.dimensions = 256
        self.fallback = HashingEmbedder(dimensions=self.dimensions)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.fallback.embed_texts(texts)
