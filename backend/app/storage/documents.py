from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import fitz
from fastapi import UploadFile

CHUNK_SIZE = 1024 * 1024
PDF_SIGNATURE = b"%PDF-"
PDF_MIME_TYPE = "application/pdf"


class DocumentStorageError(Exception):
    message = "Le document ne peut pas etre importe."


class EmptyDocumentError(DocumentStorageError):
    message = "Le fichier PDF est vide."


class InvalidDocumentTypeError(DocumentStorageError):
    message = "Seuls les fichiers PDF sont acceptes."


class OversizedDocumentError(DocumentStorageError):
    message = "Le fichier PDF depasse la taille maximale autorisee."


class InvalidPdfError(DocumentStorageError):
    message = "Le fichier PDF est invalide ou corrompu."


@dataclass(frozen=True)
class StoredDocument:
    stored_filename: str
    storage_key: str
    mime_type: str
    file_size: int
    page_count: int


class DocumentStorageService:
    def __init__(
        self,
        *,
        upload_directory: str | Path,
        max_upload_size_mb: int,
    ) -> None:
        self.root = Path(upload_directory).resolve()
        self.max_bytes = max_upload_size_mb * 1024 * 1024

    def store_pdf(self, *, file: UploadFile, user_id: int) -> StoredDocument:
        self._validate_declared_type(file)

        user_dir = self._safe_user_dir(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        stored_filename = f"{uuid4().hex}.pdf"
        destination = (user_dir / stored_filename).resolve()
        if not destination.is_relative_to(user_dir):
            raise InvalidDocumentTypeError

        file_size = 0
        first_bytes = b""

        try:
            with destination.open("wb") as output:
                while chunk := file.file.read(CHUNK_SIZE):
                    if not first_bytes:
                        first_bytes = chunk[: len(PDF_SIGNATURE)]

                    file_size += len(chunk)
                    if file_size > self.max_bytes:
                        raise OversizedDocumentError

                    output.write(chunk)

            if file_size == 0:
                raise EmptyDocumentError
            if not first_bytes.startswith(PDF_SIGNATURE):
                raise InvalidPdfError

            page_count = self._validate_pdf(destination)
        except DocumentStorageError:
            self.delete_by_key(f"{user_id}/{stored_filename}")
            raise
        except Exception as exc:
            self.delete_by_key(f"{user_id}/{stored_filename}")
            raise InvalidPdfError from exc
        finally:
            file.file.seek(0)

        return StoredDocument(
            stored_filename=stored_filename,
            storage_key=f"{user_id}/{stored_filename}",
            mime_type=PDF_MIME_TYPE,
            file_size=file_size,
            page_count=page_count,
        )

    def delete_by_key(self, storage_key: str) -> None:
        path = self.path_for_key(storage_key)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            return

    def path_for_key(self, storage_key: str) -> Path:
        path = (self.root / storage_key).resolve()
        if not path.is_relative_to(self.root):
            raise InvalidDocumentTypeError
        return path

    def _safe_user_dir(self, user_id: int) -> Path:
        user_dir = (self.root / str(user_id)).resolve()
        if not user_dir.is_relative_to(self.root):
            raise InvalidDocumentTypeError
        return user_dir

    def _validate_declared_type(self, file: UploadFile) -> None:
        filename = Path(file.filename or "").name
        if not filename or Path(filename).suffix.lower() != ".pdf":
            raise InvalidDocumentTypeError

        if file.content_type != PDF_MIME_TYPE:
            raise InvalidDocumentTypeError

    def _validate_pdf(self, path: Path) -> int:
        try:
            with fitz.open(path) as pdf:
                page_count = pdf.page_count
        except Exception as exc:
            raise InvalidPdfError from exc

        if page_count < 1:
            raise InvalidPdfError

        return page_count
