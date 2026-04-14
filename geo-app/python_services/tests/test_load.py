"""Load tests — basic throughput and concurrency validation."""

import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


@pytest.mark.slow
class TestConcurrentHealth:
    """Concurrent requests to /health."""

    def test_10_concurrent_health_checks(self, api_client):
        """10 concurrent health checks should all succeed."""
        results = []

        def check_health():
            return api_client.get("/health")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_health) for _ in range(10)]
            for future in as_completed(futures):
                results.append(future.result())

        assert all(r.status_code == 200 for r in results)

    def test_throughput_health(self, api_client):
        """Measure throughput for /health endpoint."""
        n_requests = 50
        start = time.time()

        for _ in range(n_requests):
            r = api_client.get("/health")
            assert r.status_code == 200

        elapsed = time.time() - start
        throughput = n_requests / elapsed
        assert throughput > 5, f"Throughput too low: {throughput:.1f} req/s"


@pytest.mark.slow
class TestConcurrentHeatmap:
    """Concurrent requests to /predictions/heatmap."""

    def test_10_concurrent_heatmap(self, api_client):
        results = []

        def get_heatmap():
            return api_client.get("/predictions/heatmap")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_heatmap) for _ in range(10)]
            for future in as_completed(futures):
                results.append(future.result())

        assert all(r.status_code == 200 for r in results)


@pytest.mark.slow
class TestResponseTimes:
    """P95 response time validation."""

    def test_health_p95_under_500ms(self, api_client):
        times = []
        for _ in range(30):
            start = time.time()
            api_client.get("/health")
            times.append(time.time() - start)

        times.sort()
        p95 = times[int(len(times) * 0.95)]
        assert p95 < 0.5, f"P95 response time too high: {p95:.3f}s"
