### Low Level Design

[![Directory docs](System-Design-and-Scaling/images/concurrency.drawio.png)](https://github.com/Sagor0078/System-Design-and-Scaling)

#### Correctness Issues

Correctness problems occur when shared state is corrupted because multiple threads access it simultaneously. The video identifies two main patterns:

- Check-Then-Act: You check a condition (e.g., "is seat 7A available?") and then act (e.g., "book it"). If another thread acts between your check and your action, a bug occurs.

- Read-Modify-Write: You read a value, change it, and write it back (e.g., count++). If two threads do this at once, an increment can be lost.

- Solutions: Use Locks (Mutex, Synchronized blocks) to make the operation atomic, or use Atomic Variables (like AtomicInteger in Java) for simple counters.

#### Coordination Issues 

Coordination is about how threads communicate and pass work to each other (e.g., an API thread handing an email task to a background worker).

- The Problem: How does a worker know when new work arrives without wasting CPU cycles by "spinning" in a loop? 

- The Solution: Use a Blocking Queue. This allows a worker thread to "sleep" when the queue is empty and wake up instantly when work is added.

- Back Pressure: Use a Bounded Blocking Queue (setting a max size). This prevents the system from running out of memory if work arrives faster than it can be processed.

####  Scarcity Issues

Scarcity involves limiting access to a finite number of resources (e.g., only 10 concurrent connections to an external API).

- Semaphores: Think of these as a bucket of permits. A thread must acquire a permit to act and release it when done.

- Resource Pools: For objects with state (like Database Connections), you can use a Blocking Queue to hold the objects. Threads "take" a connection and "put" it back when finished.

- Crucial Step: Always use a try-finally block to ensure the resource/permit is released even if an error occurs, preventing a system-wide "halt".


To solve any concurrency problem, ask:

- Is there shared state? Focus on Correctness (Locks/Atomics).
- Is work flowing between threads? Focus on Coordination (Blocking Queues).
- Is there a fixed limit on resources? Focus on Scarcity (Semaphores/Pools).