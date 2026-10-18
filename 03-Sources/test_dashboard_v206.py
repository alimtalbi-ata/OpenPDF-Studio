"""V20.8 UI offset regression tests."""
import unittest
from diagnostic_dashboard import build_dashboard

class TestV206(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page=build_dashboard({})
    def test_version(self):self.assertIn('V20.9',self.page)
    def test_horizontal_control(self):self.assertIn('id="overlay-x"',self.page)
    def test_vertical_control(self):self.assertIn('id="overlay-y"',self.page)
    def test_reset(self):self.assertIn('id="overlay-reset"',self.page)
    def test_transform(self):self.assertIn('transform:translate(var(--overlay-x,0px),var(--overlay-y,0px))',self.page)
    def test_range_limits(self):self.assertIn('Math.max(-150,Math.min(150,n))',self.page)
    def test_no_auto_claim(self):self.assertIn('aucun recalage automatique',self.page)
    def test_x_value(self):self.assertIn('id="overlay-x-value"',self.page)
    def test_y_value(self):self.assertIn('id="overlay-y-value"',self.page)
if __name__=='__main__':unittest.main()
