"""V25.4 Chromium export + independent Python verification + tamper tests."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
from browser_proof_export_v252 import run as make_fixture
from verify_proof_audit_v254 import verify

def run(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 baseline=make_fixture(out)
 html=(out/'dashboard.html').read_text(encoding='utf-8');checks={};errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':900},accept_downloads=True)
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html,wait_until='load')
  btn=page.locator('#proof-integrity-export-v254')
  checks['disabled_initially']=btn.is_disabled()
  page.locator('#region-pair-source').click();checks['enabled_after_selection']=btn.is_enabled()
  page.locator('#region-pair-target').click();page.locator('#next-pair').click();page.locator('#region-pair-source').click()
  with page.expect_download() as dl:btn.click()
  payload=json.loads(Path(dl.value.path()).read_text(encoding='utf-8'))
  checks['correct_filename']=dl.value.suggested_filename=='openpdf-region-audit-sha256-v25.4.json'
  checks['three_entries']=payload['selection_count']==3
  checks['independent_verification']=verify(payload)[0]
  checks['unmatched_kept']=payload['entries'][-1]['page_pair_status']=='unmatched-source'
  checks['cross_match_not_asserted']=all(e['region_cross_document_match']=='not_asserted' for e in payload['entries'])
  modified=json.loads(json.dumps(payload));modified['entries'][0]['pdf_bbox_pt'][0]+=1
  checks['tamper_detected']=not verify(modified)[0]
  modified=json.loads(json.dumps(payload));modified['entries'].pop(1);modified['selection_count']=2
  checks['deletion_detected']=not verify(modified)[0]
  modified=json.loads(json.dumps(payload));modified['head_sha256']='0'*64
  checks['head_tamper_detected']=not verify(modified)[0]
  page.locator('#proof-audit-reset-v253').click();checks['reset_disables']=btn.is_disabled()
  checks['no_js_errors']=not errors
  page.screenshot(path=str(out/'integrity-chromium-linux-real.png'),full_page=True)
  browser.close()
 (out/'audit-sha256-sample.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
 result={'browser':'Chromium Linux headless','windows_native_tested':False,'baseline':baseline['passed'],'checks':checks,'passed':all(checks.values()) and baseline['passed'],'page_errors':errors}
 (out/'qualification-v25.4.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 return result
if __name__=='__main__':
 r=run(Path(__file__).with_name('captures-v25.4'));print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['passed'] else 1)
