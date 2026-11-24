"""Central settings for TutorLens.

Change the values here, or override the three model settings in the .env file.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# ---- folders -------------------------------------------------------------
DATA_DIR = ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
CHROMA_DIR = DATA_DIR / "chroma"
DB_PATH = DATA_DIR / "tutorlens.db"
PROMPT_DIR = ROOT / "prompts"

for _folder in (DATA_DIR, PDF_DIR, CHROMA_DIR):
    _folder.mkdir(parents=True, exist_ok=True)

# ---- models (set these in .env) ------------------------------------------
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "").strip()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3").strip()

# ---- chunking and retrieval ----------------------------------------------
CHUNK_MAX_CHARS = 1200
CHUNK_OVERLAP_CHARS = 150
TOP_K = 6
MIN_SIMILARITY = 0.35
SECTION_CONTEXT_CHARS = 10000

# ---- LLM behaviour -------------------------------------------------------
TEMP_TEACH = 0.3
TEMP_JSON = 0.1

LLM_TIMEOUT_SECONDS = 300
LLM_CONTEXT_WINDOW = 8192

# Keep the Ollama model loaded between requests.
LLM_KEEP_ALIVE = "15m"

# Response generation limits.
LLM_MAX_TOKENS_SHORT = 256
LLM_MAX_TOKENS_BALANCED = 768
LLM_MAX_TOKENS_DETAILED = 2048
LLM_MAX_TOKENS_JSON = 4096


def load_prompt(name: str) -> str:
    """Read prompts/<name>.md as text."""
    return (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")


def render_prompt(name: str, **values: object) -> str:
    """Fill {placeholders} in a prompt file in a single pass.

    Single pass means text inside the values (for example the PDF text) is
    never treated as a placeholder itself.
    """
    template = load_prompt(name)
    return re.sub(
        r"\{(\w+)\}",
        lambda match: str(values.get(match.group(1), match.group(0))),
        template,
    )