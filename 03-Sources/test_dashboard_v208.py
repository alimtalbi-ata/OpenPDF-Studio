import unittest
from diagnostic_dashboard import build_dashboard
class V208(unittest.TestCase):
 def setUp(self): self.html=build_dashboard({})
 def test_version(self): self.assertIn('V20.9',self.html)
 def test_scale_control(self): self.assertIn('id="overlay-scale"',self.html)
 def test_scale_limits(self): self.assertIn('min="90" max="110"',self.html)
 def test_scale_css(self): self.assertIn('scale(var(--overlay-scale,1))',self.html)
 def test_scale_search(self): self.assertIn('for(const scale of [.90,.94,.97,1,1.03,1.06,1.10])',self.html)
 def test_reset(self): self.assertIn("scaleInput.value='100'",self.html)
 def test_safe_bounds(self): self.assertIn('Math.abs(x)>150',self.html)
