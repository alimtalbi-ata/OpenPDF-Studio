"""Regression tests for tiled image OCR coverage. Author: Abdelhalim Talbi."""
import fitz
from openpdf_ocr_page_policy_v464 import should_ocr_page

def test_empty_page_is_ocr_candidate():
    with fitz.open() as doc:
        page = doc.new_page()
        assert should_ocr_page(page, 'smart') is True
