# TutorLens

An AI teacher that explains, quizzes and grades from your PDFs. Everything runs
on your own computer with free, open-source tools.

## What it does

- **Upload** a text-based course PDF (text is extracted page by page)
- **Learn:** the AI teacher explains a section step by step, or answers your
  questions, and always shows the PDF page it used. If the answer is not in the PDF,
  it says so.
- **Quiz:** generates multiple-choice, short-answer and exercise questions
- **AI grading:** marks short answers against a rubric and gives feedback
- **Marks:** saves your scores and shows them in a table

## Tech stack

Streamlit · Python · PyMuPDF · Pydantic · sentence-transformers (BAAI/bge-m3) ·
ChromaDB · Ollama (local LLM) · SQLite + SQLAlchemy · pytest

## Setup (Windows PowerShell)

1. Install **Ollama** from https://ollama.com and download a model:
   `ollama pull <model-name>` (pick one from https://ollama.com/library that fits your RAM).
2. Open the project folder in VS Code and open a terminal.
3. Create and activate a virtual environment, then install the packages:
```
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
```
4. Copy `.env.example` to `.env` and set `OLLAMA_MODEL` to the model you pulled.
5. Run the app (always use `python -m`, so it uses the same Python as `pip`):
```
   python -m streamlit run main.py
```

The first time you upload a PDF, the embedding model (about 2 GB) is downloaded.

## Project structure

```
main.py          home page
pages/           Upload, Learn, Quiz, Marks pages
core/            all the logic (parser, chunker, embeddings, vector store, LLM, teacher, questions, grader)
models/          Pydantic schemas
db/              SQLite tables and queries
prompts/         prompt files (edit these to change the teacher's behaviour)
evaluation/      scripts for the results of the report
tests/           pytest tests
data/            your PDFs, vector database and SQLite file (created automatically)
```

## Tests

```
python -m pytest
```

## Evaluation (for the report)

With Ollama running and a PDF uploaded:

```
python evaluation/eval_grader.py                                  # AI marks vs human marks
python evaluation/eval_questions.py generate --doc 1 --n 20       # then fill the CSV by hand
python evaluation/eval_questions.py summarize
python evaluation/eval_retrieval.py --doc 1 --k 4                 # right page found? "not in PDF" refused?
```

The CSV files in `evaluation/` contain 3 example rows. Replace them with your own data.

## Troubleshooting

- **"Cannot reach Ollama":** start the Ollama app, or run `ollama serve`.
- **"Model ... is not installed":** run `ollama pull <model-name>` with the same name as in `.env`.
- **"No readable text":** the PDF is scanned images. Use a text-based PDF.
- **Answers say "not in the PDF" too often (or never):** change `MIN_SIMILARITY` in `core/config.py`.
- **Streamlit prints torch warnings:** harmless. To hide them run `python -m streamlit run main.py --server.fileWatcherType none`.
- **Slow answers:** use a smaller Ollama model, or close other programs.