from core import chunker, pdf_parser, vector_store, teacher, llm_client

def test_page_boundaries_and_keyword_rank(monkeypatch):
    parsed = pdf_parser.ParsedPDF(3, [pdf_parser.Block(1,'Backend',True), pdf_parser.Block(1,'Create project'), pdf_parser.Block(2,'npm install mysql2 express dotenv cors'), pdf_parser.Block(3,'CREATE TABLE users (id int)')])
    chunks = chunker.build_chunks(parsed)
    assert [c.page for c in chunks] == [1,2,3]
    monkeypatch.setattr(vector_store,'get_all_chunks',lambda _: [vars(c) | {'chunk_index':c.index} for c in chunks])
    assert vector_store.keyword_search(1,'npm packages install')[0]['page']==2
    assert vector_store.keyword_search(1,'users database table')[0]['page']==3

def test_independent_question_and_lengths():
    assert not teacher.is_follow_up('Explain the architecture in this lecture.')
    assert teacher.is_follow_up('Explain it more simply.')
    assert [llm_client.get_token_limit(x) for x in ('Short','Balanced','Detailed')]==[256,768,2048]

def test_redaction():
    assert teacher.sanitize_personal_information('Student ID: 1234567') == 'Student ID: [Student ID]'
    assert 'example@example.com' not in teacher.sanitize_personal_information('Email example@example.com')
    assert 'Jane Doe' not in teacher.sanitize_personal_information('git config --global user.name "Jane Doe"')
    assert teacher.sanitize_personal_information('') == ''
