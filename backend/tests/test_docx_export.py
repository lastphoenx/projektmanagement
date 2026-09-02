"""Tests für DOCX-Export-Hilfen."""

from app.core.export.docx import build_docx_bytes


def test_build_docx_bytes_returns_zip_header():
    data = build_docx_bytes(
        title="Test",
        sections=[("Abschnitt", "# Überschrift\n\nEin **fetter** Text.")],
    )
    assert data[:2] == b"PK"
