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


def build_documents(root: Path) -> list[BrainDocument]:
    documents: list[BrainDocument] = []
    for path in root.rglob("*"):
        if path.is_dir() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        for index, chunk in enumerate(chunk_text(text)):
            doc_id = hashlib.sha256(f"{path.relative_to(root)}::{index}".encode()).hexdigest()[:12]
            documents.append(
                BrainDocument(
                    doc_id=doc_id,
                    text=chunk,
                    source_path=str(path.relative_to(root)),
                    source_kind="code" if path.suffix.lower() in {".py", ".js", ".ts", ".tsx"} else "doc",
                    title=path.name,
                    metadata={"chunk": index},
                )
            )
    return documents

