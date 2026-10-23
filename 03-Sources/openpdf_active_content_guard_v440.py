"""Fail-closed preflight for active and signed PDFs during compression.

V44.2. Author: Abdelhalim Talbi.

This is a deliberately conservative *presence* check, not a PDF malware
scanner or a signature verifier. OpenPDF Studio does not execute PDF actions.
Unknown automatic actions, XFA and signed documents are not safely rewritable.
"""

from urllib.parse import urlsplit
import unicodedata


def _check_uri_action(doc, xref):
    """Accept only bounded, ordinary external links; never execute PDF URIs.

    MuPDF decodes PDF string escapes before returning the URI. We validate the
    decoded value, not a byte substring or a display URL returned by get_links.
    """
    kind, uri = doc.xref_get_key(xref, "A/URI")
    if kind != "string" or not 1 <= len(uri) <= 2048:
        raise RuntimeError("URI PDF absente ou invalide : compression refusée")
    if any(char.isspace() or unicodedata.category(char) in ("Cc", "Cf")
           or char == "\\" for char in uri):
        raise RuntimeError("URI PDF avec caractères interdits : compression refusée")
    try:
        parsed = urlsplit(uri)
    except ValueError as exc:
        raise RuntimeError("URI PDF malformée : compression refusée") from exc
    if parsed.scheme not in ("http", "https", "mailto"):
        raise RuntimeError("Schéma URI PDF non autorisé : compression refusée")
    if parsed.scheme in ("http", "https") and not parsed.hostname:
        raise RuntimeError("URI PDF sans hôte : compression refusée")
    if parsed.scheme == "mailto" and not parsed.path:
        raise RuntimeError("URI mailto PDF vide : compression refusée")


def _present(doc, xref, key):
    """Use MuPDF's PDF parser, never regex-search arbitrary PDF byte streams."""
    kind, _ = doc.xref_get_key(xref, key)
    return kind != 'null'


def reject_unsafe_rewrite(doc):
    """Reject PDFs whose security/interaction semantics cannot be preserved.

    Called for BOTH source and output. Ordinary URI and internal navigation
    links remain supported; automatic and unknown actions are refused.
    """
    # MuPDF transparently opens encrypted PDFs whose user password is empty.
    # In that case needs_pass == 0 and is_encrypted == False even though the
    # trailer still contains /Encrypt and saving would strip PDF permissions.
    # Inspect the parsed trailer, not a byte-string search.
    if doc.needs_pass or _present(doc, -1, 'Encrypt'):
        raise RuntimeError('PDF chiffré ou protégé : compression refusée')
    if doc.get_sigflags() > 0:
        raise RuntimeError('PDF signé ou signatures déclarées : compression refusée')
    catalog = doc.pdf_catalog()
    for key, label in (
        ('OpenAction', 'Action automatique du document'),
        ('AA', 'Actions automatiques du document'),
        ('Names/JavaScript', 'JavaScript du document'),
        ('AcroForm/XFA', 'Formulaire XFA'),
        ('Perms', 'Restrictions ou certification du document'),
    ):
        if _present(doc, catalog, key):
            raise RuntimeError(f'{label} : compression refusée')
    for index, page in enumerate(doc):
        if _present(doc, page.xref, 'AA'):
            raise RuntimeError(f'Action automatique sur page {index + 1} : compression refusée')
        # annot_xrefs includes link annotations, unlike page.annots(). A link
        # action /Launch or /GoToR must never be silently accepted as a URI.
        for xref, kind, _ in page.annot_xrefs():
            if _present(doc, xref, 'AA'):
                label = 'formulaire' if kind == 21 else 'annotation ou lien'
                raise RuntimeError(f'Action automatique sur {label} : compression refusée')
            # A benign-looking URI can chain /Next to a Launch/JavaScript
            # action. Unknown actions and named viewer actions are not safe to
            # rewrite, even when the rendered page appears unchanged.
            if _present(doc, xref, 'A'):
                if _present(doc, xref, 'A/Next'):
                    raise RuntimeError('Action en chaîne sur annotation ou lien : compression refusée')
                action_kind, action = doc.xref_get_key(xref, 'A/S')
                if action_kind != 'name' or action not in ('/URI', '/GoTo'):
                    raise RuntimeError('Action d’annotation ou lien non prise en charge : compression refusée')
                if action == '/URI':
                    _check_uri_action(doc, xref)
