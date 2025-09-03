#!/bin/bash

# Load Testing Scripts for Scaling System
# =======================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HOST="http://localhost:8080"
REPORTS_DIR="load_test_reports"

# Create reports directory
mkdir -p "$REPORTS_DIR"

print_banner() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Scaling System Load Testing   ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

check_system() {
    echo -e "${YELLOW} Checking if system is running...${NC}"
    
    if ! curl -s "$HOST/gateway-health" > /dev/null; then
        echo -e "${RED} System is not running at $HOST${NC}"
        echo -e "${YELLOW} Please start the system first:${NC}"
        echo "   docker-compose up -d"
        exit 1
    fi
    
    echo -e "${GREEN} System is running${NC}"
    echo
}

install_locust() {
    echo -e "${YELLOW} Checking Locust installation...${NC}"
    
    if ! command -v locust &> /dev/null; then
        echo -e "${YELLOW}Installing Locust...${NC}"
        pip install locust
    fi
    
    echo -e "${GREEN} Locust is ready${NC}"
    echo
}

run_basic_test() {
    echo -e "${YELLOW} Running Basic Load Test...${NC}"
    echo "Duration: 60 seconds, Users: 3, Spawn rate: 1/sec"
    echo "Note: Reduced load to work within rate limits (20 req/min)"
    echo
    
    locust -f locustfile.py \
        --host="$HOST" \
        --users=3 \
        --spawn-rate=1 \
        --run-time=60s \
        --headless \
        --html="$REPORTS_DIR/basic_test_$(date +%Y%m%d_%H%M%S).html" \
        --csv="$REPORTS_DIR/basic_test_$(date +%Y%m%d_%H%M%S)"
    
    echo -e "${GREEN} Basic test completed!${NC}"
}

run_stress_test() {
    echo -e "${YELLOW} Running Stress Test...${NC}"
    echo "Duration: 300 seconds (5 min), Users: 8, Spawn rate: 2/sec"
    echo "Note: Moderate load to test rate limiting behavior"
    echo
    
    locust -f locustfile.py \
        --host="$HOST" \
        --users=8 \
        --spawn-rate=2 \
        --run-time=300s \
        --headless \
        --html="$REPORTS_DIR/stress_test_$(date +%Y%m%d_%H%M%S).html" \
        --csv="$REPORTS_DIR/stress_test_$(date +%Y%m%d_%H%M%S)"
    
    echo -e "${GREEN} Stress test completed!${NC}"
}

run_cache_test() {
    echo -e "${YELLOW}⚡ Running Cache Performance Test...${NC}"
    echo "Duration: 120 seconds, Users: 5, Focus on read operations"
    echo "Note: Testing cache hit rates with moderate load"
    echo
    
    # Use HighVolumeUser class for cache testing
    locust -f locustfile.py \
        --host="$HOST" \
        --users=5 \
        --spawn-rate=2 \
        --run-time=120s \
        --headless \
        --html="$REPORTS_DIR/cache_test_$(date +%Y%m%d_%H%M%S).html" \
        --csv="$REPORTS_DIR/cache_test_$(date +%Y%m%d_%H%M%S)" \
        HighVolumeUser
    
    echo -e "${GREEN} Cache test completed!${NC}"
}

run_spike_test() {
    echo -e "${YELLOW} Running Spike Test...${NC}"
    echo "Simulating traffic spikes: 1→10→1 users (rate-limit friendly)"
    echo
    
    # First wave
    echo " Wave 1: 1 user for 30s"
    timeout 30s locust -f locustfile.py --host="$HOST" --users=1 --spawn-rate=1 --headless &
    wait
    
    # Spike (reduced from 50 to 10 users)
    echo " SPIKE: 10 users for 60s"
    timeout 60s locust -f locustfile.py --host="$HOST" --users=10 --spawn-rate=5 --headless &
    wait
    
    # Cool down
    echo "  Cool down: 1 user for 30s"
    timeout 30s locust -f locustfile.py --host="$HOST" --users=1 --spawn-rate=1 --headless &
    wait
    
    echo -e "${GREEN} Spike test completed!${NC}"
}

run_interactive() {
    echo -e "${YELLOW} Starting Interactive Locust UI...${NC}"
    echo "Open your browser to: http://localhost:8089"
    echo "Host: $HOST"
    echo "Recommended settings for rate limits:"
    echo "  - Users: 3-5"
    echo "  - Spawn rate: 1-2/sec"
    echo "Press Ctrl+C to stop"
    echo
    
    locust -f locustfile.py --host="$HOST"
}

show_reports() {
    echo -e "${YELLOW} Available Reports:${NC}"
    if [ -d "$REPORTS_DIR" ] && [ "$(ls -A $REPORTS_DIR)" ]; then
        ls -la "$REPORTS_DIR"/*.html 2>/dev/null || echo "No HTML reports found"
        echo
        echo -e "${BLUE} Open any .html file in your browser to view the report${NC}"
    else
        echo "No reports found. Run some tests first!"
    fi
}

show_help() {
    echo -e "${GREEN}Load Testing Commands:${NC}"
    echo
    echo "  $0 basic      - Quick 60s test with 3 users"
    echo "  $0 stress     - 5-minute test with 8 users"
    echo "  $0 cache      - Cache performance test"
    echo "  $0 spike      - Traffic spike simulation"
    echo "  $0 interactive - Start Locust web UI"
    echo "  $0 reports    - Show available reports"
    echo "  $0 all        - Run all automated tests"
    echo
    echo -e "${YELLOW}Note: Tests are configured for rate limits (20 req/min)${NC}"
    echo
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 basic              # Run basic test"
    echo "  $0 stress             # Run stress test"
    echo "  $0 interactive        # Open web UI"
    echo
}

# Main script logic
print_banner

case "${1:-help}" in
    "basic")
        check_system
        install_locust
        run_basic_test
        ;;
    "stress")
        check_system
        install_locust
        run_stress_test
        ;;
    "cache")
        check_system
        install_locust
        run_cache_test
        ;;
    "spike")
        check_system
        install_locust
        run_spike_test
        ;;
    "interactive"|"ui")
        check_system
        install_locust
        run_interactive
        ;;
    "reports")
        show_reports
        ;;
    "all")
        check_system
        install_locust
        echo -e "${BLUE}🏃 Running all automated tests...${NC}"
        run_basic_test
        echo
        run_cache_test
        echo
        run_stress_test
        echo -e "${GREEN} All tests completed!${NC}"
        show_reports
        ;;
    "help"|*)
        show_help
        ;;
esac
