import tempfile, unittest
from pathlib import Path
from diagnostic_dashboard import locate_text_differences, build_dashboard

class TextLocalizationTests(unittest.TestCase):
    def make_pdf(self, lines):
        import fitz
        tmp=tempfile.TemporaryDirectory(); path=Path(tmp.name)/'source.pdf'
        doc=fitz.open(); page=doc.new_page()
        for i,line in enumerate(lines):page.insert_text((72,80+25*i),line)
        doc.save(path);doc.close()
        return tmp,path

    def test_unique_match(self):
        tmp,path=self.make_pdf(['Unique fragment here'])
        with tmp:
            matches=locate_text_differences({'text_differences':[{'side':'source','page':1,'text':'Unique fragment'}]},{'source':path})
            self.assertEqual(len(matches),1)
            self.assertEqual(matches[0]['evidence'],'pdf_text_search')
            self.assertEqual(len(matches[0]['bbox']),4)

    def test_duplicate_ambiguous(self):
        tmp,path=self.make_pdf(['Repeated phrase','Repeated phrase'])
        with tmp:self.assertEqual(locate_text_differences({'text_differences':[{'side':'source','page':1,'text':'Repeated phrase'}]},{'source':path}),[])

    def test_missing_fragment(self):
        tmp,path=self.make_pdf(['Something else'])
        with tmp:self.assertEqual(locate_text_differences({'text_differences':[{'side':'source','page':1,'text':'Not present'}]},{'source':path}),[])

    def test_invalid_page_and_fragment(self):
        tmp,path=self.make_pdf(['Unique fragment here'])
        with tmp:self.assertEqual(locate_text_differences({'text_differences':[{'side':'source','page':True,'text':'Unique fragment'},{'side':'source','page':2,'text':'Unique fragment'},{'side':'source','page':1,'text':'a'}]},{'source':path}),[])

    def test_dashboard_contains_localized_zone(self):
        tmp,path=self.make_pdf(['Unique fragment here'])
        with tmp:
            html=build_dashboard({'text_differences':[{'side':'source','page':1,'text':'Unique fragment'}]},source_pdf=path)
            self.assertIn('Correspondance textuelle localisée',html)
            self.assertIn('preview-source-1',html)
            self.assertIn('data:image/png;base64,',html)

    def test_no_pdf_no_claim(self):
        self.assertEqual(locate_text_differences({'text_differences':[{'side':'source','page':1,'text':'hello'}]},{}),[])

if __name__=='__main__':unittest.main()
