"""Stable entrypoint. Author: Abdelhalim Talbi."""
import sys
import os
from pathlib import Path

def main():
    if ('--functional-self-test' in sys.argv or '--self-test' in sys.argv) and os.environ.get('OPENPDF_SMOKE_OUTPUT'):
        output = Path(os.environ['OPENPDF_SMOKE_OUTPUT'])
        output.parent.mkdir(parents=True, exist_ok=True)
        stream = output.open('w', encoding='utf-8')
        sys.stdout = stream
        sys.stderr = stream
    if '--functional-self-test' in sys.argv:
        from openpdf_functional_smoke import run
        return run()
    if '--self-test' in sys.argv:
        from openpdf_operations import OPERATIONS
        from openpdf_navigation import validate_request
        from openpdf_jobs import JobState
        if not OPERATIONS or not callable(validate_request) or JobState is None:
            return 2
        print('OPENPDF_SELF_TEST_OK')
        return 0
    if '--ocr-office' in sys.argv:
        from openpdf_ocr_office_pipeline_v511 import main as ocr_office_main
        return ocr_office_main(sys.argv[sys.argv.index('--ocr-office') + 1:])
    from openpdf_desktop import OpenPDFStudio
    OpenPDFStudio().mainloop()
    return 0

if __name__ == '__main__':
    sys.exit(main())
