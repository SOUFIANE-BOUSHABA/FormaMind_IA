from __future__ import annotations

import re
from pathlib import Path

import fitz

from app.schemas.rag import ExtractedPage

WHITESPACE_PATTERN = re.compile(r"\s+")


class PdfTextExtractionError(Exception):
    pass


class EmptyPdfTextError(PdfTextExtractionError):
    pass


class PdfTextExtractor:
    def extract_pages(
        self,
        *,
        pdf_path: Path,
        document_id: int,
        user_id: int,
        document_title: str,
    ) -> list[ExtractedPage]:
        pages: list[ExtractedPage] = []

        try:
            with fitz.open(pdf_path) as pdf:
                for page_index, page in enumerate(pdf):
                    normalized_text = self._normalize_text(page.get_text("text"))

                    if not normalized_text:
                        continue

                    pages.append(
                        ExtractedPage(
                            document_id=document_id,
                            user_id=user_id,
                            document_title=document_title,
                            page_number=page_index + 1,
                            text=normalized_text,
                        )
                    )
        except Exception as exc:
            raise PdfTextExtractionError from exc

        if not pages:
            raise EmptyPdfTextError

        return pages

    def _normalize_text(self, text: str) -> str:
        return WHITESPACE_PATTERN.sub(" ", text).strip()
