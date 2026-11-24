from core.chunker import build_chunks
from core.pdf_parser import Block, ParsedPDF


def test_sections_become_chunks_with_titles_and_pages():
    parsed = ParsedPDF(
        n_pages=3,
        blocks=[
            Block(1, "Gradient Descent", True),
            Block(1, "Gradient descent minimises a loss function step by step."),
            Block(2, "The learning rate controls the step size."),
            Block(3, "Overfitting", True),
            Block(3, "Overfitting happens when a model memorises the training data."),
        ],
    )
    chunks = build_chunks(parsed, max_chars=500, overlap=50)
    assert [c.section for c in chunks] == ["Gradient Descent", "Gradient Descent", "Overfitting"]
    assert chunks[0].page == 1
    assert "learning rate" not in chunks[0].text
    assert "learning rate" in chunks[1].text
    assert chunks[1].page == 2
    assert chunks[2].page == 3
    assert [c.index for c in chunks] == [0, 1, 2]


def test_long_text_is_split_and_respects_max_size():
    sentence = "This is a sentence about neural networks and training. "
    parsed = ParsedPDF(n_pages=1, blocks=[Block(1, "Intro", True), Block(1, sentence * 60)])
    chunks = build_chunks(parsed, max_chars=400, overlap=50)
    assert len(chunks) > 3
    assert all(len(c.text) <= 450 for c in chunks)
    assert all(c.section == "Intro" for c in chunks)


def test_text_without_spaces_is_still_split():
    parsed = ParsedPDF(n_pages=1, blocks=[Block(1, "ก" * 1000)])
    chunks = build_chunks(parsed, max_chars=300, overlap=0)
    assert len(chunks) >= 3
    assert all(len(c.text) <= 300 for c in chunks)


def test_no_headings_groups_pages():
    parsed = ParsedPDF(
        n_pages=5,
        blocks=[Block(page, f"Some text on page {page}.") for page in range(1, 6)],
    )
    chunks = build_chunks(parsed, max_chars=500, overlap=0)
    assert [c.section for c in chunks] == ["Pages 1-3"] * 3 + ["Pages 4-5"] * 2


def test_consecutive_headings_are_merged_and_empty_sections_dropped():
    parsed = ParsedPDF(
        n_pages=2,
        blocks=[
            Block(1, "Chapter 1", True),
            Block(1, "Basics", True),
            Block(1, "Some body text about the basics."),
            Block(2, "Empty section at the end", True),
        ],
    )
    chunks = build_chunks(parsed, max_chars=500, overlap=0)
    assert [c.section for c in chunks] == ["Chapter 1 Basics"]


def test_embedding_text_contains_section_title():
    parsed = ParsedPDF(n_pages=1, blocks=[Block(1, "Topic", True), Block(1, "Body text here.")])
    chunk = build_chunks(parsed)[0]
    assert chunk.for_embedding.startswith("Topic")