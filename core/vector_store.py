
"""ChromaDB wrapper with semantic and hybrid document retrieval."""

from __future__ import annotations

import math
import re
from collections import Counter

from core import config
from core.chunker import Chunk


_client = None


# ============================================================
# DATABASE CONNECTION
# ============================================================

def _get_client():
    global _client

    if _client is None:
        import chromadb

        _client = chromadb.PersistentClient(
            path=str(config.CHROMA_DIR)
        )

    return _client


def _name(doc_id: int) -> str:
    return f"doc_{doc_id}"


# ============================================================
# SIMILARITY
# ============================================================

def similarity_from_distance(distance: float) -> float:
    """Convert squared L2 distance to cosine similarity."""

    return max(-1.0, min(1.0, 1.0 - distance / 2.0))


# ============================================================
# DOCUMENT STORAGE
# ============================================================

def add_document_chunks(
    doc_id: int,
    chunks: list[Chunk],
    vectors: list[list[float]],
) -> None:

    if len(chunks) != len(vectors):
        raise ValueError(
            "The number of chunks and vectors must match."
        )

    delete_document(doc_id)

    collection = _get_client().create_collection(
        _name(doc_id)
    )

    for start in range(0, len(chunks), 100):

        part = chunks[start:start + 100]

        collection.add(
            ids=[
                f"{doc_id}-{c.index}"
                for c in part
            ],
            documents=[
                c.text for c in part
            ],
            embeddings=vectors[start:start + 100],
            metadatas=[
                {
                    "page": c.page,
                    "section": c.section,
                    "chunk_index": c.index,
                }
                for c in part
            ],
        )


# ============================================================
# SEMANTIC SEARCH
# ============================================================

def search(
    doc_id: int,
    query_vector: list[float],
    k: int,
) -> list[dict]:
    """Return the most semantically similar chunks."""

    collection = _get_client().get_collection(
        _name(doc_id)
    )

    n_results = min(k, collection.count())

    if n_results <= 0:
        return []

    result = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    hits = []

    for text, meta, distance in zip(
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):

        hits.append({
            "text": text,
            "page": int(meta["page"]),
            "section": str(meta["section"]),
            "chunk_index": int(meta["chunk_index"]),
            "similarity": similarity_from_distance(
                float(distance)
            ),
        })

    return hits


# ============================================================
# DOCUMENT CHUNKS
# ============================================================

def get_all_chunks(doc_id: int) -> list[dict]:
    """Return all document chunks in reading order."""

    collection = _get_client().get_collection(
        _name(doc_id)
    )

    data = collection.get(
        include=["documents", "metadatas"]
    )

    chunks = [
        {
            "text": text,
            "page": int(meta["page"]),
            "section": str(meta["section"]),
            "chunk_index": int(meta["chunk_index"]),
        }
        for text, meta in zip(
            data["documents"],
            data["metadatas"],
        )
    ]

    return sorted(
        chunks,
        key=lambda c: c["chunk_index"],
    )


# ============================================================
# KEYWORD SEARCH
# ============================================================

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "be", "been", "being", "to", "of", "in", "on",
    "at", "for", "from", "with", "by", "and", "or",
    "as", "it", "its", "this", "that", "these",
    "those", "what", "which", "who", "when",
    "where", "why", "how", "can", "could",
    "would", "should", "do", "does", "did",
    "me", "my", "you", "your", "please",
    "explain", "describe", "provide", "give",
    "tell", "show", "about", "according",
    "lecture", "pdf", "document", "notes", "required", "four", "described",
}


def tokenize(text: str) -> list[str]:
    """Extract searchable words and technical identifiers."""

    tokens = re.findall(
        r"[^\W_]+(?:[_.-][^\W_]+)*",
        text.lower(),
        flags=re.UNICODE,
    )

    expanded = []

    for token in tokens:

        if token not in STOP_WORDS:
            expanded.append(token)

        if re.search(r"[_.-]", token):

            expanded.extend(
                part
                for part in re.split(r"[_.-]+", token)
                if part and part not in STOP_WORDS
            )

    return expanded


