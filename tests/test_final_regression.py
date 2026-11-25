from core import citations, teacher, vector_store, embeddings

def test_citation_formats():
    assert citations.normalize('[Reference: p.5] [p.5, p.7] [p.16-18]') == '[p.5] [p.5] [p.7] [p.16] [p.17] [p.18]'
    assert citations.cited_pages('`[p.99]` [p.5, p.7]') == {5,7}
    assert citations.normalize('```python\n[p.5, p.7]\n```') == '```python\n[p.5, p.7]\n```'
    assert citations.cited_pages('[p.999]') == {999}

def test_retrieval_neighbors_and_unrelated(monkeypatch):
    chunks = [{'chunk_index':i,'page':i+1,'section':'HTTP','text':t} for i,t in enumerate(['Flutter project','http package API','fetch attractions JSON setState','ListView displays attraction data','detail page'])]
    monkeypatch.setattr(vector_store,'get_all_chunks',lambda _: chunks)
    monkeypatch.setattr(vector_store,'search',lambda *a,**k: [])
    monkeypatch.setattr(embeddings,'embed_query',lambda _: [])
    assert 3 in {s.page for s in teacher.retrieve(1,'Flutter fetches and displays attraction data from API',top_k=10)}
    assert not teacher.retrieve(1,'CNN architecture image classification Python',top_k=10)
    assert {s.page for s in teacher.retrieve(1,'Summarize the lecture',top_k=10)} == set(range(1,6))

def test_socratic_contract():
    messages = teacher.build_answer_messages('GET vs POST',[teacher.Source(1,'HTTP','GET retrieves data; POST submits data')],mode='Socratic Tutor')
    assert 'ask exactly one focused question and stop' in messages[0]['content']
