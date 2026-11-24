import pytest

pymupdf = pytest.importorskip("pymupdf")

from core.pdf_parser import parse_pdf  # noqa: E402

PARAGRAPH = (
    "Gradient descent is an optimisation method that repeatedly moves the model "
    "parameters in the direction that lowers the loss. The learning rate controls "
    "how large each step is, so a good value is important for stable training."
)


def make_pdf(path, pages=2):
    doc = pymupdf.open()
    for number in range(1, pages + 1):
        page = doc.new_page()
        page.insert_text((72, 80), f"Section {number}: Gradient Descent", fontsize=22)
        page.insert_textbox(pymupdf.Rect(72, 120, 520, 300), PARAGRAPH, fontsize=11)
    doc.save(str(path))
    doc.close()


def test_parse_pdf_returns_pages_blocks_and_headings(tmp_path):
    path = tmp_path / "lecture.pdf"
    make_pdf(path, pages=2)
    parsed = parse_pdf(path)
    assert parsed.n_pages == 2
    assert {b.page for b in parsed.blocks} == {1, 2}
    headings = [b for b in parsed.blocks if b.is_heading]
    assert headings and all("Gradient Descent" in b.text for b in headings)
    assert any("learning rate" in b.text for b in parsed.blocks if not b.is_heading)


def test_parse_pdf_accepts_bytes(tmp_path):
    path = tmp_path / "lecture.pdf"
    make_pdf(path, pages=1)
    parsed = parse_pdf(path.read_bytes())
    assert parsed.n_pages == 1


def test_pdf_without_text_raises_clear_error(tmp_path):
    path = tmp_path / "blank.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(path))
    doc.close()
    with pytest.raises(ValueError):
        parse_pdf(path)