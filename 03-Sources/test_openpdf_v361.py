import ast, json, unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class V361(unittest.TestCase):
 def test_canonical_entrypoint(self):
  tree=ast.parse((P/'openpdf_studio.py').read_text());self.assertTrue(tree)
 def test_dependency_graph(self):
  r=json.loads((P.parent/'04-Tests-et-Qualification'/'ARCHITECTURE-IMPORTS-V36.1.json').read_text());self.assertGreater(r['files_python'],50);self.assertIn('openpdf_windows_v358',r['reachable_versioned_ui_modules'])
 def test_build_config(self):
  b=(P.parent/'02-Compilation'/'BUILD-WINDOWS-INSTALLER.cmd').read_text();self.assertIn('openpdf_studio.py',b);self.assertNotIn('OpenPDF-Studio-V35.9.iss',b)
 def test_iss(self):
  self.assertIn('AppVersion "36.1"',(P/'OpenPDF-Studio-V36.1.iss').read_text())
 def test_verifier(self):
  import subprocess,sys
  r=subprocess.run([sys.executable,str(P/'verify_release_v361.py')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
if __name__=='__main__':unittest.main()
