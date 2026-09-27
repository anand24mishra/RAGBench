from __future__ import annotations

import argparse
import os
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a text or Markdown document to RAGBench")
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--api-url",
        default=os.getenv("RAGBENCH_API_URL", "http://localhost:8000"),
    )
    args = parser.parse_args()

    with args.path.open("rb") as document:
        response = httpx.post(
            f"{args.api_url.rstrip('/')}/ingest",
            files={"file": (args.path.name, document, "text/plain")},
            timeout=120,
        )
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()
