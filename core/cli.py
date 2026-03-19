from __future__ import annotations

import argparse
import json
from pathlib import Path

from .brain_ingest import build_documents
from .brain_store import BrainStore, BrainStoreConfig
from .director_bridge import run_director_cycle
from .vram_optimizer import VRAMOptimizer


def main() -> None:
    parser = argparse.ArgumentParser(description="AoA v2 Surgical Spine")
    subparsers = parser.add_subparsers(dest="command")

    build_index = subparsers.add_parser("build-index")
    build_index.add_argument("--repo-root", required=True)
    build_index.add_argument(
        "--reset",
        action="store_true",
        help="Reset the existing memory store before indexing.",
    )

    director_run = subparsers.add_parser("director-run")
    director_run.add_argument("--request-text", required=True)
    director_run.add_argument("--plan-type", default="code_lookup")
    director_run.add_argument("--embedding-backend", default="hash", choices=["hash", "ollama"])
    director_run.add_argument(
        "--hardware-profile",
        default="8gb",
        choices=VRAMOptimizer.supported_profiles(),
    )
    director_run.add_argument("--top-k", type=int, default=5)
    director_run.add_argument(
        "--trace",
        action="store_true",
        help="Include runtime trace in the JSON output.",
    )

    args = parser.parse_args()

    if args.command == "build-index":
        docs = build_documents(Path(args.repo_root))
        store = BrainStore(BrainStoreConfig(db_path=Path(".brain_db")))
        store.add_documents(docs, reset=args.reset)
        print(f"Indexed {len(docs)} chunks.")
        return

    if args.command == "director-run":
        store = BrainStore(BrainStoreConfig(db_path=Path(".brain_db")))
        result = run_director_cycle(
            store,
            args.request_text,
            args.plan_type,
            hardware_profile=args.hardware_profile,
            top_k=args.top_k,
            embedding_backend=args.embedding_backend,
        )
        if not args.trace:
            result = {key: value for key, value in result.items() if key != "trace"}
        print(json.dumps(result, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
