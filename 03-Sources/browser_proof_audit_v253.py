"""V25.3 browser audit qualification on real synthetic PDF fixtures."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
from browser_proof_export_v252 import run as make_fixture

def run(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 baseline=make_fixture(out)
 html=(out/'dashboard.html').read_text(encoding='utf-8');checks={};errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':900},accept_downloads=True)
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html,wait_until='load')
  button=page.locator('#proof-audit-export-v253');reset=page.locator('#proof-audit-reset-v253');status=page.locator('#proof-audit-status-v253')
  checks['initially_disabled']=button.is_disabled() and reset.is_disabled()
  page.locator('#region-pair-source').click();checks['source_recorded']='1 sélection' in status.inner_text() and button.is_enabled()
  page.locator('#region-pair-target').click();checks['target_recorded']='2 sélection' in status.inner_text()
  page.locator('#next-pair').click();checks['navigation_keeps_history']='2 sélection' in status.inner_text()
  page.locator('#region-pair-source').click();checks['unmatched_recorded']='3 sélection' in status.inner_text()
  with page.expect_download() as dl:button.click()
  payload=json.loads(Path(dl.value.path()).read_text())
  checks['download_filename']=dl.value.suggested_filename=='openpdf-region-audit-v25.3.json'
  checks['schema_count']=payload['schema']=='openpdf-region-audit-v25.3' and payload['selection_count']==3
  checks['sides']=[x['document_side'] for x in payload['entries']]==['source','target','source']
  checks['sequence']=[x['sequence'] for x in payload['entries']]==[1,2,3]
  checks['bbox_valid']=all(x['pdf_bbox_pt']==[40,60,140,110] for x in payload['entries'])
  checks['unmatched_status']=payload['entries'][-1]['page_pair_status']=='unmatched-source'
  checks['no_cross_region_assertion']=all(x['region_cross_document_match']=='not_asserted' for x in payload['entries'])
  reset.click();checks['reset_disables']=button.is_disabled() and reset.is_disabled() and '0 sélection' in status.inner_text()
  checks['no_js_errors']=not errors
  page.screenshot(path=str(out/'audit-chromium-linux-real.png'),full_page=True)
  browser.close()
 result={'browser':'Chromium Linux headless','windows_native_tested':False,'baseline':baseline['passed'],'checks':checks,'passed':all(checks.values()) and baseline['passed'],'page_errors':errors}
 (out/'qualification-v25.3.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 return result
if __name__=='__main__':
 r=run(Path(__file__).with_name('captures-v25.3'));print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['passed'] else 1)
