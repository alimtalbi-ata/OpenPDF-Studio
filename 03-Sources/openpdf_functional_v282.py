"""Real PDF functional verification, using PyMuPDF. Author: Abdelhalim Talbi."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import fitz
from openpdf_engine_v273 import merge_pdfs, extract_pages, compress_pdf

def _digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _make(path, texts):
    with fitz.open() as doc:
        for text in texts:
            page=doc.new_page(); page.insert_text((72,72),text)
        doc.save(path)
def run():
    with TemporaryDirectory(prefix='openpdf-v282-') as temp:
        root=Path(temp); a=root/'source-a.pdf'; b=root/'source-b.pdf'; joined=root/'joined.pdf'; subset=root/'subset.pdf'; compressed=root/'compressed.pdf'
        _make(a,['PAGE_A_1','PAGE_A_2']); _make(b,['PAGE_B_1'])
        original={p:_digest(p) for p in (a,b)}
        progress=[]
        merge_pdfs([a,b],joined,progress=progress.append)
        assert progress[-1]==1 and all(0<=p<=1 for p in progress)
        with fitz.open(joined) as pdf:
            assert len(pdf)==3
            assert ['PAGE_A_1','PAGE_A_2','PAGE_B_1']==[page.get_text().strip() for page in pdf]
        extract_pages(joined,subset,2,3)
        with fitz.open(subset) as pdf:
            assert len(pdf)==2 and 'PAGE_B_1' in pdf[1].get_text()
        compress_pdf(joined,compressed)
        with fitz.open(compressed) as pdf:
            assert len(pdf)==3 and 'PAGE_A_1' in pdf[0].get_text()
        assert all(_digest(p)==digest for p,digest in original.items())
        stable=_digest(joined)
        try: merge_pdfs([a,b],joined,cancelled=lambda:True)
        except Exception: pass
        else: raise AssertionError('Cancellation must fail')
        assert _digest(joined)==stable, 'Cancellation modified published destination'
        assert not list(root.glob('*.tmp'))
        try: extract_pages(a,subset,1,99)
        except Exception: pass
        else: raise AssertionError('Invalid page range must fail')
        with fitz.open(subset) as pdf: assert len(pdf)==2
        return {'merge':'PASS','extract':'PASS','compress':'PASS','cancel_preserves_destination':'PASS','invalid_range_preserves_destination':'PASS','sources_unchanged':'PASS'}
if __name__=='__main__':
    import json
    print(json.dumps(run(),indent=2))
