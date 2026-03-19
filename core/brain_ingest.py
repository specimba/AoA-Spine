from __future__ import annotations

import hashlib
from pathlib import Path

from .brain_store import BrainDocument

TEXT_EXTENSIONS = {".md", ".txt", ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".html"}
SKIP_PARTS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".brain_db"}


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start += max(1, max_chars - overlap)
    return chunks


def classify_source_area(path: Path) -> str:
    normalized = {part.lower() for part in path.parts}
    if "tests" in normalized:
        return "tests"
    if "data" in normalized:
        return "data"
    if path.name in {"pyproject.toml", "pytest.ini", ".editorconfig"}:
        return "config"
    if path.suffix.lower() in {".md", ".txt"}:
        return "docs"
    if "core" in normalized or path.suffix.lower() in {".py", ".js", ".jsx", ".ts", ".tsx"}:
        return "runtime"
    return "other"


def build_documents(root: Path) -> list[BrainDocument]:
    documents: list[BrainDocument] = []
    for path in root.rglob("*"):
        if path.is_dir() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        relative_path = path.relative_to(root)
        chunks = chunk_text(text)
        chunk_stride = 1200 - 150
        source_area = classify_source_area(relative_path)
        for index, chunk in enumerate(chunks):
            doc_id = hashlib.sha256(f"{relative_path}::{index}".encode()).hexdigest()[:12]
            chunk_start = index * chunk_stride
            chunk_end = min(chunk_start + len(chunk), len(text))
            documents.append(
                BrainDocument(
                    doc_id=doc_id,
                    text=chunk,
                    source_path=str(relative_path),
                    source_kind="code" if path.suffix.lower() in {".py", ".js", ".ts", ".tsx"} else "doc",
                    title=path.name,
                    source_area=source_area,
                    metadata={
                        "chunk": index,
                        "chunk_count": len(chunks),
                        "chunk_start": chunk_start,
                        "chunk_end": chunk_end,
                        "file_ext": path.suffix.lower(),
                    },
                )
            )
    return documents
