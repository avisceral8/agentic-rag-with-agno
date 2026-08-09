"""CLI entry point for running the document ingestion pipeline.

Usage:
    uv run python run_ingest.py
    uv run python run_ingest.py --force   # Re-process all files
"""

import argparse

from src.ingest import run_ingestion, _load_tracker, _save_tracker
from src.config import DOCUMENTS_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Ingest documents into the RAG knowledge base"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-processing of all files (ignore vectorized.json tracking)",
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Path to documents directory (default: ./documents/)",
    )
    args = parser.parse_args()

    if args.force:
        print("Force mode: clearing tracking data...")
        _save_tracker({})

    docs_dir = DOCUMENTS_DIR if args.dir is None else args.dir
    print(f"Documents directory: {docs_dir}")
    print()

    stats = run_ingestion(documents_dir=docs_dir)

    print()
    print("Ingestion complete!")
    return stats


if __name__ == "__main__":
    main()