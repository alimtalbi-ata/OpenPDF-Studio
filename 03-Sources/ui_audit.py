"""Static accessibility and interaction contract audit for exported HTML. Not a browser test."""
from html.parser import HTMLParser
import json
from pathlib import Path

class Inspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids=set(); self.duplicates=[]; self.labels=[]; self.controls=[]; self.links=[]; self.lang=False; self.title=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='html': self.lang=bool(a.get('lang'))
        if tag=='title': self.title=True
        if a.get('id'):
            if a['id'] in self.ids: self.duplicates.append(a['id'])
            self.ids.add(a['id'])
        if tag=='label' and a.get('for'):self.labels.append(a['for'])
        if tag in ('input','select','textarea') and a.get('id'):self.controls.append((tag,a['id'],bool(a.get('aria-label'))))
        if tag=='a' and a.get('href','').startswith('#'):self.links.append(a['href'][1:])

def audit_html(html):
    parser=Inspector();parser.feed(html)
    issues=[]
    if not parser.lang:issues.append('Document language missing')
    if not parser.title:issues.append('Document title missing')
    for key in sorted(set(parser.duplicates)):issues.append('Duplicate id: '+key)
    for key in sorted(set(parser.labels)-parser.ids):issues.append('Label points to missing id: '+key)
    for tag,key,aria in parser.controls:
        if key not in parser.labels and not aria:issues.append('Unlabelled control: '+tag+'#'+key)
    for key in sorted(set(parser.links)-parser.ids):issues.append('Broken anchor: #'+key)
    return {'passed':not issues,'issues':issues,'checked_ids':len(parser.ids),'controls':len(parser.controls),'scope':'static HTML only; not browser, keyboard or Windows certification'}

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('html_file');ap.add_argument('--output');args=ap.parse_args()
    result=audit_html(Path(args.html_file).read_text(encoding='utf-8'))
    rendered=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:Path(args.output).write_text(rendered+'\n',encoding='utf-8')
    print(rendered)
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
