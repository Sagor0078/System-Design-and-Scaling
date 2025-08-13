# System Design Basics

A concise guide to essential system design concepts for scalable and high-performance applications.

---

## Topics

1. [Scaling Basics](#1-scaling-basics--vertical-vs-horizontal-scaling)
2. [CDN & Caching Strategies](#2-cdn--caching-strategies--browser-cache-redismemcached-http-caching-headers)
3. [Load Balancing](#3-load-balancing--round-robin-least-connections-consistent-hashing)
4. [API Gateway Basics](#4-api-gateway-basics--routing-authentication-throttling)
5. [Rate Limiting](#5-rate-limiting--token-bucket-leaky-bucket)
6. [Monolith vs Microservices](#6-monolith-vs-microservices--when-to-split)

---

## 1. Scaling Basics → Vertical vs Horizontal Scaling

**Scaling** means increasing your system's capacity to handle more load.

| Feature           | Vertical Scaling (Scale Up)         | Horizontal Scaling (Scale Out)      |
|-------------------|-------------------------------------|--------------------------------------|
| **Definition**    | Add more power (CPU/RAM) to a single machine | Add more machines/instances |
| **Complexity**    | Simple                              | More complex (distributed)           |
| **Limit**         | Hardware limits                     | Virtually unlimited                   |
| **Fault Tolerance**| Low                                 | High                                  |

---

## 2. CDN & Caching Strategies → Browser Cache, Redis/Memcached, HTTP Caching Headers

**CDN (Content Delivery Network)**: Delivers cached content from edge servers close to the user.  
**Caching layers**:
- **Browser Cache** → Stores static assets locally, controlled by `Cache-Control`, `Expires`, `ETag`.
- **Server Cache** (Redis/Memcached) → Stores frequently accessed data in-memory.
- **HTTP Headers**:
  - `Cache-Control`: Max-age, no-cache, no-store
  - `ETag`: Content fingerprint
  - `Last-Modified`: Timestamp for resource changes

---

## 3. Load Balancing → Round Robin, Least Connections, Consistent Hashing

**Load Balancing** distributes requests across servers.

- **Round Robin** → Sends requests in a fixed rotation.
- **Least Connections** → Chooses server with fewest active connections.
- **Consistent Hashing** → Routes based on hash of client/data for session stickiness or caching.

---

## 4. API Gateway Basics → Routing, Authentication, Throttling

**API Gateway** = Single entry point to backend services.

- **Routing** → Path-based, host-based, or version-based request forwarding.
- **Authentication** → API keys, JWT, OAuth2, mTLS.
- **Throttling** → Limit requests (fixed window, sliding window, token bucket, leaky bucket).

---

## 5. Rate Limiting → Token Bucket, Leaky Bucket

- **Token Bucket** → Tokens refill at a fixed rate; requests need tokens (allows bursts).
- **Leaky Bucket** → Requests processed at a fixed rate; excess dropped or queued.

| Feature       | Token Bucket         | Leaky Bucket        |
|---------------|----------------------|---------------------|
| Output Rate   | Bursty allowed       | Smooth/constant     |
| Best For      | APIs with bursts     | Traffic shaping     |

---

## 6. Monolith vs Microservices → When to Split

- **Monolith** → Single deployable unit; simple but less flexible at scale.
- **Microservices** → Independent services; scalable but complex.

**When to Split:**
- Scaling bottlenecks in certain modules
- Multiple teams causing code conflicts
- Need for tech diversity per component
- Desire for fault isolation

**Rule of Thumb:**  
> Start monolithic for speed. Split only when the **cost of staying monolithic > cost of going distributed**.

---
