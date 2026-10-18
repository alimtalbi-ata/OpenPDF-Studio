import unittest, tempfile
from pathlib import Path
from openpdf_dependency_audit import static_imports,audit_directory,runtime_snapshot
class V363(unittest.TestCase):
 def test_imports(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"a.py";p.write_text("import os, json\nfrom pathlib import Path\n")
   self.assertEqual(static_imports(p),["os","json","pathlib"] if False else ["json","os","pathlib"])
 def test_audit(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/"openpdf_studio.py").write_text("import helper\n");(p/"helper.py").write_text("x=1\n");(p/"unused.py").write_text("x=2\n")
   a=audit_directory(p);self.assertEqual(a["static_reachable"],["helper","openpdf_studio"]);self.assertEqual(a["static_unreachable_count"],1)
 def test_dynamic_snapshot(self):
  self.assertIn("openpdf_dependency_audit",runtime_snapshot())
 def test_desktop_uses_canonical(self):
  s=(Path(__file__).parent/"openpdf_desktop.py").read_text()
  for name in ("openpdf_operations", "openpdf_navigation", "openpdf_jobs"):self.assertIn("from "+name+" import",s)
 def test_adapters(self):
  from openpdf_operations import OPERATIONS,run_operation
  from openpdf_navigation import next_page
  from openpdf_jobs import JobState
  self.assertTrue(OPERATIONS);self.assertTrue(callable(run_operation));self.assertTrue(callable(next_page));self.assertTrue(JobState)
if __name__=="__main__":unittest.main()
