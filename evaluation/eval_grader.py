"""Compare AI marks with human marks.

Usage (from the project folder, with Ollama running):
    python evaluation/eval_grader.py

Fill evaluation/test_set.csv with about 50 rows first. Columns:
    question, reference_answer, rubric, student_answer, human_points
`rubric` is one cell with points separated by |  (example: Point A | Point B | Point C)
`human_points` is how many rubric points a human teacher gave (0 to the number of points).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

from core import grader  # noqa: E402
from models.schemas import Question  # noqa: E402

TEST_SET = ROOT / "evaluation" / "test_set.csv"
OUTPUT = ROOT / "evaluation" / "grader_results.csv"


def main() -> None:
    df = pd.read_csv(TEST_SET).fillna("")
    rows = []
    for number, row in enumerate(df.itertuples(index=False), start=1):
        rubric = [p.strip() for p in str(row.rubric).split("|") if p.strip()]
        question = Question(
            topic="evaluation",
            difficulty="medium",
            type="short",
            question=str(row.question),
            answer=str(row.reference_answer),
            rubric=rubric,
            source_page=1,
        )
        result = grader.grade(question, str(row.student_answer))
        human = int(row.human_points)
        rows.append(
            {
                "question": question.question,
                "max_points": result.max_points,
                "human_points": human,
                "ai_points": result.points,
                "difference": result.points - human,
            }
        )
        print(f"[{number}/{len(df)}] human {human} / AI {result.points} (max {result.max_points})")

    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT, index=False)

    human_pct = out["human_points"] / out["max_points"]
    ai_pct = out["ai_points"] / out["max_points"]
    print("\n=== Grader agreement ===")
    print(f"Answers compared:            {len(out)}")
    print(f"Exact same points:           {100 * (out['difference'] == 0).mean():.1f}%")
    print(f"Within 1 point:              {100 * (out['difference'].abs() <= 1).mean():.1f}%")
    print(f"Mean absolute error (score): {(human_pct - ai_pct).abs().mean():.3f}  (0 = perfect)")
    if len(out) >= 3 and human_pct.nunique() > 1 and ai_pct.nunique() > 1:
        pearson = stats.pearsonr(human_pct, ai_pct)[0]
        spearman = stats.spearmanr(human_pct, ai_pct)[0]
        print(f"Pearson correlation:         {pearson:.3f}")
        print(f"Spearman correlation:        {spearman:.3f}")
    else:
        print("Correlation needs at least 3 answers with different scores.")
    print(f"\nDetails saved to {OUTPUT}")


if __name__ == "__main__":
    main()