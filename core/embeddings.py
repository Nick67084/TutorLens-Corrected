
"""Text embedding and query optimization for TutorLens."""

from __future__ import annotations

import logging
import time

from functools import lru_cache
from threading import Lock
from typing import Callable

from core import config


logger = logging.getLogger(__name__)

_model = None
_model_lock = Lock()


# ============================================================
# EMBEDDING MODEL INITIALIZATION
# ============================================================

def _get_model():
    """Load the embedding model once per Python process."""

    global _model

    if _model is None:

        with _model_lock:

            if _model is None:

                from sentence_transformers import SentenceTransformer

                start_time = time.perf_counter()

                logger.info(
                    "Loading embedding model: %s",
                    config.EMBEDDING_MODEL,
                )

                model = SentenceTransformer(
                    config.EMBEDDING_MODEL
                )

                model.max_seq_length = 512

                _model = model

                elapsed = time.perf_counter() - start_time

                logger.info(
                    "Embedding model loaded in %.2f seconds.",
                    elapsed,
                )

    return _model


# ============================================================
# DOCUMENT EMBEDDINGS
# ============================================================

def embed_texts(
    texts: list[str],
    batch_size: int = 16,
    progress: Callable[[int, int], None] | None = None,
) -> list[list[float]]:
    """Generate normalized embeddings in batches."""

    if not texts:
        return []

    if batch_size <= 0:
        raise ValueError("Batch size must be greater than zero.")

    model = _get_model()

    vectors: list[list[float]] = []

    for start in range(0, len(texts), batch_size):

        batch = texts[start:start + batch_size]

        output = model.encode(
            batch,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        vectors.extend(output.tolist())

        if progress:
            progress(
                min(start + batch_size, len(texts)),
                len(texts),
            )

    return vectors


# ============================================================
# QUERY EMBEDDINGS
# ============================================================

@lru_cache(maxsize=0)
def _cached_query_embedding(
    text: str,
) -> tuple[float, ...]:
    """Cache embeddings for repeated search queries."""

    model = _get_model()

    output = model.encode(
        [text],
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return tuple(output[0].tolist())


def embed_query(text: str) -> list[float]:
    """Generate or reuse an embedding for a search query."""

    text = text.strip()

    if not text:
        raise ValueError("Search query cannot be empty.")

    return list(_cached_query_embedding(text))


# ============================================================
# CACHE MANAGEMENT
# ============================================================

def clear_query_cache() -> None:
    """Clear cached query embeddings."""

    _cached_query_embedding.cache_clear()


def get_query_cache_info() -> dict:
    """Return query cache statistics."""

    info = _cached_query_embedding.cache_info()

    return {
        "hits": info.hits,
        "misses": info.misses,
        "max_size": info.maxsize,
        "current_size": info.currsize,
    }
