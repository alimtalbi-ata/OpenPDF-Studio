import unittest
from diagnostic_dashboard import build_dashboard

class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.html=build_dashboard({'warnings':['review']})
    def test_version(self):self.assertIn('Diagnostic V25.4',self.html)
    def test_overlay_panel(self):self.assertIn('id="overlay-panel"',self.html)
    def test_opacity_range(self):self.assertIn('id="overlay-opacity" type="range" min="0" max="100"',self.html)
    def test_overlay_toggle(self):self.assertIn('id="overlay-enabled"',self.html)
    def test_no_auto_registration(self):self.assertIn('aucun recalage automatique',self.html)
    def test_no_network(self):self.assertNotIn('fetch(',self.html)
    def test_fallback_for_unpaired(self):self.assertIn('overlayPanel.hidden=!overlayEnabled.checked||!valid',self.html)
    def test_escaping(self):self.assertNotIn('<script>alert(1)</script>',build_dashboard({'warnings':['<script>alert(1)</script>']}))
if __name__=='__main__':unittest.main()
