"""Scarcity example: limit concurrent resource usage with a semaphore.

Run:
    python scarcity_example.py
"""

from __future__ import annotations

import random
import threading
import time


MAX_CONCURRENT_CALLS = 3
TOTAL_REQUESTS = 10


class ApiGate:
    """Allow only a fixed number of concurrent API calls."""

    def __init__(self, max_concurrent: int) -> None:
        self._semaphore = threading.Semaphore(max_concurrent)
        self._active = 0
        self._peak = 0
        self._lock = threading.Lock()

    @property
    def peak_active(self) -> int:
        return self._peak

    def call_external_api(self, request_id: int) -> None:
        self._semaphore.acquire()
        try:
            with self._lock:
                self._active += 1
                self._peak = max(self._peak, self._active)
                current_active = self._active

            print(f"request-{request_id} started (active={current_active})")
            time.sleep(random.uniform(0.08, 0.2))
            print(f"request-{request_id} finished")
        finally:
            # Always release in finally to avoid permit leaks.
            with self._lock:
                self._active -= 1
            self._semaphore.release()


def main() -> None:
    gate = ApiGate(max_concurrent=MAX_CONCURRENT_CALLS)

    threads = [
        threading.Thread(target=gate.call_external_api, args=(i,))
        for i in range(1, TOTAL_REQUESTS + 1)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    print(f"\nPeak concurrent calls observed: {gate.peak_active}")
    print(f"Configured maximum concurrent calls: {MAX_CONCURRENT_CALLS}")


if __name__ == "__main__":
    main()
