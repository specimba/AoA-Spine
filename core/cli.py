from __future__ import annotations

import argparse
import json
from pathlib import Path

from .brain_ingest import build_documents
from .brain_store import BrainStore, BrainStoreConfig
from .director_bridge import run_director_cycle


def main() -> None:
    parser = argparse.ArgumentParser(description="AoA v2 Surgical Spine")
    subparsers = parser.add_subparsers(dest="command")

    build_index = subparsers.add_parser("build-index")
    build_index.add_argument("--repo-root", required=True)

    director_run = subparsers.add_parser("director-run")
    director_run.add_argument("--request-text", required=True)
    director_run.add_argument("--hardware-profile", default="8gb")

    args = parser.parse_args()

    if args.command == "build-index":
        docs = build_documents(Path(args.repo_root))
        store = BrainStore(BrainStoreConfig(db_path=Path(".brain_db")))
        store.add_documents(docs)
        print(f"Indexed {len(docs)} chunks.")
        return

    if args.command == "director-run":
        store = BrainStore(BrainStoreConfig(db_path=Path(".brain_db")))
        result = run_director_cycle(
            store,
            args.request_text,
            "code_lookup",
            hardware_profile=args.hardware_profile,
        )
        print(json.dumps(result, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()

