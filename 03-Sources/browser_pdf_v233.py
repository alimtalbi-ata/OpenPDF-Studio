"""Offline Chromium end-to-end qualification using actual synthetic PDF fixtures."""
from pathlib import Path
import json
import fitz
from playwright.sync_api import sync_playwright
from diagnostic_dashboard import build_dashboard


def run(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    src, dst = out/'source-fixture.pdf', out/'target-fixture.pdf'
    for path, text in ((src,'Source example page alpha'),(dst,'Target example page beta')):
        with fitz.open() as doc:
            for index in range(3):
                page=doc.new_page(width=595,height=842)
                page.insert_text((72,100),f'{text} — page {index+1}',fontsize=16)
                page.draw_rect(fitz.Rect(72,140,350,210),color=(0.1,0.3,0.7),width=2)
                page.insert_text((80,170),f'Section {index+1} / tableau et formes',fontsize=11)
            doc.save(path)
    report={'multipage_audit':{'split_merge_candidates':[{'source_pages':[1,2,3],'target_pages':[1,2,3]}]},'page_annotations':[
        {'side':'source','page':1,'bbox':[70,85,290,115],'severity':'high','summary':'Zone source à contrôler'},
        {'side':'target','page':1,'bbox':[70,85,290,115],'severity':'low','summary':'Zone cible à contrôler'}]}
    html=out/'diagnostic-v23.3.html'
    html.write_text(build_dashboard(report,source_pdf=src,target_pdf=dst),encoding='utf-8')
    checks={};errors=[];downloads={}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page(accept_downloads=True,viewport={'width':1440,'height':900})
        page.on('pageerror',lambda err:errors.append(str(err)))
        page.set_content(html.read_text(encoding='utf-8'),wait_until='load')
        checks['six_page_previews']=page.locator('.comparison').count()>=3
        checks['pdf_previews']=page.locator('.comparison .compare-pane img').count()>=2
        checks['two_findings']=page.locator('tbody tr[data-severity]').count()==2
        checks['initial_count']='2 / 2' in page.locator('#filtered-count').inner_text()
        page.locator('#qualification-severity-filter').select_option('high')
        checks['filter_high']=page.locator('tbody tr[data-severity]:visible').count()==1
        checks['chart_count']='1 / 2' in page.locator('#qualification-chart-count').inner_text()
        with page.expect_download() as d:
            page.locator('#export').click()
        csv=d.value; csv.save_as(out/csv.suggested_filename)
        csv_text=(out/csv.suggested_filename).read_text(encoding='utf-8-sig')
        checks['csv_filtered']='Zone source' in csv_text and 'Zone cible' not in csv_text
        downloads['csv']=csv.suggested_filename
        with page.expect_download() as d:
            page.locator('#export-json').click()
        diagnostic=d.value;diagnostic.save_as(out/diagnostic.suggested_filename)
        checks['json_valid']=isinstance(json.loads((out/diagnostic.suggested_filename).read_text(encoding='utf-8')),dict)
        downloads['json']=diagnostic.suggested_filename
        page.locator('#qualification-filter-reset').click()
        checks['reset_count']='2 / 2' in page.locator('#filtered-count').inner_text()
        page.locator('#next-pair').click()
        checks['navigation_status']='2 /' in page.locator('#pair-status').inner_text()
        page.locator('#next-pair').click()
        checks['third_page_navigation']='3 /' in page.locator('#pair-status').inner_text()
        page.locator('#previous-pair').click()
        checks['previous_page_navigation']='2 /' in page.locator('#pair-status').inner_text()
        page.locator('#zoom-in').click()
        checks['zoom_control']='125' in page.locator('#zoom-status').inner_text()
        page.locator('#zoom-reset').click()
        checks['zoom_reset']='100' in page.locator('#zoom-status').inner_text()
        checks['no_runtime_errors']=not errors
        page.screenshot(path=str(out/'dashboard-pdf-chromium-real.png'),full_page=True)
        browser.close()
    checks['fixture_page_counts']=all(len(fitz.open(p))==3 for p in (src,dst))
    result={'browser':'Chromium Linux headless','pdfs':'synthetic PDF fixtures','checks':checks,'passed':all(checks.values()),'page_errors':errors,'downloads':downloads,'windows_native_tested':False}
    (out/'browser-pdf-qualification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    return result

if __name__=='__main__':
    result=run(Path(__file__).with_name('captures-v23.3'))
    print(json.dumps(result,indent=2,ensure_ascii=False))
    raise SystemExit(0 if result['passed'] else 1)
