## Roadmap to Backend Scaling & System Design

This roadmap takes you from core fundamentals to advanced distributed systems, blending theory, hands-on projects, and real-world architecture patterns so you can confidently handle systems at any scale.

## Scaling & Architecture

| Topic                         | What It Is                                                                  | Key Skills                             | Resources                                                                                                                                |
| ----------------------------- | --------------------------------------------------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **CDN**                       | Content Delivery Network caches static assets geographically close to users | Cloudflare, Akamai, AWS CloudFront     | [Cloudflare Learning Center](https://www.cloudflare.com/learning/cdn/what-is-a-cdn/)                                                     |
| **Caching**                   | Store frequently accessed data in memory to reduce latency & load           | Redis, Memcached, HTTP caching headers | [Caching Strategies – AWS Docs](https://aws.amazon.com/caching/)                                                                         |
| **Sharding**                  | Splitting DB/data across multiple nodes based on a key                      | Range-based vs hash-based sharding     | [System Design Primer – Sharding](https://github.com/donnemartin/system-design-primer#sharding)                                          |
| **Queueing**                  | Asynchronous task processing                                                | RabbitMQ, Kafka, SQS, Celery           | [Message Queues Explained](https://www.cloudamqp.com/blog/part1-rabbitmq-for-beginners-what-is-rabbitmq.html)                            |
| **Replication**               | Copying data across servers for redundancy & scaling                        | Leader–Follower, Multi-Leader          | [Database Replication Patterns](https://www.geeksforgeeks.org/dbms/data-replication-in-dbms/)                                                     |
| **Partitioning**              | Splitting data logically or physically                                      | Horizontal vs Vertical partitioning    | [Partitioning – Microsoft Docs](https://learn.microsoft.com/en-us/azure/architecture/best-practices/data-partitioning)                   |
| **API Gateway**               | Single entry point for multiple services                                    | Kong, Nginx, AWS API Gateway           | [API Gateway Pattern – Microservices.io](https://microservices.io/patterns/apigateway.html)                                              |
| **Rate Limiting**             | Limit requests per user/IP                                                  | Token bucket, leaky bucket algorithms  | [Rate Limiting Algorithms](https://cloudflare.com/learning/bots/how-rate-limiting-works/)                                                |
| **CAP Theorem**               | Trade-off between Consistency, Availability, Partition Tolerance            | CP vs AP systems                       | [CAP Twelve Years Later – Brewer](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)           |
| **Microservices**             | Independent deployable services                                             | API communication, scaling, monitoring | [Microservices.io](https://microservices.io/)                                                                                            |
| **Load Balancing**            | Distribute traffic across servers                                           | Round robin, least connections         | [NGINX Load Balancing](https://www.nginx.com/resources/glossary/load-balancing/)                                                         |
| **Fault Tolerance**           | System keeps running despite failures                                       | Redundancy, retries                    | [AWS Well-Architected – Reliability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html)                                                         |
| **Database Scaling**          | Vertical vs horizontal scaling                                              | Read replicas, partitioning            | [Scaling Databases](https://www.digitalocean.com/resources/articles/horizontal-scaling-vs-vertical-scaling)                                     |
| **Service Discovery**         | Find services dynamically                                                   | Consul, Eureka                         | [Service Discovery Pattern](https://microservices.io/patterns/server-side-discovery.html)                                                |
| **Consistency Models**        | Strong, eventual, causal                                                    | [Jepsen analysis](https://jepsen.io/)  |                                                                                                                                          |
| **Eventual Consistency**      | Data converges over time                                                    | DynamoDB, Cassandra, ScyllaDB                    | [Amazon DynamoDB Eventual Consistency](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html) |
| **Distributed Transactions**  | Transactions across multiple systems                                        | Two-phase commit, Saga pattern         | [Distributed Transactions Patterns](https://microservices.io/patterns/data/saga.html)                                                    |
| **Monolith vs Microservices** | Trade-offs of single app vs many services                                   | Maintainability, complexity            | [Martin Fowler – MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html)                                                       |
| **Leader Election**           | Choosing a node as leader in a cluster                                      | Raft, Paxos, Zookeeper                 | [Raft Visualization](https://raft.github.io/)  



## Databases & Storage

| Topic                           | What It Is                                       | Key Skills                                                                                      | Resources                                                                           |
| ------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **Leader-Follower Replication** | One leader writes, followers replicate           | PostgreSQL streaming replication                                                                | [PostgreSQL Replication](https://www.postgresql.org/docs/current/warm-standby.html) |
| **WAL (Write Ahead Log)**       | Log before committing to disk for durability     | PostgreSQL WAL internals                                                                        | [WAL – PostgreSQL Docs](https://www.postgresql.org/docs/current/wal-intro.html)     |
| **Asynchronous Processing**     | Do work in background                            | Celery, Sidekiq                                                                                 | [Celery Docs](https://docs.celeryproject.org/en/stable/)                            |
| **Transaction Isolation**       | Levels: Read Uncommitted → Serializable          | [PostgreSQL Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)            |                                                                                     |
| **Read/Write Patterns**         | Optimize for read-heavy vs write-heavy workloads | [System Design Primer – Patterns](https://github.com/donnemartin/system-design-primer)          |                                                                                     |
| **Consistent Hashing**          | Distribute load/data evenly                      | [Consistent Hashing Explained](https://www.toptal.com/big-data/consistent-hashing)              |                                                                                     |
| **Redis/Memcached**             | In-memory key-value store                        | [Redis Docs](https://redis.io/docs/)                                                            |                                                                                     |
| **Backup & Restore**            | Point-in-time recovery                           | [PostgreSQL Backup](https://www.postgresql.org/docs/current/backup.html)                        |                                                                                     |
| **Hot/Cold Storage**            | Hot = fast, Cold = cheap                         | AWS S3, Glacier                                                                                 | [AWS Storage Classes](https://aws.amazon.com/s3/storage-classes/)                   |
| **Data Partitioning**           | Horizontal/vertical partitioning                 | [Azure – Data Partitioning Guidance](https://learn.microsoft.com/en-us/azure/architecture/best-practices/data-partitioning)                                                 |                                                                                     |
| **Object Storage**              | Blob storage like S3                             | [S3 Docs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)                   |                                                                                     |
| **SQL vs NoSQL**                | Relational vs document/columnar                  | [Comparison](https://www.mongodb.com/nosql-explained)                                           |                                                                                     |
| **Data Retention**              | Compliance, GDPR                                 | [Data Retention Guide](https://gdpr-info.eu/)                                                   |                                                                                     |
| **Data Modeling**               | ER diagrams, normalization                       | [Database Normalization & Normal Forms](https://www.geeksforgeeks.org/dbms/database-normalization-normal-forms/)                         |                                                                                     |
| **OLAP vs OLTP**                | Analytical vs transactional DBs                  | [OLAP vs OLTP](https://www.datastax.com/blog/olap-vs-oltp)                                      |                                                                                     |
| **ACID & BASE**                 | Transaction properties                           | [ACID vs BASE](https://neo4j.com/blog/graph-database/acid-vs-base-consistency-models-explained/)                          |                                                                                     |
| **Bloom Filters**               | Probabilistic membership check                   | [Bloom Filters Explained](https://llimllib.github.io/bloomfilter-tutorial/)                     |                                                                                     |
| **File Systems**                | Ext4, NTFS, ZFS                                  | [File System Concepts](https://en.wikipedia.org/wiki/File_system)                               |                                                                                     |
| **S3 Basics**                   | AWS object storage                               | [AWS S3 Getting Started](https://docs.aws.amazon.com/AmazonS3/latest/gsg/GetStartedWithS3.html) |                                                                                     |
| **B+ Trees**                    | DB indexing structure                            | [B+ Tree Tutorial](https://www.cs.usfca.edu/~galles/visualization/BPlusTree.html)               |                                                                                     |
| **Indexing**                    | Speed up queries                                 | [Database Indexing Guide](https://use-the-index-luke.com/)                                      |                                                                                     |


## Communication & APIs

| Topic                 | What It Is                                | Key Skills                                                                                                                               | Resources                                                    |
| --------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| **JWT**               | Token-based authentication                | [JWT.io](https://jwt.io/)                                                                                                                |                                                              |
| **CORS**              | Cross-origin requests security            | [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)                                                                       |                                                              |
| **OAuth**             | Auth delegation                           | [OAuth2 Simplified](https://aaronparecki.com/oauth-2-simplified/)                                                                        |                                                              |
| **Throttling**        | Limit traffic                             | Token bucket, leaky bucket                                                                                                               | [Rate Limiting Guide](https://stripe.com/blog/rate-limiters) |
| **Serialization**     | JSON, ProtoBuf                            | [Protocol Buffers Docs](https://developers.google.com/protocol-buffers)                                                                  |                                                              |
| **API Security**      | OWASP API Top 10                          | [OWASP API Security](https://owasp.org/API-Security/)                                                                                    |                                                              |
| **Long Polling**      | HTTP hold-open                            | [MDN Long Polling](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)                         |                                                              |
| **WebSockets**        | Full-duplex communication                 | [WebSockets Guide](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)                                                      |                                                              |
| **Idempotency**       | Same request multiple times → same result | [Idempotency Explained](https://stripe.com/blog/idempotency)                                                                             |                                                              |
| **Service Mesh**      | Istio, Linkerd                            | [Service Mesh Intro](https://istio.io/latest/about/service-mesh/)                                                                        |                                                              |
| **Retry Patterns**    | Exponential backoff                       | [Retry Best Practices](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)                                |                                                              |
| **REST vs gRPC**      | HTTP vs binary RPC                        | [gRPC Docs](https://grpc.io/docs/)                                                                                                       |                                                              |
| **API Versioning**    | URI, header-based                         | [API Versioning Strategies](https://cloud.google.com/blog/products/api-management/api-design-choosing-the-right-api-versioning-strategy) |                                                              |
| **Circuit Breaker**   | Stop cascading failures                   | [Netflix Hystrix](https://martinfowler.com/bliki/CircuitBreaker.html)                                                                    |                                                              |
| **Fan-out/Fan-in**    | Split & aggregate requests                | [Fan-out/Fan-in – Azure Durable Functions](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-cloud-backup)                                         |                                                              |
| **Message Queues**    | Kafka, RabbitMQ                           | [Kafka Guide](https://kafka.apache.org/)                                                                                                 |                                                              |
| **Dead Letter Queue** | Store failed messages                     | [DLQ in AWS SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)                 |                                                              |


## Reliability & Observability

| Topic                     | What It Is                       | Key Skills                                                                                                                 | Resources                                                                                     |
| ------------------------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **Metrics**               | Quantitative system data         | Prometheus, Grafana                                                                                                        | [Prometheus Docs](https://prometheus.io/)                                                     |
| **Alerting**              | Notify on issues                 | Alertmanager, PagerDuty                                                                                                    | [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/overview/)                   |
| **Failover**              | Switch to backup system          | DNS failover, DB failover                                                                                                  | [Failover Concepts](https://www.cloudflare.com/learning/cdn/glossary/failover/)               |
| **Logging**               | Centralized logs                 | ELK stack, Loki                                                                                                            | [Logging Best Practices](https://logz.io/learn/complete-guide-elk-stack/)                     |
| **Rollbacks**             | Revert deployment                | Git, Kubernetes                                                                                                            | [Deployment Strategies](https://martinfowler.com/bliki/BlueGreenDeployment.html)              |
| **Monitoring**            | Metrics + health checks          | [Monitoring 101](https://grafana.com/docs/grafana/latest/)                                                                 |                                                                                               |
| **Heartbeats**            | Service health signals           | [Heartbeat Patterns](https://en.wikipedia.org/wiki/Heartbeat_%28computing%29)                                              |                                                                                               |
| **Retry Logic**           | Retries with backoff             | [AWS Retry Best Practices](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)              |                                                                                               |
| **Autoscaling**           | Scale based on load              | Kubernetes HPA                                                                                                             | [K8s Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) |
| **SLO/SLI/SLA**           | Availability & performance goals | [Google SRE Book – Chapter 4](https://sre.google/sre-book/service-level-objectives/)                                       |                                                                                               |
| **Load Testing**          | Simulate high traffic            | k6, Locust                                                                                                                 | [Load Testing Guide](https://k6.io/docs/)                                                     |
| **Error Budgets**         | Allowable downtime               | [SRE Book – Embracing Risk](https://sre.google/sre-book/embracing-risk/)                                                     |                                                                                               |
| **Health Checks**         | Liveness/readiness probes        | [K8s Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) |                                                                                               |
| **Incident Response**     | Handling outages                 | PagerDuty, Statuspage                                                                                                      | [Incident Management Guide](https://www.atlassian.com/incident-management)                    |
| **Chaos Engineering**     | Break things intentionally       | Netflix Chaos Monkey                                                                                                       | [Principles of Chaos](https://principlesofchaos.org/)                                         |
| **Distributed Tracing**   | Trace requests across services   | OpenTelemetry, Jaeger                                                                                                      | [OpenTelemetry Docs](https://opentelemetry.io/)                                               |
| **Canary Deployments**    | Gradual rollout                  | [Deployment Strategies](https://martinfowler.com/bliki/CanaryRelease.html)                                                 |                                                                                               |
| **Graceful Degradation**  | Reduce features on failure       | [SRE Book – Handling Overload](https://sre.google/sre-book/handling-overload/)                               |                                                                                               |
| **Blue-Green Deployment** | Swap between two environments    | [Blue-Green Guide](https://martinfowler.com/bliki/BlueGreenDeployment.html)                                                |                                                                                               |

## **6-18** Module Backend Systems Design & Scaling Learning Plan

### Module 1 – Foundations & Core Concepts

Goal: Understand the building blocks of large-scale systems.

Topics
- Scaling basics → Vertical vs horizontal scaling
- CDN & Caching strategies → Browser cache, Redis/Memcached, HTTP caching headers
- Load Balancing → Round Robin, Least Connections, Consistent Hashing
- API Gateway basics → Routing, authentication, throttling
- Rate Limiting → Token Bucket, Leaky Bucket
- Monolith vs Microservices → When to split

Hands-On

- [Mini Project](https://github.com/Sagor0078/System-Design-and-Scaling/tree/main/Module1/scaling-system):
1. Build a simple FastAPI app with Redis caching and Nginx load balancing
2. Add an API Gateway (Kong or Nginx) in front of it
3. Implement rate limiting using Redis

Resources
- [System Design Primer](https://github.com/donnemartin/system-design-primer)
- [High Scalability Blog](http://highscalability.com/)
- [Cloudflare CDN Guide](https://www.cloudflare.com/learning/cdn/what-is-a-cdn/)

### Module 2 – Databases & Storage

Goal: Learn how to scale and structure data.

Topics
- SQL vs NoSQL – Trade-offs
- Indexing & B+ Trees
- Leader-Follower Replication & WAL
- Sharding & Partitioning
- Hot/Cold Storage
- Backup & Restore strategies
- ACID vs BASE & Consistency Models

Hands-On

- [Mini Project](https://github.com/Sagor0078/System-Design-and-Scaling/tree/main/Module2)

1. PostgreSQL with read replicas
2. Implement sharding manually (range/hash partitioning)
3. Add backup & restore scripts
4. Compare strong vs eventual consistency with MongoDB or Cassandra

Resources
- Designing Data-Intensive Applications (DDIA) – Chapters 1-5
- [PostgreSQL Replication Docs](https://www.postgresql.org/docs/current/warm-standby.html)
- [MongoDB Sharding Guide](https://www.mongodb.com/docs/manual/sharding/)

### Module 3 – Asynchronous Processing & Messaging

Goal: Master async patterns for scalability.

Topics

- Queueing – RabbitMQ, Kafka, AWS SQS
- Dead Letter Queues
- Fan-out/Fan-in patterns
- Retry Patterns & Circuit Breaker
- Long Polling vs WebSockets
- Service Mesh basics

Hands-On

- [Mini Project](https://github.com/Sagor0078/System-Design-and-Scaling/tree/main/Module3):

1. Event-driven order processing system
2. Producer → Queue → Consumer
3. DLQ for failed tasks
4. Retry with exponential backoff
5. WebSocket for real-time status updates

Resources

- [RabbitMQ Tutorial](https://www.rabbitmq.com/tutorials/tutorial-one-python.html)
- [Kafka Streams Guide](https://kafka.apache.org/documentation/streams/)
- [Service Mesh Intro – Istio](https://istio.io/latest/about/service-mesh/)

### Module 4 – Reliability, Observability & Fault Tolerance

Goal: Make systems resilient and debuggable.

Topics

- Fault Tolerance & Failover
- Distributed Tracing (OpenTelemetry, Jaeger)
- Metrics & Monitoring (Prometheus + Grafana)
- Alerting & Incident Response
- Health Checks & Graceful Degradation
- Chaos Engineering (Netflix Chaos Monkey)

Hands-On

- [Mini Project](https://github.com/Sagor0078/System-Design-and-Scaling/tree/main/Module4):

1. Deploy on Kubernetes (manifests in `Module4/resilient-service/k8s/`)
2. Add health checks, liveness/readiness probes
3. Implement autoscaling based on CPU/memory
4. Add Prometheus + Grafana dashboards
5. Simulate failures & verify fault tolerance

Resources

- [Google SRE Book – full table of contents](https://sre.google/sre-book/table-of-contents/)
  - [Ch. 3 Embracing Risk](https://sre.google/sre-book/embracing-risk/) · [Ch. 4 SLOs](https://sre.google/sre-book/service-level-objectives/) · [Ch. 21 Handling Overload](https://sre.google/sre-book/handling-overload/) · [Ch. 22 Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)
- [Google SRE Workbook](https://sre.google/workbook/table-of-contents/) – the practical companion
- [Prometheus Docs](https://prometheus.io/docs/introduction/overview/)
- [Chaos Engineering Principles](https://principlesofchaos.org/)
- [AWS Builders' Library – Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- [AWS Builders' Library – Implementing health checks](https://aws.amazon.com/builders-library/implementing-health-checks/)
- [Kubernetes – Liveness, readiness & startup probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Jaeger Docs](https://www.jaegertracing.io/docs/latest/) · [OpenTelemetry – Traces](https://opentelemetry.io/docs/concepts/signals/traces/)
- [Netflix Chaos Monkey](https://netflix.github.io/chaosmonkey/) · [Chaos Mesh](https://github.com/chaos-mesh/chaos-mesh) (Kubernetes-native)

### Module 5 – Advanced Distributed Systems

Goal: Handle complexity of multi-node systems.

Topics
- CAP Theorem deep dive
- Leader Election (Raft, Paxos)
- Distributed Transactions – 2PC, Saga Pattern
- Eventual Consistency
- Consistent Hashing
- Service Discovery (Consul, Eureka)

Hands-On

- Mini Project:

1. Build a distributed key-value store (in Go or Python)
2. Implement leader election with Raft
3. Support consistent hashing for partitioning
4. Add service discovery with Consul

Resources

- [Raft Visualization](https://raft.github.io/)
- Distributed Systems: Principles and Paradigms – Tanenbaum
- [Microservices.io Patterns](https://microservices.io/)

### Module 6 – Real-World Scale Architecture

Goal: Integrate all concepts into one large-scale system.

Topics
- API Security – JWT, OAuth, CORS, Idempotency
- Blue-Green & Canary Deployments
- Data Retention & Compliance
- OLAP vs OLTP optimization
- Graceful Rollbacks

Hands-On – Capstone Project

- High-scale e-commerce backend with:

1. API Gateway & microservices
2. PostgreSQL sharding + read replicas
3. Redis caching layer
4. Kafka-based async processing
5. Prometheus + Grafana monitoring
6. Kubernetes autoscaling
7. Canary deployment strategy
8. Disaster recovery & backup scripts

Resources

- [AWS Architecture Blog](https://aws.amazon.com/architecture/)
- [Netflix Tech Blog](https://netflixtechblog.com/)
- [Uber Engineering Blog](https://eng.uber.com/)


## Recommended resources

> All links below were last link-checked on 2026-11-06.

### Books

- [Designing Data-Intensive Applications](https://dataintensive.net/) – Kleppmann. The one book to read if you only read one ([O'Reilly edition](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/))
- [Google SRE Book](https://sre.google/sre-book/table-of-contents/) and [SRE Workbook](https://sre.google/workbook/table-of-contents/) – free online, full text

### Video channels

- [Jordan has no life](https://www.youtube.com/@jordanhasnolife5163) – DDIA chapter-by-chapter walkthroughs and deep system design breakdowns; the closest thing to a free distributed-systems course
- [Hello Interview](https://www.youtube.com/@hello_interview) – mock interviews and design walkthroughs from ex-FAANG interviewers; see also their written [System Design in a Hurry](https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction) guide
- [ByteByteGo](https://www.youtube.com/@ByteByteGo) – short animated explainers; good for first contact with a concept
- [Gaurav Sen](https://www.youtube.com/@gkcs) – component-level reasoning, strong on trade-offs
- [System Design Interview](https://www.youtube.com/@SystemDesignInterview) – long, careful end-to-end designs
- [InfoQ](https://www.youtube.com/@InfoQ) – real production war stories from conference talks

### Practice & reference

- [System Design Primer](https://github.com/donnemartin/system-design-primer) – the canonical starting repo
- [System Design 101](https://github.com/ByteByteGoHq/system-design-101) – diagram-first reference
- [Awesome Scalability](https://github.com/binhnguyennus/awesome-scalability) – curated real-world architecture write-ups
- [Patterns of Distributed Systems](https://martinfowler.com/articles/patterns-of-distributed-systems/) – Fowler/Joshi, pattern catalogue with code
- [How to build distributed systems](https://builddistributedsystem.com/)
- [Iximiuz Labs – DevOps](https://labs.iximiuz.com/) – browser-based hands-on labs
- [MIT 6.824 Distributed Systems](https://pdos.csail.mit.edu/6.824/) – lectures, labs and the classic paper list

### Engineering blogs

- [Netflix Tech Blog](https://netflixtechblog.com/) · [Uber Engineering](https://eng.uber.com/) · [Meta Engineering](https://engineering.fb.com/)
- [All Things Distributed](https://www.allthingsdistributed.com/) – Werner Vogels
- [AWS Builders' Library](https://aws.amazon.com/builders-library/) – how AWS actually builds for reliability
- [High Scalability](https://highscalability.com/) · [Arpit Bhayani](https://arpitbhayani.me/blogs) · [System Design One](https://systemdesign.one/)