#!/usr/bin/env python3
"""
worldv2 — Manual Ingestion CLI

Usage:
  python3 ingest.py --file path/to/file.pdf
  python3 ingest.py --file path/to/notes.txt
  python3 ingest.py --text "My vitamin D is 32 ng/mL as of February 2026"
  python3 ingest.py --text "Ran 10km today, felt great, avg pace 5:10/km"
"""

import argparse
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Manually ingest data into worldv2 Qdrant memory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", metavar="PATH", help="Path to a PDF or text file to ingest")
    group.add_argument("--text", metavar="TEXT", help="Raw text to save directly to memory")

    parser.add_argument(
        "--tag",
        metavar="TAG",
        action="append",
        dest="tags",
        help="Optional tag(s) for this memory (repeatable: --tag bloodwork --tag 2026-02)",
    )
    args = parser.parse_args()

    # Import here so dotenv is loaded first
    from memory.qdrant_client import QdrantMemory
    from memory.file_ingestor import FileIngestor

    memory = QdrantMemory()
    ingestor = FileIngestor(memory)

    metadata = {}
    if args.tags:
        metadata["tags"] = args.tags

    if args.text:
        point_id = ingestor.ingest_text(args.text, metadata=metadata)
        print(f"✅ Text saved to memory → {point_id}")

    elif args.file:
        import os
        if not os.path.exists(args.file):
            print(f"❌ File not found: {args.file}")
            sys.exit(1)

        count = ingestor.ingest_file(args.file, metadata=metadata)
        print(f"✅ '{args.file}' ingested — {count} chunk(s) saved to memory")


if __name__ == "__main__":
    main()
