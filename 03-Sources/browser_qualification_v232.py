"""Real Chromium smoke qualification of the generated offline HTML dashboard.
Requires: pip install playwright and a Chromium binary. No fake screenshots.
"""
from pathlib import Path
import json
from diagnostic_dashboard import build_dashboard

def run(out: Path, executable: str = '/usr/bin/chromium') -> dict:
    from playwright.sync_api import sync_playwright
    out.mkdir(parents=True, exist_ok=True)
    html = out / 'diagnostic-v23.2.html'
    html.write_text(build_dashboard({}), encoding='utf-8')
    errors = []
    checks = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=executable, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.set_content(html.read_text(encoding='utf-8'), wait_until='load')
        checks['title'] = 'V23.2' in page.title()
        checks['dashboard'] = page.locator('#qualification-overview').count() == 1
        checks['filters'] = page.locator('#qualification-severity-filter').count() == 1
        checks['exports'] = page.locator('#export').count() == 1
        page.locator('#qualification-severity-filter').select_option('high')
        checks['filter_change'] = page.locator('#qualification-severity-filter').input_value() == 'high'
        page.locator('#qualification-filter-reset').click()
        checks['filter_reset'] = page.locator('#qualification-severity-filter').input_value() == 'all'
        checks['no_runtime_errors'] = not errors
        page.screenshot(path=str(out / 'dashboard-chromium-real.png'), full_page=True)
        browser.close()
    result = {'browser': 'Chromium (Linux, headless)', 'checks': checks, 'page_errors': errors, 'passed': all(checks.values()), 'screenshot': 'dashboard-chromium-real.png', 'windows_native_tested': False}
    (out / 'browser-qualification.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    return result

if __name__ == '__main__':
    result = run(Path(__file__).with_name('captures-v23.2'))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
