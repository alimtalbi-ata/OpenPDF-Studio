"""Single UI lifecycle coordinator; pure Python, independently testable.
Author: Abdelhalim Talbi.
"""
class UIController:
    def __init__(self, schedule, cancel):
        self._schedule, self._cancel = schedule, cancel
        self._tokens = set()
        self.closed = False

    def schedule(self, delay, callback):
        if self.closed:
            return None
        token_box = [None]
        def invoke():
            self._tokens.discard(token_box[0])
            if not self.closed:
                callback()
        token = self._schedule(delay, invoke)
        token_box[0] = token
        self._tokens.add(token)
        return token

    def close(self):
        if self.closed:
            return
        self.closed = True
        for token in tuple(self._tokens):
            try:
                self._cancel(token)
            except (ValueError, RuntimeError, KeyError):
                pass
        self._tokens.clear()

    @property
    def pending(self):
        return len(self._tokens)
