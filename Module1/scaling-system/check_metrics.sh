#!/bin/bash

# Performance Monitoring Script for Scaling System
# ================================================

set -e

# colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HOST="http://localhost:8080"
AUTH_TOKEN="Bearer test-token"

print_banner() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Performance Monitoring Report ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

check_system() {
    echo -e "${YELLOW} Checking if system is running...${NC}"
    
    if ! curl -s "$HOST/gateway-health" > /dev/null; then
        echo -e "${RED} System is not running at $HOST${NC}"
        echo -e "${YELLOW}Please start the system first:${NC}"
        echo "   docker-compose up -d"
        exit 1
    fi
    
    echo -e "${GREEN} System is running${NC}"
    echo
}

check_response_times() {
    echo -e "${BLUE}1. Response Time Analysis${NC}"
    echo "Target: < 100ms for cached requests"
    echo "----------------------------------------"
    
    # Create a test user
    USER_ID=$(curl -s -X POST "$HOST/api/users" \
        -H "Authorization: $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"name":"Test User","email":"test@example.com"}' | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "1")
    
    # Test non-cached request
    echo "Testing non-cached request..."
    NON_CACHED_TIME=$(curl -s -w "%{time_total}" -o /dev/null \
        -H "Authorization: $AUTH_TOKEN" \
        "$HOST/api/users/$USER_ID")
    NON_CACHED_MS=$(echo "$NON_CACHED_TIME * 1000" | bc -l 2>/dev/null || echo "N/A")
    
    # Test cached requests (5 samples)
    echo "Testing cached requests (5 samples)..."
    CACHED_TIMES=()
    for i in {1..5}; do
        TIME=$(curl -s -w "%{time_total}" -o /dev/null \
            -H "Authorization: $AUTH_TOKEN" \
            "$HOST/api/users/$USER_ID")
        CACHED_MS=$(echo "$TIME * 1000" | bc -l 2>/dev/null || echo "0")
        CACHED_TIMES+=($CACHED_MS)
        sleep 0.1
    done
    
    # Calculate average
    TOTAL=0
    for time in "${CACHED_TIMES[@]}"; do
        TOTAL=$(echo "$TOTAL + $time" | bc -l 2>/dev/null || echo "$TOTAL")
    done
    AVG_CACHED=$(echo "scale=2; $TOTAL / ${#CACHED_TIMES[@]}" | bc -l 2>/dev/null || echo "N/A")
    
    echo "• Non-cached response time: ${NON_CACHED_MS}ms"
    echo "• Cached average response time: ${AVG_CACHED}ms"
    
    # Check if target is met
    if (( $(echo "$AVG_CACHED < 100" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "${GREEN} Target met: Response time < 100ms${NC}"
    else
        echo -e "${RED} Target not met: Response time >= 100ms${NC}"
    fi
    echo
}

check_throughput() {
    echo -e "${BLUE}2. Throughput Analysis${NC}"
    echo "Target: 1000+ requests per second"
    echo "----------------------------------------"
    
    # Simple throughput test (10 seconds)
    echo "Running throughput test for 10 seconds..."
    
    COUNT=0
    START_TIME=$(date +%s)
    
    while [ $(($(date +%s) - START_TIME)) -lt 10 ]; do
        if curl -s "$HOST/gateway-health" > /dev/null; then
            ((COUNT++))
        fi
        # Small delay to prevent overwhelming
        sleep 0.01
    done
    
    DURATION=$(($(date +%s) - START_TIME))
    RPS=$((COUNT / DURATION))
    
    echo "• Total requests: $COUNT"
    echo "• Duration: ${DURATION}s"
    echo "• Requests per second: $RPS"
    
    if [ $RPS -ge 1000 ]; then
        echo -e "${GREEN} Target met: $RPS >= 1000 req/s${NC}"
    else
        echo -e "${RED} Target not met: $RPS < 1000 req/s${NC}"
    fi
    echo
}

check_availability() {
    echo -e "${BLUE}3. Availability Analysis${NC}"
    echo "Target: 99.9% uptime"
    echo "----------------------------------------"
    
    # Monitor for 30 seconds, check every 5 seconds
    echo "Monitoring availability for 30 seconds..."
    
    TOTAL_CHECKS=0
    SUCCESSFUL_CHECKS=0
    
    for i in {1..6}; do
        if curl -s "$HOST/gateway-health" > /dev/null; then
            ((SUCCESSFUL_CHECKS++))
        fi
        ((TOTAL_CHECKS++))
        if [ $i -lt 6 ]; then
            sleep 5
        fi
    done
    
    # Calculate uptime percentage
    UPTIME_PERCENT=$(echo "scale=3; $SUCCESSFUL_CHECKS * 100 / $TOTAL_CHECKS" | bc -l 2>/dev/null || echo "0")
    
    echo "• Total checks: $TOTAL_CHECKS"
    echo "• Successful checks: $SUCCESSFUL_CHECKS"
    echo "• Uptime percentage: ${UPTIME_PERCENT}%"
    
    if (( $(echo "$UPTIME_PERCENT >= 99.9" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "${GREEN} Target met: ${UPTIME_PERCENT}% >= 99.9%${NC}"
    else
        echo -e "${RED} Target not met: ${UPTIME_PERCENT}% < 99.9%${NC}"
    fi
    echo
}

check_scalability() {
    echo -e "${BLUE}4. Scalability Analysis${NC}"
    echo "Target: Horizontal scaling ready"
    echo "----------------------------------------"
    
    # Check for multiple server instances
    echo "Checking for multiple server instances..."
    
    SERVERS=()
    for i in {1..10}; do
        SERVER_ID=$(curl -s -H "Authorization: $AUTH_TOKEN" "$HOST/api/health" | \
            grep -o '"X-Server-ID":[^,]*' | cut -d'"' -f4 2>/dev/null || echo "")
        if [ ! -z "$SERVER_ID" ] && [[ ! " ${SERVERS[@]} " =~ " ${SERVER_ID} " ]]; then
            SERVERS+=("$SERVER_ID")
        fi
        sleep 0.1
    done
    
    UNIQUE_SERVERS=${#SERVERS[@]}
    
    echo "• Unique servers detected: $UNIQUE_SERVERS"
    echo "• Server IDs: ${SERVERS[*]}"
    
    if [ $UNIQUE_SERVERS -ge 3 ]; then
        echo -e "${GREEN} Target met: $UNIQUE_SERVERS servers (horizontal scaling ready)${NC}"
        if [ $UNIQUE_SERVERS -gt 1 ]; then
            echo -e "${GREEN} Load balancing working${NC}"
        fi
    else
        echo -e "${RED} Target not met: Only $UNIQUE_SERVERS servers detected${NC}"
        echo -e "${RED} Need at least 3 servers for horizontal scaling${NC}"
    fi
    echo
}

run_load_test() {
    echo -e "${BLUE}5. Load Test with Locust${NC}"
    echo "----------------------------------------"
    
    if command -v locust &> /dev/null; then
        echo "Running basic load test with Locust..."
        if [ -f "load_test.sh" ]; then
            ./load_test.sh basic
        else
            echo "Running direct locust command..."
            locust -f locustfile.py --host=$HOST --users=10 --spawn-rate=2 --run-time=30s --headless
        fi
    else
        echo -e "${YELLOW}  Locust not installed. Skipping load test.${NC}"
        echo "To install: pip install locust"
    fi
    echo
}

main() {
    print_banner
    check_system
    
    echo -e "${GREEN}Starting comprehensive performance monitoring...${NC}"
    echo
    
    check_response_times
    check_throughput
    check_availability
    check_scalability
    run_load_test
    
    echo -e "${BLUE}================================${NC}"
    echo -e "${GREEN}Performance monitoring complete!${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
    
    echo " Tips for improvement:"
    echo "1. For faster response times: Optimize caching strategy"
    echo "2. For higher throughput: Scale horizontally with more instances"
    echo "3. For better availability: Implement health checks and auto-recovery"
    echo "4. For scaling: Use container orchestration (K8s) or AWS ECS"
    echo
    
    echo " To run detailed load tests:"
    echo "   ./load_test.sh stress    # 5-minute stress test"
    echo "   ./load_test.sh cache     # Cache performance test"
    echo "   ./load_test.sh all       # All test scenarios"
}

main "$@"
