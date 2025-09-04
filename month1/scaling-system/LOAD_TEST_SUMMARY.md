# Load Testing Summary

## Load Testing Implementation Complete!

FastAPI scaling system now has comprehensive load testing capabilities using **Locust**.

## Files Created

### Core Load Testing Files
- **`locustfile.py`** - Main test scenarios (3 user classes, 15+ test scenarios)
- **`load_test.sh`** - Automated testing script with multiple test modes
- **`locust.conf`** - Locust configuration with predefined profiles
- **`LOAD_TESTING.md`** - Comprehensive documentation

### Updated Files
- **`pyproject.toml`** - Added locust>=2.31.8 to dev dependencies
- **`Makefile`** - Added load testing commands

## Quick Start

### 1. Install Dependencies
```bash
uv sync --group dev
```

### 2. Start the System
```bash
docker-compose up -d
```

### 3. Run Load Tests
```bash
# quick basic test (60 seconds, 10 users)
./load_test.sh basic

# interactive web UI
./load_test.sh interactive
# Then open: http://localhost:8089
```

## Available Test Scenarios

### 1. ScalingSystemUser (Primary)
**Simulates normal user behavior**
- CRUD operations on users
- Health checks across all services
- Cache performance testing
- Load balancer validation

### 2. HighVolumeUser 
**High-frequency stress testing**
- Rapid read operations (0.1-0.5s intervals)
- Cache hit rate optimization
- Load balancing effectiveness

### 3. AdminUser
**Administrative operations**
- Bulk user creation/reading
- System monitoring scenarios
- Administrative workflows

## Test Modes

| Command | Duration | Users | Purpose |
|---------|----------|-------|---------|
| `./load_test.sh basic` | 60s | 10 | Quick validation |
| `./load_test.sh stress` | 5min | 50 | Sustained load |
| `./load_test.sh cache` | 2min | 20 | Cache performance |
| `./load_test.sh spike` | Variable | 1→50→1 | Traffic spikes |
| `./load_test.sh all` | ~8min | Mixed | Full test suite |

## What Gets Tested

### Performance Metrics
- Response times (average, 95th percentile)
- Throughput (requests per second)
- Error rates under load
- Cache hit/miss ratios
- Load balancer distribution

### System Components
- Nginx API Gateway (`/gateway-health`)
- Nginx Load Balancer (traffic distribution)
- FastAPI App Instances (`/app1/health`, `/app2/health`, `/app3/health`)
- Redis Caching (repeat request performance)
- User API endpoints (CRUD operations)

## Success Criteria

### Basic Test Targets
-  **Response Time**: < 200ms average
-  **Error Rate**: 0%
-  **Cache**: Visible improvement on repeated requests

### Stress Test Targets  
-  **Response Time**: < 500ms (95th percentile)
-  **Error Rate**: < 1%
-  **Load Balance**: Even distribution across app instances

##  Usage Examples

### Command Line Testing
```bash
# basic test with custom parameters
locust -f locustfile.py --host=http://localhost:8080 --users=10 --spawn-rate=2 --run-time=60s --headless

# generate HTML report
locust -f locustfile.py --host=http://localhost:8080 --users=20 --spawn-rate=5 --run-time=120s --headless --html=my_report.html

# test specific user class
locust -f locustfile.py --host=http://localhost:8080 --users=15 --spawn-rate=3 --run-time=90s --headless HighVolumeUser
```

### Web UI Testing
```bash
# start interactive mode
./load_test.sh interactive

# configure test in browser:
# 1. Open http://localhost:8089
# 2. Set number of users
# 3. Set spawn rate
# 4. Start test
# 5. Monitor real-time charts
```

### Integration with CI/CD
The load tests can be integrated into your CI/CD pipeline:
```yaml
- name: Load Testing
  run: |
    docker-compose up -d
    sleep 10
    ./load_test.sh basic
    docker-compose down
```

## Troubleshooting

### Common Issues
1. **System not running**: Check `docker-compose ps`
2. **Port conflicts**: Ensure ports 8080, 8089 are available
3. **High error rates**: Check `docker-compose logs`
4. **Slow responses**: Monitor Redis with `docker-compose exec redis redis-cli info`

### Monitoring Commands
```bash
# check system status
make health

# view application logs
docker-compose logs -f app1 app2 app3

# monitor Redis cache
docker-compose exec redis redis-cli monitor
```

## Next Steps

1. **Run your first test**: `./load_test.sh basic`
2. **Explore the web UI**: `./load_test.sh interactive`
3. **Analyze reports**: Check `load_test_reports/` directory
4. **Customize scenarios**: Edit `locustfile.py` for your specific needs
5. **Set up monitoring**: Integrate with your monitoring stack

## Documentation

- **Full Guide**: See `LOAD_TESTING.md` for comprehensive documentation
- **Locust Docs**: https://docs.locust.io/
- **Configuration**: Edit `locust.conf` for default settings

---

**load testing framework is ready!** Start with `./load_test.sh basic` to validate your system performance.
