"""Check whether retrieval finds the right PDF page.

Usage (the PDF must already be uploaded in the app):
    python evaluation/eval_retrieval.py --doc 1 --k 4

Fill evaluation/retrieval_set.csv first. Columns:
    question, expected_page
`expected_page` = the page that contains the answer.
Leave it EMPTY for questions whose answer is NOT in the PDF - the system should
refuse those ("not in this PDF").
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from core import config, embeddings, vector_store  # noqa: E402

CSV_PATH = ROOT / "evaluation" / "retrieval_set.csv"


def main(doc_id: int, k: int) -> None:
    df = pd.read_csv(CSV_PATH)
    hits_found = answerable = 0
    refused = unanswerable = 0
    for row in df.itertuples(index=False):
        results = vector_store.search(doc_id, embeddings.embed_query(str(row.question)), k)
        pages = {r["page"] for r in results}
        relevant = [r for r in results if r["similarity"] >= config.MIN_SIMILARITY]
        if pd.isna(row.expected_page):
            unanswerable += 1
            correct = not relevant
            refused += int(correct)
            print(f"[not in PDF] {'refused OK' if correct else 'WRONGLY ANSWERED'}: {row.question}")
        else:
            answerable += 1
            correct = int(row.expected_page) in pages
            hits_found += int(correct)
            print(f"[page {int(row.expected_page)}] {'found' if correct else 'MISSED'} (top pages {sorted(pages)}): {row.question}")

    print("\n=== Retrieval results ===")
    if answerable:
        print(f"Hit@{k} (right page in top {k}): {100 * hits_found / answerable:.1f}%  ({hits_found} of {answerable})")
    if unanswerable:
        print(f"Correctly refused 'not in PDF':  {100 * refused / unanswerable:.1f}%  ({refused} of {unanswerable})")
    print(f"(refusal threshold MIN_SIMILARITY = {config.MIN_SIMILARITY}; tune it in core/config.py)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", type=int, required=True, help="document id (first uploaded PDF = 1)")
    parser.add_argument("--k", type=int, default=config.TOP_K)
    args = parser.parse_args()
    main(args.doc, args.k)