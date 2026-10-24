"""Run Notebook 1 code cells in order against the configured live services."""
import contextlib
import argparse
import io
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Also run hosted Pinecone writes and queries and local generation")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    os.chdir(root)
    notebook = json.loads((root / "1_rag_pipeline.ipynb").read_text(encoding="utf-8"))
    scope = {"__name__": "__main__"}
    for number, cell in enumerate(notebook["cells"], start=1):
        if number == 19 and not args.live:
            print("Local data cells passed. Use --live to include Pinecone uploads and generation.")
            return
        if cell["cell_type"] != "code":
            continue
        print(f"Running cell {number}", flush=True)
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile("".join(cell["source"]), f"cell {number}", "exec"), scope)
        print(f"PASS cell {number}", flush=True)
    if not scope["retrieved_docs"]:
        raise RuntimeError("Retrieval returned no documents after indexing.")
    if not scope["response"].content:
        raise RuntimeError("Generation returned an empty answer.")
    print("All code cells passed; retrieval and generation returned results.")


if __name__ == "__main__":
    main()
