"""Isolated PDF round-trip smoke; no external files. Author: Abdelhalim Talbi."""
import json
import sys
import tempfile
from pathlib import Path

def run():
    try:
        import fitz
        with tempfile.TemporaryDirectory(prefix="openpdf-smoke-") as tmp:
            root = Path(tmp)
            first = root / "first.pdf"
            second = root / "second.pdf"
            merged = root / "merged.pdf"
            split = root / "split.pdf"
            with fitz.open() as d:
                page = d.new_page()
                page.insert_text((72, 72), "OpenPDF functional smoke page A")
                d.save(first)
            with fitz.open() as d:
                page = d.new_page()
                page.insert_text((72, 72), "OpenPDF functional smoke page B")
                d.save(second)
            with fitz.open() as result:
                for path in (first, second):
                    with fitz.open(path) as source:
                        result.insert_pdf(source)
                result.save(merged)
            with fitz.open(merged) as d:
                assert len(d) == 2, "merge page count"
                assert "page A" in d[0].get_text(), "merge first text"
                assert "page B" in d[1].get_text(), "merge second text"
                with fitz.open() as output:
                    output.insert_pdf(d, from_page=1, to_page=1)
                    output.save(split)
            with fitz.open(split) as d:
                assert len(d) == 1 and "page B" in d[0].get_text(), "split validation"
        print("OPENPDF_FUNCTIONAL_TEST_OK")
        return 0
    except Exception as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(run())
