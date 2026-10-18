"""Lifecycle helpers for single scheduled UI refresh. Author: Abdelhalim Talbi."""
class RefreshScheduler:
    def __init__(self, schedule, cancel):
        self._schedule = schedule
        self._cancel = cancel
        self._token = None
        self._closed = False

    def start(self, callback, interval=180):
        if self._closed or self._token is not None:
            return False
        def tick():
            self._token = None
            if self._closed:
                return
            callback()
            if not self._closed:
                self._token = self._schedule(interval, tick)
        self._token = self._schedule(interval, tick)
        return True

    def close(self):
        self._closed = True
        token, self._token = self._token, None
        if token is not None:
            try:
                self._cancel(token)
            except (ValueError, RuntimeError, KeyError):
                pass

    @property
    def closed(self):
        return self._closed
