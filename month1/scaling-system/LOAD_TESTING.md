# Load Testing with Locust

This directory contains comprehensive load testing tools for the Scaling System using [Locust](https://locust.io/).

## Quick Start

### 1. Install Dependencies
```bash
# Install locust and other dev dependencies
uv sync --group dev
```

### 2. Start the System
```bash
# Start all services
docker-compose up -d

# Verify system is running
curl http://localhost:8080/gateway-health
```

### 3. Run Load Tests

#### Simple Script-Based Testing
```bash
# Make the script executable
chmod +x load_test.sh

# Quick basic test (60 seconds, 10 users)
./load_test.sh basic

# Stress test (5 minutes, 50 users)
./load_test.sh stress

# Cache performance test
./load_test.sh cache

# Run all tests
./load_test.sh all
```

#### Interactive Web UI
```bash
# Start Locust web interface
./load_test.sh interactive

# Then open http://localhost:8089 in your browser
```

#### Manual Locust Commands
```bash
# Basic load test
locust -f locustfile.py --host=http://localhost:8080 --users=10 --spawn-rate=2 --run-time=60s --headless

# With HTML report
locust -f locustfile.py --host=http://localhost:8080 --users=10 --spawn-rate=2 --run-time=60s --headless --html=report.html

# Interactive mode (web UI)
locust -f locustfile.py --host=http://localhost:8080
```

## Test Scenarios

### ScalingSystemUser (Default)
- **Purpose**: Normal user behavior simulation
- **Tasks**: CRUD operations, health checks, caching tests
- **Weight Distribution**:
  - List users: 20% (most common operation)
  - Create user: 15%
  - Get user: 12% 
  - App health checks: 10%
  - Update user: 8%
  - Gateway health: 5%
  - Cache tests: 3%
  - Delete user: 2%

### HighVolumeUser
- **Purpose**: High-frequency stress testing
- **Tasks**: Rapid reads and health checks
- **Wait Time**: 0.1-0.5 seconds (very fast)
- **Focus**: Cache performance and load balancing

### AdminUser
- **Purpose**: Administrative operations simulation
- **Tasks**: Bulk operations and system monitoring
- **Operations**: Bulk user creation, system overview checks

## Test Types

### 1. Basic Test (`./load_test.sh basic`)
- **Duration**: 60 seconds
- **Users**: 10
- **Spawn Rate**: 2 users/second
- **Purpose**: Validate basic functionality

### 2. Stress Test (`./load_test.sh stress`)
- **Duration**: 5 minutes
- **Users**: 50
- **Spawn Rate**: 5 users/second
- **Purpose**: Test system under sustained load

### 3. Cache Test (`./load_test.sh cache`)
- **Duration**: 2 minutes
- **Users**: 20 (HighVolumeUser class)
- **Spawn Rate**: 10 users/second
- **Purpose**: Validate Redis caching performance

### 4. Spike Test (`./load_test.sh spike`)
- **Pattern**: 1→50→1 users
- **Duration**: Variable (waves)
- **Purpose**: Test system resilience to traffic spikes

## Configuration Files

### locust.conf
Default configuration file with predefined profiles:
- `basic`: Light testing
- `stress`: Heavy sustained load
- `spike`: High burst traffic
- `cache`: Cache-focused testing

### locustfile.py
Python test definitions with three user classes and comprehensive task definitions.

## Reports and Monitoring

### Automatic Reports
All tests generate:
- **HTML Report**: Visual charts and statistics
- **CSV Files**: Raw data for analysis
- **Console Output**: Real-time statistics

### Report Location
```
load_test_reports/
├── basic_test_20240101_120000.html
├── stress_test_20240101_130000.html
├── cache_test_20240101_140000.html
├── *.csv (raw data)
└── locust.log
```

### Viewing Reports
```bash
# List available reports
./load_test.sh reports

# Open HTML report in browser
firefox load_test_reports/basic_test_*.html
```

## Performance Metrics

### Key Metrics to Monitor
1. **Response Time**: 95th percentile should be < 500ms
2. **Throughput**: Requests per second (RPS)
3. **Error Rate**: Should be < 1% under normal load
4. **Cache Hit Rate**: Monitor Redis performance
5. **Load Balancer Distribution**: Even traffic across app instances

### Success Criteria
- **Basic Test**: 0% error rate, < 200ms average response time
- **Stress Test**: < 1% error rate, < 500ms 95th percentile
- **Cache Test**: Visible cache hit improvement on repeated requests

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if system is running
   docker-compose ps
   curl http://localhost:8080/gateway-health
   ```

2. **High Error Rates**
   ```bash
   # Check application logs
   docker-compose logs app1 app2 app3
   ```

3. **Slow Performance**
   ```bash
   # Check Redis cache
   docker-compose exec redis redis-cli info
   
   # Check nginx load balancer
   docker-compose logs load-balancer
   ```

### Resource Requirements
- **Memory**: 2GB+ recommended for full stress tests
- **CPU**: Multi-core recommended for concurrent testing
- **Network**: Local testing preferred for consistent results

## Advanced Usage

### Custom Test Scenarios
Create custom user classes in `locustfile.py`:
```python
class CustomUser(HttpUser):
    wait_time = between(1, 2)
    
    @task
    def custom_task(self):
        # Your custom test logic
        pass
```

### Environment Variables
```bash
# Override default host
LOCUST_HOST=http://production.example.com ./load_test.sh basic

# Custom user count
LOCUST_USERS=100 ./load_test.sh stress
```

### Distributed Testing
```bash
# Master node
locust -f locustfile.py --master --host=http://localhost:8080

# Worker nodes (run on multiple machines)
locust -f locustfile.py --worker --master-host=<master-ip>
```

## Integration with CI/CD

Add to `.github/workflows/ci-cd.yml`:
```yaml
- name: Load Testing
  run: |
    docker-compose up -d
    sleep 10
    ./load_test.sh basic
    docker-compose down
```
