from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from app.rag.pdf_extractor import EmptyPdfTextError, PdfTextExtractor


def create_pdf(path: Path, page_texts: list[str]) -> None:
    pdf = fitz.open()

    for text in page_texts:
        page = pdf.new_page()
        if text:
            page.insert_text((72, 72), text)

    pdf.save(path)
    pdf.close()


def test_pdf_extractor_preserves_page_numbers(tmp_path: Path) -> None:
    pdf_path = tmp_path / "course.pdf"
    create_pdf(pdf_path, ["Premiere page", "Deuxieme page"])

    extractor = PdfTextExtractor()

    pages = extractor.extract_pages(
        pdf_path=pdf_path,
        document_id=10,
        user_id=20,
        document_title="Cours RAG",
    )

    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert pages[0].text == "Premiere page"
    assert pages[1].page_number == 2
    assert pages[1].text == "Deuxieme page"


def test_pdf_extractor_skips_empty_pages(tmp_path: Path) -> None:
    pdf_path = tmp_path / "course.pdf"
    create_pdf(pdf_path, ["Page avec texte", "", "Autre page"])

    extractor = PdfTextExtractor()

    pages = extractor.extract_pages(
        pdf_path=pdf_path,
        document_id=10,
        user_id=20,
        document_title="Cours RAG",
    )

    assert len(pages) == 2
    assert [page.page_number for page in pages] == [1, 3]


def test_pdf_extractor_rejects_pdf_without_text(tmp_path: Path) -> None:
    pdf_path = tmp_path / "empty.pdf"
    create_pdf(pdf_path, ["", ""])

    extractor = PdfTextExtractor()

    with pytest.raises(EmptyPdfTextError):
        extractor.extract_pages(
            pdf_path=pdf_path,
            document_id=10,
            user_id=20,
            document_title="Cours vide",
        )