def keyword_search(
    doc_id: int,
    query: str,
    k: int = 12,
) -> list[dict]:
    """Rank chunks using BM25-style keyword matching."""

    if k <= 0:
        return []

    query_tokens = set(tokenize(query))

    if not query_tokens:
        return []

    chunks = get_all_chunks(doc_id)

    if not chunks:
        return []

    tokenized_chunks = [
        tokenize(
            chunk["text"]
        )
        for chunk in chunks
    ]

    total_documents = len(chunks)

    average_length = max(
        1.0,
        sum(
            len(tokens)
            for tokens in tokenized_chunks
        ) / total_documents,
    )

    document_frequency = Counter()

    for tokens in tokenized_chunks:
        document_frequency.update(set(tokens))

    k1 = 1.5
    b = 0.75

    results = []

    for chunk, tokens in zip(
        chunks,
        tokenized_chunks,
    ):

        frequencies = Counter(tokens)
        document_length = len(tokens)
        score = 0.0
        matched_terms = 0

        for term in query_tokens:

            frequency = frequencies.get(term, 0)

            if frequency == 0:
                continue

            matched_terms += 1

            df = document_frequency[term]

            idf = math.log(
                1.0
                + (
                    total_documents - df + 0.5
                ) / (df + 0.5)
            )

            denominator = frequency + k1 * (
                1.0 - b
                + b * document_length / average_length
            )

            score += idf * (
                frequency * (k1 + 1.0)
            ) / denominator

        if score > 0:

            results.append({
                **chunk,
                "keyword_score": score,
                "keyword_coverage": (
                    matched_terms / len(query_tokens)
                ),
            })

    results.sort(
        key=lambda hit: hit["keyword_score"],
        reverse=True,
    )

    return results[:k]


# ============================================================
# HYBRID RETRIEVAL
# ============================================================

def hybrid_search(
    doc_id: int,
    query: str,
    query_vector: list[float],
    k: int = 6,
) -> list[dict]:
    """Combine semantic similarity and keyword relevance."""

    if k <= 0:
        return []

    candidate_count = max(k * 3, 12)

    semantic_hits = search(
        doc_id,
        query_vector,
        candidate_count,
    )

    keyword_hits = keyword_search(
        doc_id,
        query,
        candidate_count,
    )

    candidates = {}

    # Add semantic candidates.

    for hit in semantic_hits:

        index = hit["chunk_index"]

        candidates[index] = {
            **hit,
            "keyword_score": 0.0,
            "keyword_coverage": 0.0,
        }

    # Merge keyword candidates.

    for hit in keyword_hits:

        index = hit["chunk_index"]

        if index in candidates:

            candidates[index]["keyword_score"] = (
                hit["keyword_score"]
            )

            candidates[index]["keyword_coverage"] = (
                hit["keyword_coverage"]
            )

        else:

            candidates[index] = {
                **hit,
                "similarity": None,
            }

    if not candidates:
        return []

    max_keyword_score = max(
        hit["keyword_score"]
        for hit in candidates.values()
    )

    results = []

    for hit in candidates.values():

        similarity = hit["similarity"]

        semantic_score = (
            max(0.0, similarity)
            if similarity is not None
            else 0.0
        )

        keyword_score = (
            hit["keyword_score"] / max_keyword_score
            if max_keyword_score > 0
            else 0.0
        )

        coverage = hit["keyword_coverage"]

        hybrid_score = (
            0.45 * semantic_score
            + 0.45 * keyword_score
            + 0.10 * coverage
        )

        results.append({
            **hit,
            "hybrid_score": hybrid_score,
        })

    results.sort(
        key=lambda hit: hit["hybrid_score"],
        reverse=True,
    )

    return results[:k]


# ============================================================
# SECTION MANAGEMENT
# ============================================================

def get_sections(doc_id: int) -> list[str]:
    """Return unique section titles in reading order."""

    seen = []

    for chunk in get_all_chunks(doc_id):

        if chunk["section"] not in seen:
            seen.append(chunk["section"])

    return seen


def get_section_chunks(
    doc_id: int,
    section: str,
) -> list[dict]:

    return [
        chunk
        for chunk in get_all_chunks(doc_id)
        if chunk["section"] == section
    ]


# ============================================================
# DOCUMENT DELETION
# ============================================================

def delete_document(doc_id: int) -> None:

    client = _get_client()

    collections = client.list_collections()

    names = {
        collection
        if isinstance(collection, str)
        else collection.name
        for collection in collections
    }

    name = _name(doc_id)

    if name in names:
        client.delete_collection(name)
