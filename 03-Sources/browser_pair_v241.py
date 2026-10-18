"""Actual Chromium smoke checks for evidence-gated paired-page scrolling."""
from pathlib import Path
import json
import fitz
from playwright.sync_api import sync_playwright
from diagnostic_dashboard import build_dashboard


def run(out):
 out=Path(out);out.mkdir(exist_ok=True,parents=True)
 source=out/'source.pdf';target=out/'target.pdf'
 for path in (source,target):
  with fitz.open() as doc:
   for i in range(3):
    p=doc.new_page();p.insert_text((90,100),f'Verified pair page {i+1}');
   doc.save(path)
 report={'page_annotations':[{'side':'source','page':1,'severity':'high','summary':'Source first'},{'side':'target','page':2,'severity':'low','summary':'Target second'}], 'multipage_audit':{'exact_text_page_matches':[{'source_page':1,'target_page':1}], 'candidate_text_page_matches':[{'source_page':2,'target_page':2}], 'split_merge_candidates':[{'source_pages':[1,2,3],'target_pages':[1,2,3]}]}}
 html=out/'dashboard.html';html.write_text(build_dashboard(report,source_pdf=source,target_pdf=target),encoding='utf-8')
 checks={};errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':900});page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html.read_text(encoding='utf-8'),wait_until='load')
  checks['version']='V24.1' in page.title()
  statuses=page.locator('.comparison').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.pairStatus)')
  checks['pair_evidence']=statuses==['exact-text','candidate-text','unmatched-source','unmatched-target']
  sync=page.locator('#sync-scroll');status=page.locator('#pair-evidence-status')
  checks['exact_enabled']=sync.is_enabled() and 'exact' in status.inner_text()
  page.locator('#next-pair').click()
  checks['candidate_disabled']=sync.is_disabled() and not sync.is_checked() and 'candidat' in status.inner_text()
  page.locator('#next-pair').click()
  checks['unmatched_source_disabled']=sync.is_disabled() and 'non appariées' in status.inner_text()
  page.locator('#next-pair').click()
  checks['unmatched_target_disabled']=sync.is_disabled() and 'non appariées' in status.inner_text()
  page.locator('#previous-pair').click();page.locator('#previous-pair').click();page.locator('#previous-pair').click()
  checks['exact_restored']=sync.is_enabled()
  checks['pdf_fixture_count']=len(fitz.open(source))==3 and len(fitz.open(target))==3
  checks['no_runtime_errors']=not errors
  page.screenshot(path=str(out/'pair-evidence-chromium-linux-real.png'),full_page=True)
  browser.close()
 result={'browser':'Chromium Linux headless','windows_native_tested':False,'checks':checks,'passed':all(checks.values()),'errors':errors}
 (out/'qualification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 return result
if __name__=='__main__':
 r=run(Path(__file__).with_name('captures-v24.1'));print(json.dumps(r,indent=2,ensure_ascii=False));raise SystemExit(0 if r['passed'] else 1)
