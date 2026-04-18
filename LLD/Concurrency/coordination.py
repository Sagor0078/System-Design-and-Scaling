"""Coordination example: producers and workers using a bounded blocking queue.

Run:
    python coordination_example.py
"""

from __future__ import annotations

import queue
import random
import threading
import time


NUM_PRODUCERS = 2
NUM_WORKERS = 3
TASKS_PER_PRODUCER = 8
QUEUE_MAXSIZE = 5


def producer(name: str, work_queue: queue.Queue[str]) -> None:
    for i in range(1, TASKS_PER_PRODUCER + 1):
        task = f"{name}-task-{i}"
        # Blocks if queue is full: this is natural back pressure.
        work_queue.put(task)
        print(f"{name} queued {task} (size={work_queue.qsize()})")
        time.sleep(random.uniform(0.02, 0.08))


def worker(name: str, work_queue: queue.Queue[str | None]) -> None:
    while True:
        # Blocks when queue is empty; no CPU-wasting spin loop.
        task = work_queue.get()

        if task is None:
            work_queue.task_done()
            print(f"{name} received stop signal")
            return

        print(f"{name} processing {task}")
        time.sleep(random.uniform(0.05, 0.12))
        print(f"{name} finished {task}")
        work_queue.task_done()


def main() -> None:
    work_queue: queue.Queue[str | None] = queue.Queue(maxsize=QUEUE_MAXSIZE)

    workers = [
        threading.Thread(target=worker, args=(f"worker-{i}", work_queue), daemon=True)
        for i in range(1, NUM_WORKERS + 1)
    ]
    for thread in workers:
        thread.start()

    producers = [
        threading.Thread(target=producer, args=(f"producer-{i}", work_queue), daemon=True)
        for i in range(1, NUM_PRODUCERS + 1)
    ]
    for thread in producers:
        thread.start()

    for thread in producers:
        thread.join()

    # Wait until all produced tasks are fully processed.
    work_queue.join()

    # Send one sentinel per worker for clean shutdown.
    for _ in workers:
        work_queue.put(None)

    work_queue.join()
    for thread in workers:
        thread.join()

    print("All work completed cleanly.")


if __name__ == "__main__":
    main()
