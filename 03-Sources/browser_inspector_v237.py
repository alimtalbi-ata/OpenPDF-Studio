"""Actual Chromium Linux UI qualification, including real synthetic PDF page previews."""
from pathlib import Path
import json
import fitz
from playwright.sync_api import sync_playwright
from diagnostic_dashboard import build_dashboard

def run(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    a,b=out/'source.pdf',out/'target.pdf'
    for path,label in [(a,'SOURCE'),(b,'TARGET')]:
        with fitz.open() as doc:
            for i in range(2):
                page=doc.new_page();page.insert_text((80,100),f'{label} PAGE {i+1}')
            doc.save(path)
    report={'page_annotations':[{'side':'source','page':1,'bbox':[70,85,220,120],'severity':'high','summary':'Contrôle A'}, {'side':'target','page':2,'bbox':[70,85,220,120],'severity':'low','summary':'Contrôle B'}]}
    html=out/'dashboard-v23.7.html';html.write_text(build_dashboard(report,source_pdf=a,target_pdf=b),encoding='utf-8')
    checks={};errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':900})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html.read_text(encoding='utf-8'),wait_until='load')
        checks['title']='V23.7' in page.title()
        checks['two_findings']=page.locator('tbody tr[data-severity]').count()==2
        checks['real_pdf_previews']=page.locator('.compare-pane img').count()>=2
        checks['initial_status']='2 constat(s)' in page.locator('#inspector-status').inner_text()
        page.locator('#inspector-next').click()
        checks['first_selection']='Constat 1 / 2' in page.locator('#inspector-status').inner_text()
        checks['detail_a']='Contrôle A' in page.locator('#inspector-detail').inner_text()
        page.locator('#inspector-next').click()
        checks['second_selection']='Constat 2 / 2' in page.locator('#inspector-status').inner_text()
        checks['detail_b']='Contrôle B' in page.locator('#inspector-detail').inner_text()
        page.locator('#inspector-prev').click()
        checks['previous']='Constat 1 / 2' in page.locator('#inspector-status').inner_text()
        page.locator('#severity').select_option('low')
        checks['filter_resets_selection']='1 constat(s)' in page.locator('#inspector-status').inner_text()
        page.locator('#inspector-next').click()
        checks['filtered_detail']='Contrôle B' in page.locator('#inspector-detail').inner_text()
        checks['end_disabled']=page.locator('#inspector-next').is_disabled()
        checks['no_js_errors']=not errors
        page.screenshot(path=str(out/'inspector-chromium-linux-real.png'),full_page=True)
        browser.close()
    result={'browser':'Chromium Linux headless','pdf_fixture':'real synthetic PDF files','checks':checks,'passed':all(checks.values()),'page_errors':errors,'windows_native_tested':False,'screenshot':'inspector-chromium-linux-real.png'}
    (out/'browser-inspector-qualification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    return result
if __name__=='__main__':
    r=run(Path(__file__).with_name('captures-v23.7'));print(json.dumps(r,indent=2,ensure_ascii=False));raise SystemExit(0 if r['passed'] else 1)
