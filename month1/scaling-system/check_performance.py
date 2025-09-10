#!/usr/bin/env python3
"""
Performance Monitoring Script for Scaling System
=================================================

This script checks all the key performance metrics:
- Response times for cached vs non-cached requests
- Throughput (requests per second)
- Availability (uptime monitoring)
- System health checks
"""

import json
import statistics
import time
from datetime import datetime

import requests


class PerformanceMonitor:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.headers = {"Authorization": "Bearer test-token"}

    def check_response_times(self, iterations: int = 50):
        """Check response times for cached vs non-cached requests."""
        print("Testing Response Times...")

        # Create a test user first
        user_data = {"name": "Test User", "email": "test@example.com"}
        response = requests.post(
            f"{self.base_url}/api/users",
            json=user_data,
            headers=self.headers,
            timeout=10
        )

        if response.status_code != 200:
            return {"error": "Failed to create test user"}

        user_id = response.json()["data"]["id"]

        # Test non-cached request (first call)
        start_time = time.time()
        response = requests.get(
            f"{self.base_url}/api/users/{user_id}",
            headers=self.headers,
            timeout=5,
        )
        non_cached_time = (time.time() - start_time) * 1000  # Convert to ms

        # Test cached requests
        cached_times = []
        for _ in range(iterations):
            start_time = time.time()
            response = requests.get(
                f"{self.base_url}/api/users/{user_id}",
                headers=self.headers,
                timeout=5,
            )
            cached_times.append((time.time() - start_time) * 1000)
            time.sleep(0.01)  # Small delay between requests

        return {
            "non_cached_response_time_ms": round(non_cached_time, 2),
            "cached_avg_response_time_ms": round(statistics.mean(cached_times), 2),
            "cached_median_response_time_ms": round(statistics.median(cached_times), 2),
            "cached_95th_percentile_ms": round(
                statistics.quantiles(cached_times, n=20)[18], 2
            ),
            "target_met": statistics.mean(cached_times) < 100,
            "sample_size": iterations,
        }

    def check_throughput(
        self, concurrent_users: int = 100, duration: int = 30
    ):
        """Check system throughput with simple sequential requests."""
        print(f"🚀 Testing Throughput for {duration}s...")

        successful_requests = 0
        failed_requests = 0
        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                response = requests.get(
                    f"{self.base_url}/gateway-health", timeout=5
                )
                if response.status_code == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
            except Exception:
                failed_requests += 1

            time.sleep(0.001)  # Small delay

        total_time = time.time() - start_time
        total_requests = successful_requests + failed_requests

        return {
            "duration_seconds": round(total_time, 2),
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "requests_per_second": round(total_requests / total_time, 2),
            "success_rate_percent": (
                round((successful_requests / total_requests) * 100, 2)
                if total_requests > 0
                else 0
            ),
            "target_met": (total_requests / total_time) >= 1000,
        }

    def check_availability(
        self, check_interval: int = 5, duration: int = 60
    ):
        """Monitor system availability over time."""
        print(
            f"Monitoring Availability for {duration}s (checking every {check_interval}s)..."
        )

        total_checks = 0
        successful_checks = 0
        downtime_periods = []
        current_downtime_start = None

        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                response = requests.get(
                    f"{self.base_url}/gateway-health", headers=self.headers, timeout=5
                )
                total_checks += 1

                if response.status_code == 200:
                    successful_checks += 1
                    if current_downtime_start:
                        # End of downtime period
                        downtime_periods.append(time.time() - current_downtime_start)
                        current_downtime_start = None
                else:
                    if not current_downtime_start:
                        current_downtime_start = time.time()

            except Exception:
                total_checks += 1
                if not current_downtime_start:
                    current_downtime_start = time.time()

            time.sleep(check_interval)

        uptime_percentage = (
            (successful_checks / total_checks) * 100 if total_checks > 0 else 0
        )

        return {
            "uptime_percentage": round(uptime_percentage, 3),
            "total_checks": total_checks,
            "successful_checks": successful_checks,
            "failed_checks": total_checks - successful_checks,
            "downtime_periods": len(downtime_periods),
            "total_downtime_seconds": round(sum(downtime_periods), 2),
            "target_met": uptime_percentage >= 99.9,
        }

    def check_scalability(self):
        """Check horizontal scaling configuration."""
        print("🔧 Checking Scalability Configuration...")

        # Check if multiple app instances are running
        app_servers = set()
        for _ in range(10):
            try:
                response = requests.get(
                    f"{self.base_url}/api/health",
                    headers=self.headers,
                    timeout=5,
                )
                if response.status_code == 200:
                    server_id = response.headers.get("X-Server-ID", "unknown")
                    app_servers.add(server_id)
            except Exception:  # noqa: S112
                continue
            time.sleep(0.1)

        return {
            "unique_servers_detected": len(app_servers),
            "server_ids": list(app_servers),
            "load_balancing_working": len(app_servers) > 1,
            "horizontal_scaling_ready": len(app_servers) >= 3,
        }

    def run_all_checks(self):
        """Run all performance checks."""
        print("=" * 60)
        print("Performance Monitoring Dashboard")
        print("=" * 60)

        results = {
            "timestamp": datetime.now().isoformat(),
            "target_metrics": {
                "response_time_target": "< 100ms for cached requests",
                "throughput_target": "1000+ concurrent requests",
                "availability_target": "99.9% uptime",
                "scalability_target": "Horizontal scaling ready",
            },
        }

        # Check each metric
        results["response_times"] = self.check_response_times()
        results["scalability"] = self.check_scalability()
        results["availability"] = self.check_availability(
            duration=30
        )  # Shorter for demo

        # Run throughput test
        results["throughput"] = self.check_throughput(duration=15)

        return results

    def generate_report(self, results) -> str:
        """Generate a human-readable report."""
        report = []
        report.append("PERFORMANCE MONITORING REPORT")
        report.append("=" * 50)
        report.append(f"Timestamp: {results['timestamp']}")
        report.append("")

        # Response Time Analysis
        rt = results["response_times"]
        status = "PASS" if rt.get("target_met", False) else "FAIL"
        report.append(f"1. Response Time (Target: < 100ms): {status}")
        report.append(
            f"   • Cached avg: {rt.get('cached_avg_response_time_ms', 'N/A')}ms"
        )
        report.append(
            f"   • 95th percentile: {rt.get('cached_95th_percentile_ms', 'N/A')}ms"
        )
        report.append("")

        # throughput analysis
        th = results["throughput"]
        status = "PASS" if th.get("target_met", False) else " FAIL"
        report.append(f"2. Throughput (Target: 1000+ req/s): {status}")
        report.append(f"   • Achieved: {th.get('requests_per_second', 'N/A')} req/s")
        report.append(f"   • Success rate: {th.get('success_rate_percent', 'N/A')}%")
        report.append("")

        # Availability Analysis
        av = results["availability"]
        status = " PASS" if av.get("target_met", False) else " FAIL"
        report.append(f"3. Availability (Target: 99.9%): {status}")
        report.append(f"   • Uptime: {av.get('uptime_percentage', 'N/A')}%")
        report.append(f"   • Failed checks: {av.get('failed_checks', 'N/A')}")
        report.append("")

        # Scalability Analysis
        sc = results["scalability"]
        status = "PASS" if sc.get("horizontal_scaling_ready", False) else " FAIL"
        report.append(f"4. Scalability (Target: Multi-instance): {status}")
        report.append(
            f"   • Active servers: {sc.get('unique_servers_detected', 'N/A')}"
        )
        report.append(
            f"   • Load balancing: {'True' if sc.get('load_balancing_working', False) else 'False'}"
        )

        return "\n".join(report)


def main():
    """Main function to run performance monitoring."""
    monitor = PerformanceMonitor()

    # Check if system is running
    try:
        response = requests.get(f"{monitor.base_url}/gateway-health", timeout=5)
        if response.status_code != 200:
            print(
                "System is not responding properly. Please start with: docker-compose up -d"
            )
            return
    except Exception:
        print("System is not running. Please start with: docker-compose up -d")
        return

    print("System is running. Starting performance monitoring...")

    # Run all checks
    results = monitor.run_all_checks()

    # Generate and display report
    report = monitor.generate_report(results)
    print("\n" + report)

    # Save detailed results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"performance_report_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {filename}")


if __name__ == "__main__":
    main()
