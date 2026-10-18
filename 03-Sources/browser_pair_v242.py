"""V24.2 real Chromium regression on explicit page-pair evidence."""
from pathlib import Path
import json
import fitz
from playwright.sync_api import sync_playwright
from diagnostic_dashboard import build_dashboard

def run(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 source=out/'source.pdf';target=out/'target.pdf'
 for path in (source,target):
  with fitz.open() as doc:
   for i in range(3):
    p=doc.new_page();p.insert_text((90,100),f'Pair page {i+1}')
   doc.save(path)
 report={'page_annotations':[{'side':'source','page':1,'severity':'high','summary':'Source first'}], 'multipage_audit':{'exact_text_page_matches':[{'source_page':1,'target_page':1}], 'candidate_text_page_matches':[{'source_page':2,'target_page':2}], 'split_merge_candidates':[{'source_pages':[1,2,3],'target_pages':[1,2,3]}]}}
 html=out/'dashboard.html';html.write_text(build_dashboard(report,source_pdf=source,target_pdf=target),encoding='utf-8')
 checks={};errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':900});page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html.read_text(),wait_until='load')
  sync=page.locator('#sync-scroll');status=page.locator('#pair-evidence-status')
  checks['version']='V24.2' in page.title()
  checks['pair_statuses']=page.locator('.comparison').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.pairStatus)')==['exact-text','candidate-text','unmatched-source','unmatched-target']
  checks['exact_enabled']=sync.is_enabled() and sync.is_checked()
  sync.uncheck();checks['manual_disable']=not sync.is_checked()
  page.locator('#next-pair').click();checks['candidate_blocked']=sync.is_disabled() and not sync.is_checked() and status.get_attribute('data-evidence')=='candidate-text'
  page.locator('#next-pair').click();checks['unmatched_source_blocked']=sync.is_disabled() and not sync.is_checked()
  page.locator('#next-pair').click();checks['unmatched_target_blocked']=sync.is_disabled() and not sync.is_checked()
  for _ in range(3):page.locator('#previous-pair').click()
  checks['manual_preference_restored']=sync.is_enabled() and not sync.is_checked()
  sync.check();checks['manual_reenable']=sync.is_checked()
  page.locator('#next-pair').click();page.locator('#previous-pair').click()
  checks['enabled_preference_restored']=sync.is_enabled() and sync.is_checked()
  checks['no_js_errors']=not errors
  page.screenshot(path=str(out/'pair-sync-chromium-linux-real.png'),full_page=True)
  browser.close()
 result={'platform':'Chromium Linux headless','windows_native_tested':False,'checks':checks,'passed':all(checks.values()),'errors':errors}
 (out/'qualification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
 return result
if __name__=='__main__':
 r=run(Path(__file__).with_name('captures-v24.2'));print(json.dumps(r,indent=2,ensure_ascii=False));raise SystemExit(0 if r['passed'] else 1)
