# OpenPDF Studio V50.6 — Compression quality evidence

Author: Abdelhalim Talbi. Date: 2026-10-23.

V50.6 binds the production full-RGB quality audit to the **actual** candidate
bytes, SHA-256 hashes, policy, source identity and profile before exclusive
publication. Accepted profiles now include measured page count, pixel count,
MAE, changed fraction and render scale. A missing or mismatched audit rejects
the candidate without publishing a PDF.

Qualification: 11 new functional tests on real synthetic PDFs, 16 V50.5
regressions, 11 V50.4 benchmark tests and 12 static reconciliation tests passed
locally on Linux. Static closure: 88 required modules, none missing.
Native Windows V50.6 build/installer and GUI qualification are NOT claimed
until corresponding GitHub Actions jobs complete successfully.

Bounded-scale RGB is not a PDF/A, OCR, print or accessibility certification.
No automatic merge to main.
