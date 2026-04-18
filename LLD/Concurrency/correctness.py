"""Correctness example: race conditions vs lock-protected logic.

Run:
    python correctness_example.py
"""

from __future__ import annotations

import threading
import time


class Counter:
    """Shared counter with unsafe and safe increment methods."""

    def __init__(self) -> None:
        self.value = 0
        self._lock = threading.Lock()

    def increment_unsafe(self) -> None:
        # Intentionally split read/modify/write to make the race obvious.
        current = self.value
        time.sleep(0.0001)
        self.value = current + 1

    def increment_safe(self) -> None:
        with self._lock:
            current = self.value
            time.sleep(0.0001)
            self.value = current + 1


class SeatBooking:
    """Single seat inventory to demonstrate check-then-act races."""

    def __init__(self) -> None:
        self.owner: str | None = None
        self._lock = threading.Lock()

    def book_unsafe(self, user: str) -> bool:
        if self.owner is None:
            time.sleep(0.001)
            self.owner = user
            return True
        return False

    def book_safe(self, user: str) -> bool:
        with self._lock:
            if self.owner is None:
                time.sleep(0.001)
                self.owner = user
                return True
            return False


def run_counter_demo() -> None:
    expected = 20 * 200
    counter = Counter()

    threads = [
        threading.Thread(target=lambda: [counter.increment_unsafe() for _ in range(200)])
        for _ in range(20)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("Counter (unsafe)")
    print(f"expected={expected}, actual={counter.value}")

    counter.value = 0
    threads = [
        threading.Thread(target=lambda: [counter.increment_safe() for _ in range(200)])
        for _ in range(20)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("Counter (safe)")
    print(f"expected={expected}, actual={counter.value}")


def run_booking_demo() -> None:
    booking = SeatBooking()
    unsafe_results: list[tuple[str, bool]] = []

    def try_unsafe(user: str) -> None:
        unsafe_results.append((user, booking.book_unsafe(user)))

    t1 = threading.Thread(target=try_unsafe, args=("alice",))
    t2 = threading.Thread(target=try_unsafe, args=("bob",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print("\nBooking (unsafe)")
    print(f"results={unsafe_results}, final_owner={booking.owner}")

    booking = SeatBooking()
    safe_results: list[tuple[str, bool]] = []

    def try_safe(user: str) -> None:
        safe_results.append((user, booking.book_safe(user)))

    t3 = threading.Thread(target=try_safe, args=("alice",))
    t4 = threading.Thread(target=try_safe, args=("bob",))
    t3.start()
    t4.start()
    t3.join()
    t4.join()

    print("Booking (safe)")
    print(f"results={safe_results}, final_owner={booking.owner}")


if __name__ == "__main__":
    run_counter_demo()
    run_booking_demo()
