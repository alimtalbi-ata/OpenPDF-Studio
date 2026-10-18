"""V25.2 real-PDF browser qualification for individual evidence export."""
from pathlib import Path
import json
import fitz
from playwright.sync_api import sync_playwright
from diagnostic_dashboard import build_dashboard

def run(out):
 out=Path(out);out.mkdir(exist_ok=True,parents=True)
 src,tgt=out/'source.pdf',out/'target.pdf'
 for path,side in ((src,'source'),(tgt,'target')):
  with fitz.open() as doc:
   for n in range(2):
    page=doc.new_page();page.insert_text((80,100),f'{side} page {n+1} V25.2')
   doc.save(path)
 def region(side,page):
  return dict(side=side,page=page,coordinate_space='full_page_raster',rotation=0,raster_width=595,raster_height=842,pdf_width=595,pdf_height=842,bbox=[40,60,140,110])
 report={'page_annotations':[{'side':side,'page':n,'bbox':[40,60,140,110],'severity':'low','summary':'Evidence'} for side in ('source','target') for n in (1,2)],'multipage_audit':{'exact_text_page_matches':[{'source_page':1,'target_page':1}]},'visual_regions_raster_space':[region('source',1),region('target',1),region('source',2),region('target',2)]}
 html=out/'dashboard.html';html.write_text(build_dashboard(report,source_pdf=src,target_pdf=tgt),encoding='utf-8')
 checks={};errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':900},accept_downloads=True);page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html.read_text(encoding='utf-8'),wait_until='load')
  btn=page.locator('#proof-export-v252')
  checks['initially_disabled']=btn.is_disabled()
  page.locator('#region-pair-source').click()
  checks['source_enabled']=btn.is_enabled()
  checks['source_context']='source page 1 région 1' in page.locator('#proof-export-status-v252').inner_text()
  with page.expect_download() as dl:btn.click()
  download=dl.value;proof=json.loads(Path(download.path()).read_text())
  checks['json_name']=download.suggested_filename=='openpdf-region-proof-v25.2.json'
  checks['valid_bbox']=proof['pdf_bbox_pt']==[40,60,140,110]
  checks['individual_proof']=proof['document_side']=='source' and proof['page']==1 and proof['region_index']==1
  checks['no_region_pair_assertion']=proof['region_cross_document_match']=='not_asserted'
  checks['page_pair_status']=proof['page_pair_status']=='exact-text'
  page.locator('#region-pair-target').click()
  checks['target_enabled']=btn.is_enabled() and 'cible page 1' not in page.locator('#proof-export-status-v252').inner_text() and 'target page 1' in page.locator('#proof-export-status-v252').inner_text()
  page.locator('#next-pair').click()
  checks['navigation_invalidates']=btn.is_disabled()
  page.locator('#region-pair-source').click()
  checks['unmatched_region_selectable']=btn.is_enabled()
  with page.expect_download() as dl:btn.click()
  proof2=json.loads(Path(dl.value.path()).read_text())
  checks['unmatched_not_asserted']=proof2['page_pair_status']=='unmatched-source' and proof2['region_cross_document_match']=='not_asserted'
  page.locator('#region-selection-clear').click()
  checks['clear_invalidates']=btn.is_disabled()
  checks['no_js_errors']=not errors
  page.screenshot(path=str(out/'proof-export-chromium-linux-real.png'),full_page=True)
  browser.close()
 result={'browser':'Chromium Linux headless','windows_native_tested':False,'real_pdf_fixtures':True,'checks':checks,'passed':all(checks.values()),'page_errors':errors}
 (out/'qualification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 return result
if __name__=='__main__':
 r=run(Path(__file__).with_name('captures-v25.2'));print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['passed'] else 1)
