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


## Platform & Infrastructure — Production Operations

The stack this repository's infrastructure actually runs on: managed Kubernetes,
Helm + Kustomize, Terraform/OpenTofu, Vault for secrets, Argo CD for GitOps, and
a service mesh. Everything below is operational guidance — how to run these in
production — rather than getting-started material. All links verified 2026-11-06.

### Kubernetes — running it, not just using it

| Topic | Why it matters in production | Resource |
| ----- | ---------------------------- | -------- |
| **Production checklist** | The single best audit of what a real cluster needs before traffic hits it | [learnk8s Production Best Practices](https://learnk8s.io/production-best-practices) |
| **Requests & limits** | Wrong requests break the HPA and the scheduler silently; limits cause OOMKills and CPU throttling | [Managing Resources for Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) |
| **Probes** | Liveness that checks dependencies turns a dependency outage into a cluster-wide restart loop (see `Module4/`) | [Liveness, Readiness & Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) |
| **Disruption budgets** | Without a PDB, a node drain can take every replica at once | [Disruptions & PDBs](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) |
| **Priority & preemption** | Decides who dies when a node fills up — set it before you need it | [Pod Priority & Preemption](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/) |
| **Graceful node shutdown** | Nodes that disappear without draining drop in-flight requests | [Node Shutdown](https://kubernetes.io/docs/concepts/cluster-administration/node-shutdown/) |
| **RBAC** | Least privilege for humans and service accounts; the default is more open than you think | [RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) |
| **Pod Security Standards** | Replaced PodSecurityPolicy; baseline/restricted profiles per namespace | [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) |
| **Policy as code** | Enforce "no `:latest`", required labels, resource limits at admission time | [Kyverno](https://kyverno.io/docs/) · [OPA Gatekeeper](https://open-policy-agent.github.io/gatekeeper/website/docs/) |
| **CIS benchmarking** | Scores your cluster against the CIS Kubernetes Benchmark | [kube-bench](https://github.com/aquasecurity/kube-bench) |
| **etcd backup & restore** | etcd *is* your cluster; practise the restore before you need it | [Operating etcd](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/) |
| **Cluster & volume backup** | Namespace-level backup/restore and migration | [Velero](https://velero.io/docs/) |
| **Autoscaling** | HPA for pods, Cluster Autoscaler or Karpenter for nodes | [HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) · [Autoscaler](https://github.com/kubernetes/autoscaler) · [Karpenter](https://karpenter.sh/) |
| **Metrics & debugging** | Which cluster metrics exist, and how to debug a cluster rather than a pod | [System Metrics](https://kubernetes.io/docs/concepts/cluster-administration/system-metrics/) · [Debug Clusters](https://kubernetes.io/docs/tasks/debug/debug-cluster/) |
| **Monitoring stack** | The standard operator-based Prometheus/Grafana install | [kube-prometheus](https://github.com/prometheus-operator/kube-prometheus) · [Prometheus Operator](https://prometheus-operator.dev/docs/getting-started/introduction/) |
| **Ingress, successor to** | Gateway API is where ingress is heading; worth planning for | [Gateway API](https://gateway-api.sigs.k8s.io/) |
| **TLS automation** | Certificate issuance and renewal in-cluster | [cert-manager](https://cert-manager.io/docs/) |
| **Learn the internals** | Build a cluster by hand once and nothing is a black box afterwards | [Kubernetes the Hard Way](https://github.com/kelseyhightower/kubernetes-the-hard-way) |
| **Learn from outages** | A catalogue of real Kubernetes failure post-mortems | [k8s.af](https://k8s.af/) |
| **Reference** | The docs worth reading cover to cover, plus the cheat sheet | [Concepts](https://kubernetes.io/docs/concepts/) · [kubectl Quick Reference](https://kubernetes.io/docs/reference/kubectl/quick-reference/) |

### Managed Kubernetes — the identity bridge

Workload identity is the piece that makes Vault, external-secrets and cloud APIs
work without long-lived credentials in a Secret. Get this right first.

| Platform | Resource |
| -------- | -------- |
| **EKS** | [EKS Best Practices Guides](https://aws.github.io/aws-eks-best-practices/) · [IAM Roles for Service Accounts](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) · [EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html) (the newer, simpler mechanism) |
| **GKE** | [Workload Identity Federation](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) · [Hardening your cluster](https://cloud.google.com/kubernetes-engine/docs/how-to/hardening-your-cluster) |
| **AKS** | [Workload Identity](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview) · [AKS Baseline Architecture](https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/containers/aks/baseline-aks) |

### HashiCorp Vault

| Topic | Why it matters in production | Resource |
| ----- | ---------------------------- | -------- |
| **Production hardening** | The checklist: audit devices, TLS, no root tokens in CI, policy scoping | [Production Hardening](https://developer.hashicorp.com/vault/tutorials/operations/production-hardening) |
| **Kubernetes auth** | Pods authenticate with their ServiceAccount token — no bootstrap secret to leak | [Kubernetes Auth Method](https://developer.hashicorp.com/vault/docs/auth/kubernetes) |
| **Getting secrets into pods** | Three approaches with real trade-offs: sidecar injection, a CRD-driven operator, or CSI volumes | [Agent Injector](https://developer.hashicorp.com/vault/docs/platform/k8s/injector) · [Vault Secrets Operator](https://developer.hashicorp.com/vault/docs/platform/k8s/vso) · [CSI Provider](https://developer.hashicorp.com/vault/docs/platform/k8s/csi) |
| **Dynamic database credentials** | Per-pod, short-lived DB users instead of one shared password — the biggest single win Vault offers | [Database Secrets Engine](https://developer.hashicorp.com/vault/docs/secrets/databases) |
| **Encryption as a service** | Encrypt application data without the app ever holding a key | [Transit Secrets Engine](https://developer.hashicorp.com/vault/docs/secrets/transit) |
| **HA & storage** | Raft integrated storage, quorum, and what a lost node actually costs | [Integrated Storage](https://developer.hashicorp.com/vault/docs/concepts/integrated-storage) |
| **Seal & auto-unseal** | A restarted Vault is a sealed Vault; plan unsealing before your first 3am restart | [Seal/Unseal Concepts](https://developer.hashicorp.com/vault/docs/concepts/seal) |
| **Deployment** | The official chart, and the values that matter for HA | [vault-helm](https://github.com/hashicorp/vault-helm) |
| **Multi-backend alternative** | Sync secrets from Vault *or* cloud secret managers into Kubernetes Secrets | [External Secrets Operator](https://external-secrets.io/latest/) |
| **Reference** | The full docs, worth skimming the concepts section end to end | [Vault Documentation](https://developer.hashicorp.com/vault/docs) |

### Argo CD & GitOps

| Topic | Why it matters in production | Resource |
| ----- | ---------------------------- | -------- |
| **GitOps principles** | The four principles worth agreeing on as a team before arguing about tools | [OpenGitOps](https://opengitops.dev/) |
| **Best practices** | Separate config repo from source, pin versions, avoid the manifest-drift traps | [Argo CD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/) |
| **App of apps** | Bootstrapping a whole cluster from one root Application | [Cluster Bootstrapping](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/) |
| **ApplicationSets** | One template across many clusters/environments instead of copy-pasted Applications | [ApplicationSet](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/) |
| **Sync waves & hooks** | Ordering: CRDs before the controllers that use them, migrations before rollout | [Sync Phases & Waves](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/) |
| **Secrets in GitOps** | The hard part of GitOps; options and their trade-offs | [Secret Management](https://argo-cd.readthedocs.io/en/stable/operator-manual/secret-management/) · [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) |
| **HA & disaster recovery** | Argo CD is itself a production service; back up its state | [High Availability](https://argo-cd.readthedocs.io/en/stable/operator-manual/high_availability/) · [Disaster Recovery](https://argo-cd.readthedocs.io/en/stable/operator-manual/disaster_recovery/) |
| **RBAC** | Who can sync what, per project — the control that makes shared clusters safe | [Argo CD RBAC](https://argo-cd.readthedocs.io/en/stable/operator-manual/rbac/) |
| **Progressive delivery** | Canary and blue-green with automated metric analysis and rollback | [Argo Rollouts](https://argo-rollouts.readthedocs.io/en/stable/) · [Flagger](https://flagger.app/) |
| **Reference** | The operator manual is the half that matters once you run it | [Argo CD Documentation](https://argo-cd.readthedocs.io/en/stable/) |

### Helm & Kustomize

| Topic | Why it matters in production | Resource |
| ----- | ---------------------------- | -------- |
| **Chart best practices** | Values naming, labels, and the conventions that keep charts upgradable | [Helm Chart Best Practices](https://helm.sh/docs/chart_best_practices/) |
| **Library charts** | Share boilerplate across services without copy-pasting templates | [Library Charts](https://helm.sh/docs/topics/library_charts/) |
| **Chart CI** | Lint and install-test charts on every PR | [chart-testing](https://github.com/helm/chart-testing) |
| **Seeing what will change** | A real diff before an upgrade, which `helm upgrade` alone does not give you | [helm-diff](https://github.com/databus23/helm-diff) |
| **Kustomize overlays** | Per-environment patches with no templating language at all | [Kustomize Guides](https://kubectl.docs.kubernetes.io/guides/) · [Kustomize Reference](https://kubectl.docs.kubernetes.io/references/kustomize/) |
| **Reference** | Template function and values reference | [Helm Documentation](https://helm.sh/docs/) |

### Terraform / OpenTofu

| Topic | Why it matters in production | Resource |
| ----- | ---------------------------- | -------- |
| **Style & structure** | The official conventions, now that there is an official style guide | [Terraform Style Guide](https://developer.hashicorp.com/terraform/language/style) |
| **Module design** | Composable modules with clear inputs/outputs beat one giant root module | [Developing Modules](https://developer.hashicorp.com/terraform/language/modules/develop) |
| **Remote state** | Locking and shared state; the first thing to fix after a `terraform.tfstate` in Git | [Remote State](https://developer.hashicorp.com/terraform/language/state/remote) |
| **Secrets in state** | State files contain plaintext secrets — treat them as secrets | [Sensitive Data in State](https://developer.hashicorp.com/terraform/language/state/sensitive-data) |
| **Team workflow** | PR-driven plan/apply with an audit trail, and DRY multi-environment layouts | [Atlantis](https://www.runatlantis.io/) · [Terragrunt](https://terragrunt.gruntwork.io/docs/) |
| **Cloud guidance** | Google's practical best-practice guide applies well beyond GCP | [Best Practices for Terraform](https://cloud.google.com/docs/terraform/best-practices-for-terraform) |
| **Security scanning** | Catch public buckets and open security groups in CI, not in production | [Checkov](https://www.checkov.io/) · [Trivy](https://github.com/aquasecurity/trivy) |
| **Cluster & Vault provisioning** | Battle-tested module, and managing Vault policies as code | [terraform-aws-eks](https://github.com/terraform-aws-modules/terraform-aws-eks) · [Vault Provider](https://registry.terraform.io/providers/hashicorp/vault/latest/docs) |
| **Reference** | Language and CLI reference for both forks | [Terraform Docs](https://developer.hashicorp.com/terraform/docs) · [OpenTofu Docs](https://opentofu.org/docs/) |

### Service Mesh (Istio / Linkerd)

| Topic | Why it matters in production | Resource |
| ----- | ---------------------------- | -------- |
| **Operational best practices** | Istio's own list of what breaks in real deployments | [Istio Ops Best Practices](https://istio.io/latest/docs/ops/best-practices/) |
| **mTLS rollout** | Migrating to strict mTLS without an outage in the middle | [mTLS Migration](https://istio.io/latest/docs/tasks/security/authentication/mtls-migration/) |
| **Traffic management** | The model behind retries, timeouts, outlier detection and mirroring | [Traffic Management Concepts](https://istio.io/latest/docs/concepts/traffic-management/) |
| **Canary releases** | Weighted traffic shifting, the mesh-level counterpart to Argo Rollouts | [Traffic Shifting](https://istio.io/latest/docs/tasks/traffic-management/traffic-shifting/) |
| **Sidecar-free mesh** | Ambient mode removes the per-pod sidecar tax; relevant if sidecar cost bites | [Istio Ambient](https://istio.io/latest/docs/ambient/) |
| **Lighter alternative** | Linkerd trades features for far less operational surface | [Linkerd Docs](https://linkerd.io/docs/) · [Linkerd Tasks](https://linkerd.io/2.18/tasks/) |
| **Reference** | Tasks and reference docs, versioned per release | [Istio Documentation](https://istio.io/latest/docs/) |

### Platform practice

- [The Twelve-Factor App](https://12factor.net/) — still the baseline contract between app and platform
- [Google SRE Workbook](https://sre.google/workbook/table-of-contents/) — SLOs, alerting on burn rate, and on-call that works
- [CNCF Landscape](https://landscape.cncf.io/) — when you need to know what else exists in a category
- [CNCF Reports](https://www.cncf.io/reports/) — adoption data, useful for justifying a tool choice

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