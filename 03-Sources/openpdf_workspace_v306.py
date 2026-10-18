"""V30.6: deterministic action selection and normalized matching. Abdelhalim Talbi."""
import unicodedata
from openpdf_workspace_v304 import available_actions, dispatch

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value)).casefold() if not unicodedata.combining(c))

def search_actions(query=''):
    terms=normalize(query).split()
    return tuple(a for a in available_actions() if all(term in normalize(' '.join(a)) for term in terms))

def selected_action(actions, selection):
    """Resolve selection safely; stale/invalid IDs must not execute an unrelated action."""
    if not selection: return None
    try:
        index=int(selection[0])
    except (ValueError, TypeError, IndexError):
        return None
    if index<0 or index>=len(actions): return None
    return actions[index][2]

def connect(app):
    from openpdf_workspace_v305 import connect as previous
    previous(app)
    if getattr(app,'_v306_connected',False): return app
    app._v306_connected=True
    # V30.5 owns the searchable dialog. The V30.6 adapter is intentionally
    # headless: it supplies independently testable selection/normalization.
    return app
