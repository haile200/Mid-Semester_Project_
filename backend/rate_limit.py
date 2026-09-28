import threading
import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    """Allows `limit` events per key in any `window_seconds`.

    Counts live in this process's memory: each gunicorn worker keeps its own, and a restart clears them.
    """

    def __init__(self, limit, window_seconds, clock=time.monotonic):
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock
        self._events = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key):
        """Records the event if allowed and returns 0; otherwise returns the seconds until a slot frees up."""
        now = self._clock()
        with self._lock:
            events = self._events[key]
            while events and now - events[0] >= self.window_seconds:
                events.popleft()
            if len(events) >= self.limit:
                return self.window_seconds - (now - events[0])
            events.append(now)
            return 0
