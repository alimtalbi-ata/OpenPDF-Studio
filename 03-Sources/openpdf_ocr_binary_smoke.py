"""Exercise packaged OCR language data inside the actual Windows executable."""
import json,sys,tempfile
from pathlib import Path

def run():
    try:
        import fitz
        from openpdf_ocr_service_v347 import searchable_pdf
        bundle=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))
        tessdata=bundle/'tessdata'
        for lang in ('fra','eng'):
            model=tessdata/(lang+'.traineddata')
            if not model.is_file() or model.stat().st_size<100000:
                raise RuntimeError('Packaged OCR model missing: '+str(model))
        with tempfile.TemporaryDirectory(prefix='openpdf-ocr-binary-') as tmp:
            root=Path(tmp);source=root/'scan.pdf';target=root/'result.pdf'
            with fitz.open() as d:
                p=d.new_page(width=595,height=842)
                p.insert_text((72,140),'DOCUMENT FACTURE TEST',fontsize=28)
                image=p.get_pixmap(dpi=200,alpha=False).tobytes('png')
            with fitz.open() as d:
                p=d.new_page(width=595,height=842)
                p.insert_image(p.rect,stream=image)
                d.save(source)
            with fitz.open(source) as d:
                assert not d[0].get_text().strip(),'input is not a scan'
            receipt=searchable_pdf(source,target,language='fra+eng',dpi=200,tessdata=str(tessdata))
            assert receipt.ocr_pages==1,'OCR page count'
            with fitz.open(target) as d:
                content=d[0].get_text().upper()
                assert 'DOCUMENT' in content and 'FACTURE' in content,repr(content)
        print('OPENPDF_OCR_BINARY_TEST_OK')
        return 0
    except Exception as exc:
        print(json.dumps({'status':'FAILED','error':str(exc)}),file=sys.stderr)
        return 1
