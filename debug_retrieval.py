from core import config, embeddings, vector_store
from db.database import get_session
from db.tables import Document
from sqlalchemy import select

with get_session() as session:
    doc = session.scalar(
        select(Document)
        .where(Document.owner_id.is_not(None))
        .order_by(Document.id.desc())
    )

    if doc is None:
        raise ValueError("No private PDF found.")

    doc_id = doc.id
    print("Document ID:", doc_id)
    print("Document:", doc.title)

chunks = vector_store.get_all_chunks(doc_id)

print("Total chunks:", len(chunks))
print("Minimum similarity:", config.MIN_SIMILARITY)

question = "What is HTTP?"

vector = embeddings.embed_query(question)

hits = vector_store.search(doc_id, vector, 5)

for hit in hits:
    print("\n--------------------")
    print("Page:", hit["page"])
    print("Similarity:", hit["similarity"])
    print("Text:", hit["text"][:400])