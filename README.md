# AoA v2 Surgical Spine

AoA v2 Surgical Spine is a reconstructed repository built from the text-packed
`AoA v2a.py` source dump. The goal of this repo is simple: turn the hidden
single-file structure into a real, testable codebase that can be reviewed
before release.

## What It Includes

- repository ingestion with bounded text chunking
- JSONL-backed memory storage with optional LanceDB mirroring
- hybrid lexical and semantic retrieval
- CPU-only reranking for low-VRAM environments
- VRAM budgeting and overflow refusal
- golden dataset evaluation for basic regression checks
- a small CLI for indexing and Director-style retrieval runs

## Repository Layout

```text
AoA-v2-Surgical-Spine/
├─ core/                  Runtime modules
├─ data/                  Golden dataset and telemetry fixtures
├─ tests/                 Smoke coverage
├─ boot_system.py         Minimal startup check
├─ pyproject.toml         Packaging and CLI entrypoint
├─ CONTRIBUTING.md        Local development guidance
└─ RELEASE_CHECKLIST.md   Pre-release validation checklist
```

## Quick Start

```powershell
cd C:\Users\speci.000\Documents\AoA-v2-Surgical-Spine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
python boot_system.py
python -m core.cli build-index --repo-root .
python -m core.cli director-run --request-text "What providers are supported?"
python -m pytest -q
```

## CLI

Build the local memory index:

```powershell
python -m core.cli build-index --repo-root .
```

Run a Director-style grounded lookup:

```powershell
python -m core.cli director-run --request-text "What providers are supported?"
```

## Validation Status

The reconstructed repo has been validated with:

- `python boot_system.py`
- `python -m core.cli build-index --repo-root .`
- `python -m core.cli director-run --request-text "What providers are supported?"`
- `python -m pytest -q`

## Notes

- `lancedb` is optional. The repository works without it and falls back to JSONL persistence.
- `OllamaEmbedder` is intentionally stubbed for safe local runs. Replace it with a live provider only when integration work starts.
- The original packed file contained structural and formatting issues. This repo applies bounded fixes so the system is runnable, inspectable, and ready for review.
