"""Protection for Wikidata: a small TTL/LRU cache, at most two requests in flight, and exponential back-off.

Many visitors asking at once make Wikidata answer 429 («too many requests»).  Every Wikidata call goes
through `get()`: repeated entities and properties come from memory for ten minutes, only two requests run
at the same time, and a 429 / timeout / 5xx waits 0.4 s, then 0.8 s, before the next attempt.
"""
import threading
import time
from collections import OrderedDict

import httpx

API = "https://www.wikidata.org/w/api.php"
DELAYS = (0.4, 0.8)            # exponential back-off: 0.4 s, then 0.8 s
RETRY_STATUS = {429, 500, 502, 503, 504}
_GATE = threading.Semaphore(2)


class TTLCache:
    """Least-recently-used cache whose entries expire after `ttl` seconds (thread-safe)."""

    def __init__(self, maxsize: int = 512, ttl: float = 600.0):
        self.maxsize, self.ttl = maxsize, ttl
        self._data: OrderedDict = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            stamp, value = self._data.get(key, (0.0, None))
            if value is None or time.time() - stamp > self.ttl:
                self._data.pop(key, None)
                return None
            self._data.move_to_end(key)
            return value

    def put(self, key, value) -> None:
        with self._lock:
            self._data[key] = (time.time(), value)
            self._data.move_to_end(key)
            while len(self._data) > self.maxsize:
                self._data.popitem(last=False)


CACHE = TTLCache()


def get(http: httpx.Client, params: dict) -> dict:
    """The JSON answer of one Wikidata API call (cached, throttled, retried); raises httpx.HTTPError if it never works."""
    key = tuple(sorted((k, str(v)) for k, v in params.items()))
    cached = CACHE.get(key)
    if cached is not None:
        return cached
    for attempt in range(len(DELAYS) + 1):
        with _GATE:                                   # the wait below happens outside the gate
            try:
                resp = http.get(API, params=params)
                if resp.status_code not in RETRY_STATUS:
                    data = resp.json()
                    CACHE.put(key, data)
                    return data
            except httpx.TimeoutException:
                pass
        if attempt < len(DELAYS):
            time.sleep(DELAYS[attempt])
    raise httpx.HTTPError("Wikidata لم يردّ بعد إعادة المحاولة")
