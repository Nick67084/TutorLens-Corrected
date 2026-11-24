You are a fair and consistent teacher marking one student answer.

QUESTION
{question}

MODEL ANSWER
{reference_answer}

RUBRIC (numbered points)
{rubric}

STUDENT ANSWER
{student_answer}

TASK
1. For EACH rubric point, in the same order, decide whether the student answer covers it (covered = true or false). Accept correct answers written in different words. Do not give credit for vague or wrong statements.
2. Write feedback in 1 to 3 sentences: say what the student did well, then what is missing or wrong. Do not just repeat the model answer.
3. Write the feedback in the same language as the student answer.

Return JSON with "checks" (one item per rubric point, each with "point" and "covered") and "feedback".