"""Check the quality of generated questions by hand.

Step 1 - generate questions into a CSV (Ollama must be running):
    python evaluation/eval_questions.py generate --doc 1 --n 20

Step 2 - open evaluation/questions_to_check.csv in Excel and fill the last three
columns with 1 (yes) or 0 (no) for every question:
    correct              the model answer is right according to the PDF
    answerable_from_pdf  the question can be answered using only the PDF
    difficulty_ok        the difficulty label looks right

Step 3 - see the percentages:
    python evaluation/eval_questions.py summarize
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

CSV_PATH = ROOT / "evaluation" / "questions_to_check.csv"
CHECK_COLUMNS = ["correct", "answerable_from_pdf", "difficulty_ok"]


def generate(doc_id: int, n: int) -> None:
    from core import question_gen

    rows = []
    while len(rows) < n:
        batch = question_gen.generate_quiz(
            doc_id, n=min(5, n - len(rows)), difficulty="mixed", types=["mcq", "short", "exercise"]
        )
        for q in batch:
            rows.append(
                {
                    "question": q.question,
                    "type": q.type,
                    "difficulty": q.difficulty,
                    "answer": q.answer,
                    "rubric": " | ".join(q.rubric),
                    "source_page": q.source_page,
                    **{column: "" for column in CHECK_COLUMNS},
                }
            )
        print(f"Generated {len(rows)} / {n}")
    pd.DataFrame(rows[:n]).to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"Saved {CSV_PATH}. Now fill the last three columns with 1 or 0.")


def summarize() -> None:
    df = pd.read_csv(CSV_PATH)
    print(f"Questions in file: {len(df)}")
    for column in CHECK_COLUMNS:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if values.empty:
            print(f"{column:22s} not filled in yet")
        else:
            print(f"{column:22s} {100 * values.mean():.1f}%  ({int(values.sum())} of {len(values)})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("--doc", type=int, required=True, help="document id (see the Upload page order, first PDF = 1)")
    gen.add_argument("--n", type=int, default=20)
    sub.add_parser("summarize")
    args = parser.parse_args()
    if args.command == "generate":
        generate(args.doc, args.n)
    else:
        summarize()