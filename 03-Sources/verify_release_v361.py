"""Historical V36.1 artifact check; current release uses verify_release_v362.py."""
from pathlib import Path
p=Path(__file__).resolve().parent
assert (p/'OpenPDF-Studio-V36.1.iss').is_file()
assert '#define AppVersion "36.1"' in (p/'OpenPDF-Studio-V36.1.iss').read_text()
print('V36.1 historical artifacts present; current build must use V36.2 verifier')
