"""Deterministic synthetic PDF quality corpus. Author: Abdelhalim Talbi."""
from pathlib import Path
import json
import fitz

def build_corpus(directory):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    specs=(('04-complex-table.pdf','table'),('05-embedded-image.pdf','image'),('06-multilingual.pdf','languages'),('07-long-document.pdf','long'))
    output=[]
    for name,kind in specs:
        path=directory/name
        with fitz.open() as doc:
            p=doc.new_page(width=595,height=842)
            p.insert_text((45,45),'SYNTHETIC TEST DOCUMENT — '+kind,fontsize=12)
            if kind=='table':
                for x in (45,160,300,445,550): p.draw_line((x,100),(x,330))
                for y in (100,140,180,220,260,300,330): p.draw_line((45,y),(550,y))
                for r in range(5):
                    for c in range(4):p.insert_text((50+c*115,120+r*40),f'R{r+1} C{c+1}',fontsize=9)
            elif kind=='image':
                import zlib,struct
                w=h=40; pixels=bytes((x*5%256,y*5%256,100) for y in [] for x in []) if False else b''.join(bytes((x*5%256,y*5%256,100)) for y in range(h) for x in range(w))
                def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
                raw=b''.join(b'\x00'+pixels[y*w*3:(y+1)*w*3] for y in range(h))
                png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
                p.insert_image(fitz.Rect(80,100,280,300),stream=png)
            elif kind=='languages':
                p.insert_text((45,100),'Francais: document de reference, donnees et tableaux',fontsize=11)
                p.insert_text((45,125),'English: reference document, tables and images',fontsize=11)
                p.insert_text((45,150),'Espanol: documento de referencia',fontsize=11)
                p.insert_text((45,175),'Deutsch: Referenzdokument',fontsize=11)
            else:
                for page_index in range(1,10):
                    q=doc.new_page() if page_index>1 else p
                    for line in range(25):q.insert_text((45,70+line*23),f'Page {page_index} line {line}: alpha beta gamma delta',fontsize=10)
            doc.save(path)
        with fitz.open(path) as check:
            output.append({'name':name,'kind':kind,'pages':check.page_count,'bytes':path.stat().st_size,'sha256':__import__('hashlib').sha256(path.read_bytes()).hexdigest()})
    (directory/'MANIFEST-SYNTHETIC.json').write_text(json.dumps({'origin':'SYNTHETIC - NOT REAL DOCUMENTS','cases':output},indent=2),encoding='utf-8')
    return output
