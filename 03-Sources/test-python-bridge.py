import unittest
from pathlib import Path
import tempfile
from python_bridge import run_diagnostic, DiagnosticBridgeError

P = {'width': 600, 'height': 800, 'blocks': [{'text': 'Example', 'box': {'x': 30, 'y': 50, 'w': 100, 'h': 20}}]}

class BridgeTests(unittest.TestCase):
    def test_round_trip(self):
        result = run_diagnostic([P], [P])
        self.assertIsInstance(result, dict)
        self.assertIn('report', result)
    def test_invalid_pages(self):
        with self.assertRaises(DiagnosticBridgeError):
            run_diagnostic([{'bad': True}], [P])
    def test_timeout_validation(self):
        with self.assertRaises(ValueError):
            run_diagnostic([P], [P], timeout=0)
    def test_missing_node(self):
        with self.assertRaises(DiagnosticBridgeError):
            run_diagnostic([P], [P], node_executable='node-does-not-exist-r22')
    def test_invalid_response(self):
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / 'invalid.js'
            script.write_text('process.stdout.write("not json")')
            with self.assertRaises(DiagnosticBridgeError):
                run_diagnostic([P], [P], bridge_path=script)
    def test_non_finite_rejected(self):
        bad = dict(P, width=float('nan'))
        with self.assertRaises(DiagnosticBridgeError):
            run_diagnostic([bad], [P])

if __name__ == '__main__':
    unittest.main(verbosity=2)
