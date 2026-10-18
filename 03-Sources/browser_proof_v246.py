"""Chromium end-to-end test for real verified regions, including negative controls."""
from pathlib import Path
import json
import fitz
from playwright.sync_api import sync_playwright
from diagnostic_dashboard import build_dashboard

def run(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 source,target=out/'source.pdf',out/'target.pdf'
 for path,label in [(source,'SOURCE'),(target,'TARGET')]:
  with fitz.open() as d:
   p=d.new_page();p.insert_text((100,110),label+' verified region sample');d.save(path)
 def region(side,bbox):
  return dict(side=side,page=1,coordinate_space='full_page_raster',rotation=0,raster_width=595,raster_height=842,pdf_width=595,pdf_height=842,bbox=bbox)
 report={'page_annotations':[{'side':'source','page':1,'bbox':[100,90,260,130],'severity':'high','summary':'Contrôle source'}, {'side':'target','page':1,'bbox':[100,90,260,130],'severity':'low','summary':'Contrôle cible'}], 'multipage_audit':{'exact_text_page_matches':[{'source_page':1,'target_page':1}]}, 'visual_regions_raster_space':[region('source',[100,90,260,130]),region('source',[290,170,390,210]),region('target',[100,90,260,130]),region('source',[600,0,620,10])]}
 html=out/'dashboard-v24.6.html';html.write_text(build_dashboard(report,source_pdf=source,target_pdf=target),encoding='utf-8')
 checks={};errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':900});page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html.read_text(encoding='utf-8'),wait_until='load')
  checks['version']='V24.6' in page.title()
  checks['pdf_previews']=page.locator('.compare-pane img').count()>=2
  checks['source_regions']=page.locator('#preview-source-1 .pdf-region').count()==2
  checks['target_regions']=page.locator('#preview-target-1 .pdf-region').count()==1
  checks['invalid_region_rejected']=page.locator('.pdf-region').count()==3
  checks['button_initially_disabled']=page.locator('#inspector-region').is_disabled()
  page.locator('#inspector-next').click()
  checks['source_button_enabled']=page.locator('#inspector-region').is_enabled()
  checks['source_region_count']='(2)' in page.locator('#inspector-region').inner_text()
  page.locator('#inspector-region').click()
  checks['regions_auto_shown']=page.locator('#regions-visible').is_checked()
  checks['first_region_selected']=page.locator('#preview-source-1 .pdf-region.is-selected').count()==1
  checks['focused_region_highlight']=page.locator('.pdf-region.region-focus-v246').count()==1
  checks['focus_status_source']='source' in page.locator('#region-focus-status-v246').inner_text()
  checks['first_region_evidence']='100.00' in page.locator('#region-evidence-fields').inner_text()
  checks['explicit_non_attribution']='non associée automatiquement' in page.locator('#inspector-detail').inner_text()
  page.locator('#inspector-region').click()
  checks['second_region_selected']=page.locator('#preview-source-1 .pdf-region.is-selected').count()==1 and '2 / 2' in page.locator('#inspector-detail').inner_text()
  page.locator('#inspector-region').click()
  checks['wraparound_region']='1 / 2' in page.locator('#inspector-detail').inner_text()
  page.locator('#inspector-next').click()
  checks['target_button_enabled']=page.locator('#inspector-region').is_enabled()
  page.locator('#inspector-region').click()
  checks['focus_status_target']='cible' in page.locator('#region-focus-status-v246').inner_text()
  checks['target_region_selected']=page.locator('#preview-target-1 .pdf-region.is-selected').count()==1
  page.locator('#region-pair-source').click()
  checks['source_navigation_button']=page.locator('#region-pair-proof').get_attribute('data-proof')=='validated' and 'Source' in page.locator('#region-pair-proof').inner_text()
  checks['source_coordinates_provenance']='100.00' in page.locator('#region-pair-proof').inner_text() or '290.00' in page.locator('#region-pair-proof').inner_text()
  page.locator('#region-pair-target').click()
  checks['target_navigation_button']=page.locator('#region-pair-proof').get_attribute('data-proof')=='validated' and 'Cible' in page.locator('#region-pair-proof').inner_text()
  page.locator('#preview-target-1 .pdf-region').click()
  checks['proof_card_source_and_coordinates']=page.locator('#proof-card-v245').get_attribute('data-validated')=='true' and 'Cible' in page.locator('#proof-fields-v245').inner_text() and '100.00' in page.locator('#proof-fields-v245').inner_text()
  checks['no_inferred_region_pairing']='non établie' in page.locator('#proof-warning-v245').inner_text()
  page.locator('#region-selection-clear').click()
  checks['highlight_cleared']=page.locator('.pdf-region.region-focus-v246').count()==0
  checks['clear_proof']=page.locator('#region-pair-proof').get_attribute('data-proof')=='none'
  page.locator('#severity').select_option('high')
  checks['proof_card_cleared']=page.locator('#proof-card-v245').get_attribute('data-validated')=='false' and 'Non disponible' in page.locator('#proof-fields-v245').inner_text()
  checks['filter_clears_selection']=page.locator('#inspector-region').is_disabled()
  checks['no_js_errors']=not errors
  page.screenshot(path=str(out/'proof-card-chromium-linux-real.png'),full_page=True)
  browser.close()
 result={'browser':'Chromium Linux headless','real_pdf_fixtures':True,'windows_native_tested':False,'checks':checks,'passed':all(checks.values()),'page_errors':errors,'screenshot':'proof-card-chromium-linux-real.png'}
 (out/'qualification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');return result
if __name__=='__main__':
 r=run(Path(__file__).with_name('captures-v24.6'));print(json.dumps(r,indent=2,ensure_ascii=False));raise SystemExit(0 if r['passed'] else 1)
