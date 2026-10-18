import unittest
from diagnostic_dashboard import build_dashboard

class ZoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=build_dashboard({})
    def test_zoom_controls(self):
        for name in ('zoom-in','zoom-out','zoom-reset','zoom-status'):
            self.assertIn('id="'+name+'"',self.html)
    def test_sync_control(self):
        self.assertIn('id="sync-scroll"',self.html)
        self.assertIn('Défilement synchronisé',self.html)
    def test_bounded_zoom(self):
        self.assertIn('zoomLevels=[50,75,100,125,150,200,250,300]',self.html)
        self.assertIn('Math.min(zoomIndex+1,zoomLevels.length-1)',self.html)
    def test_ratio_based_scroll(self):
        self.assertIn('pane.scrollTop/yMax',self.html)
        self.assertIn('other.scrollHeight-other.clientHeight',self.html)
    def test_missing_pane_excluded(self):
        self.assertIn('.compare-pane:not(.missing)',self.html)
        self.assertIn('panes.length!==2',self.html)
    def test_no_network_sync(self):
        self.assertNotIn('fetch(',self.html)
        self.assertNotIn('WebSocket(',self.html)
    def test_version(self):
        self.assertIn('Diagnostic V25.4',self.html)

if __name__=='__main__':unittest.main()
