import warnings
from pathlib import Path

import pypdf
from langchain_core.documents import Document

from dungeon.core.metadata import PAGE, SOURCE


class PdfFolderLoader:
    """Loads one Document per page from the PDFs in a source folder.

    Only the folder's top-level ``*.pdf`` files are read, sorted by
    name. Pages are numbered from 1, as printed. Pages without
    extractable text are skipped with a warning.
    """

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def load(self) -> list[Document]:
        if not self._folder.is_dir():
            raise FileNotFoundError(f"Source folder not found: {self._folder}")

        paths = sorted(
            path
            for path in self._folder.iterdir()
            if path.is_file() and path.suffix.lower() == ".pdf"
        )

        if not paths:
            raise FileNotFoundError(f"No PDFs in {self._folder}")

        return [doc for path in paths for doc in self._load_pdf(path)]

    @staticmethod
    def _load_pdf(path: Path) -> list[Document]:
        reader = pypdf.PdfReader(path)
        documents = []

        for number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                warnings.warn(
                    f"{path}: page {number} has no text, skipping",
                    stacklevel=2,
                )
                continue

            documents.append(
                Document(
                    page_content=text,
                    metadata={SOURCE: str(path), PAGE: number},
                )
            )

        return documents
