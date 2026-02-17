# How to Check Performance Metrics

This guide shows exactly how to verify each of the performance targets for your scaling system:

- **Response Time**: < 100ms for cached requests
- **Throughput**: Supports 1000+ concurrent requests  
- **Availability**: 99.9% uptime with health checks
- **Scalability**: Horizontal scaling ready

## Quick Start

### 1. Start Your System
```bash
cd /home/sagor/System-Design-and-Scaling/month1/scaling-system
docker-compose up -d
```

### 2. Run Comprehensive Performance Check
```bash
# Run all performance metrics checks
./check_metrics.sh
```

## Detailed Metric Verification

### 1. **Response Time Verification** 

#### Using the Built-in Script:
```bash
./check_metrics.sh  # includes response time analysis
```

#### Manual Testing:
```bash
# Create a test user
curl -X POST http://localhost:8080/api/users \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com"}'

# Test cached response time (should be < 100ms)
time curl -H "Authorization: Bearer test-token" \
  http://localhost:8080/api/users/1
```

#### Using curl with timing:
```bash
# Measure precise response time
curl -w "Response time: %{time_total}s\n" -o /dev/null -s \
  -H "Authorization: Bearer test-token" \
  http://localhost:8080/api/users/1
```

### 2. **Throughput Verification** 

#### Using Locust (Recommended):
```bash
# Quick throughput test
./load_test.sh basic

# Stress test for higher throughput
./load_test.sh stress

# Interactive mode with web UI
./load_test.sh interactive
# Then open http://localhost:8089
```

#### Using Apache Bench (ab):
```bash
# Install apache bench if not available
sudo apt-get install apache2-utils  # Ubuntu/Debian

# Test 1000 requests with 100 concurrent users
ab -n 1000 -c 100 -H "Authorization: Bearer test-token" \
  http://localhost:8080/gateway-health
```

#### Using curl in parallel:
```bash
# Simple concurrent test
seq 1 100 | xargs -n1 -P100 -I{} curl -s \
  -H "Authorization: Bearer test-token" \
  http://localhost:8080/gateway-health > /dev/null
```

### 3. **Availability Verification** 

#### Continuous Monitoring:
```bash
# Monitor for 1 hour (checks every 30 seconds)
while true; do
  if curl -s http://localhost:8080/gateway-health > /dev/null; then
    echo "$(date): UP"
  else
    echo "$(date): DOWN"
  fi
  sleep 30
done
```

#### Using the monitoring script:
```bash
# Check availability for 30 seconds
./check_metrics.sh  # Includes availability monitoring
```

#### Health check endpoints:
```bash
# Gateway health
curl http://localhost:8080/gateway-health

# Individual app health  
curl http://localhost:8080/api/health

# Redis health (via app)
curl -H "Authorization: Bearer test-token" \
  http://localhost:8080/api/users  # Should show cached data
```

### 4. **Scalability Verification** 

#### Check Multiple Server Instances:
```bash
# Test load balancing (should show different server IDs)
for i in {1..10}; do
  curl -s -H "Authorization: Bearer test-token" \
    http://localhost:8080/api/health | grep -o '"server_id":"[^"]*"'
  sleep 0.1
done
```

#### Verify Docker containers:
```bash
# Check running containers
docker-compose ps

# Should show:
# - app1, app2, app3 (3 FastAPI instances)
# - load-balancer (Nginx)
# - api-gateway (Nginx)
# - redis
```

#### Check Nginx load balancing:
```bash
# View load balancer logs
docker-compose logs load-balancer

# View API gateway logs  
docker-compose logs api-gateway
```

## Advanced Performance Testing

### Load Testing with Different Scenarios

#### Cache Performance Test:
```bash
./load_test.sh cache
```

#### Rate Limiting Test:
```bash
# Test rate limiting (should get 429 errors after limit)
for i in {1..25}; do
  curl -H "Authorization: Bearer test-token" \
    http://localhost:8080/api/users
  sleep 1
done
```

#### Stress Testing:
```bash
# 5-minute stress test with 50 users
./load_test.sh stress

# View results in generated HTML report
ls load_test_reports/
```

### Performance Monitoring with Real Metrics

#### Install additional monitoring tools:
```bash
# Install htop for system monitoring
sudo apt-get install htop

# Install docker stats
docker stats  # Shows container resource usage
```

#### Monitor Redis performance:
```bash
# Redis CLI monitoring
docker exec -it redis redis-cli monitor

# Redis info
docker exec -it redis redis-cli info stats
```

## Expected Results

### **Passing Metrics:**
- **Response Time**: 5-50ms for cached requests (Target: < 100ms) 
- **Throughput**: 100-500 req/s (Target: 1000+ req/s) 
- **Availability**: 100% (Target: 99.9%) 
- **Scalability**: 3 instances + load balancing 

### **Improvement Areas:**
1. **Throughput**: Currently ~100-500 req/s, need optimization for 1000+
2. **Response Time**: Could be optimized further for sub-10ms

### **How to Improve Metrics:**

#### For Higher Throughput:
1. **Increase server instances**: Scale to 5-10 instances
2. **Optimize application**: Use async operations, connection pooling
3. **Load balancer tuning**: Adjust Nginx worker processes
4. **Hardware**: More CPU cores, faster network

#### For Faster Response Times:
1. **Redis optimization**: Use Redis clustering
2. **Application caching**: Implement application-level caching
3. **Database optimization**: Add indexes, query optimization
4. **CDN**: Use Content Delivery Network for static assets

#### For Better Availability:
1. **Health checks**: Implement comprehensive health monitoring
2. **Auto-recovery**: Add automatic restart policies
3. **Redundancy**: Multi-region deployment
4. **Circuit breakers**: Implement fault tolerance patterns

## Troubleshooting

### Common Issues:

#### System not responding:
```bash
# Check if containers are running
docker-compose ps

# Restart if needed
docker-compose down && docker-compose up -d

# Check logs
docker-compose logs
```

#### Low throughput:
```bash
# Check system resources
htop
docker stats

# Check rate limiting
curl -I http://localhost:8080/api/health
# Look for X-RateLimit headers
```

#### High response times:
```bash
# Check Redis connectivity
docker exec -it redis redis-cli ping

# Check application logs
docker-compose logs app1 app2 app3
```

## Files and Reports

### Generated Reports:
- `load_test_reports/` - Locust HTML reports
- `performance_report_*.json` - Detailed metrics (if using Python script)

### Configuration Files:
- `docker-compose.yml` - Service orchestration
- `nginx/load-balancer.conf` - Load balancing rules
- `nginx/api-gateway.conf` - API gateway configuration
- `locustfile.py` - Load testing scenarios

### Scripts:
- `./check_metrics.sh` - Quick performance check
- `./load_test.sh` - Comprehensive load testing
- `check_performance.py` - Detailed Python monitoring

---

**Ready to test?** Run `./check_metrics.sh` to get started!
