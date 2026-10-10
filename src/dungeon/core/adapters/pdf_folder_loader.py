import warnings
from pathlib import Path

import pypdf
from langchain_core.documents import Document

from dungeon.core.metadata import PAGE, SOURCE


class PdfFolderLoader:
    """Loads one Document per page from the PDFs in a source folder.

    Only the folder's top-level ``*.pdf`` files are read, sorted by
    name. A Document's source is the file name, and its page is the
    PDF page index counted from 1, which can differ from the printed
    number. Pages without extractable text are skipped, with one
    warning per file.
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
        blank = []

        for number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                blank.append(number)
                continue

            documents.append(
                Document(
                    page_content=text,
                    metadata={SOURCE: path.name, PAGE: number},
                )
            )

        if blank:
            warnings.warn(
                f"{path.name}: no text on pages "
                f"{_format_pages(blank)}, skipping",
                stacklevel=2,
            )

        return documents


def _format_pages(pages: list[int]) -> str:
    """Format ascending page numbers as ranges: ``1-3, 8, 24``."""
    runs = [[pages[0], pages[0]]]

    for page in pages[1:]:
        if page == runs[-1][1] + 1:
            runs[-1][1] = page
        else:
            runs.append([page, page])

    return ", ".join(
        str(start) if start == end else f"{start}-{end}" for start, end in runs
    )
