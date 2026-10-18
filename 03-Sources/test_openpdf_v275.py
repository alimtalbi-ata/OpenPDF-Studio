import logging
import tempfile
import unittest
from pathlib import Path
from openpdf_diagnostics_v275 import configure_logging, log_exception

class DiagnosticTests(unittest.TestCase):
    def test_log_created(self):
        with tempfile.TemporaryDirectory() as directory:
            logger = configure_logging(directory)
            logger.info('test event')
            for handler in logger.handlers: handler.flush()
            self.assertIn('test event', (Path(directory)/'openpdf.log').read_text(encoding='utf-8'))
    def test_error_type_logged_not_message(self):
        with tempfile.TemporaryDirectory() as directory:
            logger = logging.getLogger('openpdf_studio')
            for handler in logger.handlers: handler.close()
            logger.handlers.clear()
            logger = configure_logging(directory)
            log_exception(logger, 'merge', ValueError('private_filename.pdf'))
            for handler in logger.handlers: handler.flush()
            content = (Path(directory)/'openpdf.log').read_text(encoding='utf-8')
            self.assertIn('ValueError', content)
            self.assertNotIn('private_filename.pdf', content)
    def test_rotation_configured(self):
        with tempfile.TemporaryDirectory() as directory:
            logger = logging.getLogger('openpdf_studio')
            for handler in logger.handlers: handler.close()
            logger.handlers.clear()
            logger = configure_logging(directory)
            self.assertEqual(logger.handlers[0].maxBytes, 2_000_000)
if __name__=='__main__': unittest.main()
