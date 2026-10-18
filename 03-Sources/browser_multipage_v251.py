"""V25.1 genuine multipage PDF browser qualification."""
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
   for i in range(1,4):
    page=doc.new_page();page.insert_text((80,100),f'{side} page {i} V25.1')
   doc.save(path)
 def region(side,page):
  return dict(side=side,page=page,coordinate_space='full_page_raster',rotation=0,raster_width=595,raster_height=842,pdf_width=595,pdf_height=842,bbox=[40,60,140,110])
 report={'page_annotations':[{'side':side,'page':n,'bbox':[40,60,140,110],'severity':'low','summary':'Evidence'} for side in ('source','target') for n in range(1,4)],'multipage_audit':{'exact_text_page_matches':[{'source_page':1,'target_page':1}],'candidate_text_page_matches':[{'source_page':2,'target_page':3}]},'visual_regions_raster_space':[region('source',1),region('target',1),region('source',2),region('target',3),region('source',3),region('target',2)]}
 html=out/'dashboard.html';html.write_text(build_dashboard(report,source_pdf=src,target_pdf=tgt),encoding='utf-8')
 checks={};errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':900});page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html.read_text(encoding='utf-8'),wait_until='load')
  states=page.locator('.comparison').evaluate_all('(els)=>els.map(e=>e.dataset.pairStatus)')
  checks['four_pair_states']=states==['exact-text','candidate-text','unmatched-source','unmatched-target']
  checks['exact_status']=page.locator('#multipage-guard-v251').get_attribute('data-state')=='exact-text'
  checks['exact_independent']='régions indépendantes' in page.locator('#multipage-guard-v251').inner_text()
  page.locator('#next-pair').click()
  checks['candidate_status']=page.locator('#multipage-guard-v251').get_attribute('data-state')=='candidate-text'
  checks['candidate_warning']='revue humaine obligatoire' in page.locator('#multipage-guard-v251').inner_text()
  page.keyboard.press('Alt+Shift+ArrowRight')
  checks['unmatched_source']=page.locator('#multipage-guard-v251').get_attribute('data-state')=='unmatched-source'
  checks['unmatched_source_warning']='comparaison géométrique non autorisée' in page.locator('#multipage-guard-v251').inner_text()
  page.locator('#next-pair').click()
  checks['unmatched_target']=page.locator('#multipage-guard-v251').get_attribute('data-state')=='unmatched-target'
  checks['unmatched_target_warning']='comparaison géométrique non autorisée' in page.locator('#multipage-guard-v251').inner_text()
  checks['no_next_overrun']=page.locator('#next-pair').is_disabled()
  page.locator('#query').focus();page.keyboard.press('Alt+Shift+ArrowLeft')
  checks['typing_guard']=page.locator('#multipage-guard-v251').get_attribute('data-state')=='unmatched-target'
  checks['no_js_errors']=not errors
  page.screenshot(path=str(out/'multipage-chromium-linux-real.png'),full_page=True)
  browser.close()
 result={'browser':'Chromium Linux headless','windows_native_tested':False,'real_pdf_fixtures':True,'checks':checks,'passed':all(checks.values()),'page_errors':errors}
 (out/'qualification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 return result
if __name__=='__main__':
 r=run(Path(__file__).with_name('captures-v25.1'));print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['passed'] else 1)
