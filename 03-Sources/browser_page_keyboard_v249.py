"""Browser verification of keyboard navigation with genuine synthetic PDF fixtures."""
from pathlib import Path
import json
import fitz
from playwright.sync_api import sync_playwright
from diagnostic_dashboard import build_dashboard

def run(out):
 out=Path(out);out.mkdir(exist_ok=True,parents=True)
 src,tgt=out/'source.pdf',out/'target.pdf'
 for path,side in [(src,'source'),(tgt,'target')]:
  with fitz.open() as doc:
   page=doc.new_page();page.insert_text((100,100),side+' keyboard test');doc.save(path)
 def region(side,bbox):
  return dict(side=side,page=1,coordinate_space='full_page_raster',rotation=0,raster_width=595,raster_height=842,pdf_width=595,pdf_height=842,bbox=bbox)
 report={'page_annotations':[{'side':'source','page':1,'bbox':[40,60,150,110],'severity':'high','summary':'Source'},{'side':'target','page':1,'bbox':[60,80,170,130],'severity':'low','summary':'Target'}],'multipage_audit':{'exact_text_page_matches':[{'source_page':1,'target_page':1}]},'visual_regions_raster_space':[region('source',[40,60,150,110]),region('source',[180,180,280,230]),region('target',[60,80,170,130])]}
 html=out/'dashboard.html';html.write_text(build_dashboard(report,source_pdf=src,target_pdf=tgt),encoding='utf-8')
 checks={};errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':900});page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html.read_text(encoding='utf-8'),wait_until='load')
  checks['version']=page.title()=='OpenPDF Studio V24.9'
  checks['source_regions']=page.locator('#preview-source-1 .pdf-region').count()==2
  checks['target_regions']=page.locator('#preview-target-1 .pdf-region').count()==1
  checks['shortcut_help']=page.locator('#region-keyboard-hint-v248').count()==1
  page.keyboard.press('Alt+Shift+s')
  checks['source_shortcut']=page.locator('#preview-source-1 .pdf-region.is-selected').count()==1
  checks['source_status']='source' in page.locator('#region-keyboard-status-v248').inner_text()
  page.keyboard.press('Alt+Shift+c')
  checks['target_shortcut']=page.locator('#preview-target-1 .pdf-region.is-selected').count()==1
  page.keyboard.press('Escape')
  checks['escape_clear']=page.locator('.pdf-region.is-selected').count()==0
  page.locator('#query').focus();page.keyboard.press('Alt+Shift+s')
  checks['typing_guard']=page.locator('.pdf-region.is-selected').count()==0
  page.locator('#query').blur()
  page.keyboard.press('Alt+Shift+s')
  checks['shortcut_after_blur']=page.locator('#preview-source-1 .pdf-region.is-selected').count()==1
  checks['page_help']=page.locator('#page-keyboard-help-v249').count()==1
  checks['page_status']=bool(page.locator('#page-keyboard-status-v249').inner_text())
  checks['page_shortcut_no_overrun']=page.locator('#next-pair').is_disabled()
  page.locator('#query').focus();page.keyboard.press('Alt+Shift+ArrowRight')
  checks['page_typing_guard']=page.locator('#next-pair').is_disabled()
  checks['no_js_errors']=not errors
  page.screenshot(path=str(out/'keyboard-chromium-linux-real.png'),full_page=True)
  browser.close()
 result={'browser':'Chromium Linux headless','windows_native_tested':False,'real_pdf_fixtures':True,'checks':checks,'passed':all(checks.values()),'page_errors':errors}
 (out/'qualification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 return result
if __name__=='__main__':
 result=run(Path(__file__).with_name('captures-v24.9'));print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['passed'] else 1)
