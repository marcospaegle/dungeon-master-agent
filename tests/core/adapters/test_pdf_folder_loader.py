from pathlib import Path

import pytest
from pypdf.errors import PdfReadError

from dungeon.core.adapters.pdf_folder_loader import PdfFolderLoader


def make_pdf(path: Path, pages: list[str]) -> None:
    """Write a minimal PDF with one line of text per page."""
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>"]
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(len(pages)))
    objects.append(
        f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode()
    )
    font = 3 + 2 * len(pages)
    for i, text in enumerate(pages):
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] "
            f"/Contents {4 + 2 * i} 0 R "
            f"/Resources << /Font << /F1 {font} 0 R >> >> >>".encode()
        )
        stream = f"BT /F1 12 Tf 20 100 Td ({text}) Tj ET" if text else ""
        objects.append(
            f"<< /Length {len(stream)} >>\n"
            f"stream\n{stream}\nendstream".encode()
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out = b"%PDF-1.4\n"
    offsets = []
    for n, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF"
    ).encode()
    path.write_bytes(out)


def test_loads_one_document_per_page_numbered_from_one(tmp_path):
    make_pdf(tmp_path / "a.pdf", ["first page", "second page"])

    docs = PdfFolderLoader(tmp_path).load()

    assert [d.page_content for d in docs] == ["first page", "second page"]
    assert [d.metadata["page"] for d in docs] == [1, 2]
    assert docs[0].metadata["source"] == "a.pdf"


def test_reads_only_top_level_pdfs_sorted_by_name(tmp_path):
    make_pdf(tmp_path / "b.PDF", ["bee"])
    make_pdf(tmp_path / "a.pdf", ["aye"])
    (tmp_path / "sub").mkdir()
    make_pdf(tmp_path / "sub" / "c.pdf", ["sea"])
    (tmp_path / "notes.txt").write_text("ignored")

    docs = PdfFolderLoader(tmp_path).load()

    assert [d.page_content for d in docs] == ["aye", "bee"]


def test_skips_pages_without_text_with_one_warning_per_file(tmp_path):
    make_pdf(tmp_path / "a.pdf", ["", "", "text", "", "x", ""])
    make_pdf(tmp_path / "b.pdf", ["", "text"])

    with pytest.warns(UserWarning) as caught:
        docs = PdfFolderLoader(tmp_path).load()

    assert [str(w.message) for w in caught] == [
        "a.pdf: no text on pages 1-2, 4, 6, skipping",
        "b.pdf: no text on pages 1, skipping",
    ]
    assert [d.metadata["page"] for d in docs] == [3, 5, 2]


def test_missing_folder_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        PdfFolderLoader(tmp_path / "nope").load()


def test_folder_without_pdfs_fails(tmp_path):
    with pytest.raises(FileNotFoundError, match="No PDFs"):
        PdfFolderLoader(tmp_path).load()


def test_corrupt_pdf_fails_loudly(tmp_path):
    (tmp_path / "bad.pdf").write_bytes(b"not a pdf")

    with pytest.raises(PdfReadError):
        PdfFolderLoader(tmp_path).load()
