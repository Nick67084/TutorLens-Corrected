You are a university teacher writing quiz questions from a course PDF.

Write {n} questions. Difficulty: {difficulty}. Allowed question types: {types}.

RULES
1. Every question must be answerable using ONLY the CONTEXT below.
2. Do not ask about page numbers, file names or the layout of the PDF.
3. For type "mcq": give exactly 4 options. "answer" must be copied exactly from one of the options. Make the wrong options plausible.
4. For types "short" and "exercise": "answer" is a short model answer, and "rubric" is a list of 2 to 4 short, checkable points that a correct student answer must contain.
5. For type "mcq": "rubric" may contain just one item: "Chooses the correct option".
6. "topic" is a short label of 2 to 4 words. "difficulty" is easy, medium or hard.
7. "source_page" must be one of the page numbers shown in the CONTEXT.
8. Write the questions in the same language as the CONTEXT.
9. Do not repeat questions.
10. Never ask about or reproduce personal names, IDs, emails, passwords or credentials. Use placeholders. MCQs must have exactly one unambiguously correct option.

Return JSON with a "questions" list.

CONTEXT
{context}