# Stress Tests

This directory contains performance and load tests to verify the Skye library handles high-load scenarios correctly.

## Purpose

Stress tests verify that the library performs well under load and handles concurrent operations correctly. They should:
- Test concurrent request handling
- Verify rate limiting under load
- Test failover scenarios under stress
- Measure and report performance metrics
- Identify race conditions and bottlenecks

## Test Files

```
stress/
├── test_concurrent_routing.py    # Concurrent request handling
├── test_rate_limiting.py          # Rate limit enforcement under load
├── test_capability_load.py        # Capability execution under load
└── test_failover.py               # Failover behavior under stress
```

## Running Stress Tests

```bash
# Run all stress tests
pytest tests/stress/

# Run specific stress test
pytest tests/stress/test_concurrent_routing.py

# Run with verbose output
pytest tests/stress/ -v

# Run with performance metrics
pytest tests/stress/ --benchmark-only
```

## Performance Metrics

Stress tests track and report:
- **Requests per second (RPS)** - Throughput under load
- **Average latency** - Mean response time
- **P95/P99 latency** - Tail latency percentiles
- **Error rate** - Percentage of failed requests
- **Memory usage** - Peak memory consumption
- **Concurrent requests** - Number of simultaneous operations

## Writing Stress Tests

### Concurrent Request Test

```python
import pytest
import asyncio
import time
from skye.router import ModelRouter
from skye.base.completion import CompletionRequest
from skye.base.messages import UserMessage

@pytest.mark.stress
@pytest.mark.asyncio
async def test_concurrent_routing_100_requests():
    """Test router with 100 concurrent requests.
    
    Metrics tracked:
    - Total time
    - Average latency
    - Success rate
    - Memory usage
    """
    router = ModelRouter.from_yaml("tests/fixtures/sample_config.yaml")
    
    async def make_request(request_id: int):
        """Make a single request."""
        request = CompletionRequest(
            messages=[UserMessage(content=f"Request {request_id}")],
            model="gpt-3.5-turbo"
        )
        start = time.time()
        try:
            response = await router.acomplete(messages=request.messages, model=request.model)
            latency = time.time() - start
            return {"success": True, "latency": latency, "id": request_id}
        except Exception as e:
            latency = time.time() - start
            return {"success": False, "latency": latency, "id": request_id, "error": str(e)}
    
    # Create 100 concurrent requests
    start_time = time.time()
    tasks = [make_request(i) for i in range(100)]
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    latencies = [r["latency"] for r in results]
    
    # Calculate metrics
    success_rate = len(successful) / len(results) * 100
    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
    p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
    rps = len(results) / total_time
    
    # Print metrics
    print(f"\n=== Concurrent Routing Test Results ===")
    print(f"Total requests: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Success rate: {success_rate:.2f}%")
    print(f"Total time: {total_time:.2f}s")
    print(f"Requests/sec: {rps:.2f}")
    print(f"Avg latency: {avg_latency:.3f}s")
    print(f"P95 latency: {p95_latency:.3f}s")
    print(f"P99 latency: {p99_latency:.3f}s")
    
    # Assertions
    assert success_rate >= 95.0, f"Success rate too low: {success_rate}%"
    assert avg_latency < 5.0, f"Average latency too high: {avg_latency}s"
    assert len(failed) == 0, f"Some requests failed: {failed}"
```

### Rate Limiting Test

```python
import pytest
import asyncio
import time
from skye.router import ModelRouter

@pytest.mark.stress
@pytest.mark.asyncio
async def test_rate_limiting_enforcement():
    """Test rate limit enforcement under load.
    
    Verifies:
    - TPM/RPM limits are enforced
    - Rate limit tracking is accurate
    - Pre-call checks work correctly
    """
    router = ModelRouter.from_yaml("tests/fixtures/rate_limit_config.yaml")
    
    # Configure with strict rate limits
    target = router.routes[0].targets[0]
    target.rpm = 10  # 10 requests per minute
    target.tpm = 1000  # 1000 tokens per minute
    
    async def make_request():
        """Make a request and track if it was rate limited."""
        try:
            response = await router.acomplete(messages=request.messages, model=request.model)
            return {"rate_limited": False}
        except RateLimitError:
            return {"rate_limited": True}
    
    # Make 20 requests (should hit rate limit)
    start_time = time.time()
    tasks = [make_request() for _ in range(20)]
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start_time
    
    # Count rate limited requests
    rate_limited = sum(1 for r in results if r["rate_limited"])
    successful = len(results) - rate_limited
    
    print(f"\n=== Rate Limiting Test Results ===")
    print(f"Total requests: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Rate limited: {rate_limited}")
    print(f"Time elapsed: {elapsed:.2f}s")
    
    # Verify rate limiting worked
    assert rate_limited > 0, "Rate limiting should have triggered"
    assert successful <= 10, "Should not exceed RPM limit"
```

### Capability Load Test

```python
import pytest
import asyncio
from skye.tools import CapabilityRegistry, capability

@pytest.mark.stress
@pytest.mark.asyncio
async def test_capability_concurrent_execution():
    """Test concurrent capability execution.
    
    Verifies:
    - Capabilities execute correctly under load
    - No race conditions in registry
    - Performance remains acceptable
    """
    # Register test capability
    @capability(name="test_capability")
    async def test_capability(value: int) -> int:
        await asyncio.sleep(0.01)  # Simulate work
        return value * 2
    
    registry = CapabilityRegistry()
    registry.register(test_capability)
    
    async def execute_capability(value: int):
        """Execute capability and measure time."""
        start = time.time()
        result = await registry.execute("test_capability", {"value": value})
        latency = time.time() - start
        return {"result": result, "latency": latency}
    
    # Execute 100 concurrent capability calls
    tasks = [execute_capability(i) for i in range(100)]
    results = await asyncio.gather(*tasks)
    
    # Verify results
    assert len(results) == 100
    assert all(r["result"] == i * 2 for i, r in enumerate(results))
    
    # Check performance
    avg_latency = sum(r["latency"] for r in results) / len(results)
    print(f"\n=== Capability Load Test Results ===")
    print(f"Total executions: {len(results)}")
    print(f"Average latency: {avg_latency:.3f}s")
    
    assert avg_latency < 0.1, f"Latency too high: {avg_latency}s"
```

### Failover Test

```python
import pytest
import asyncio
from skye.router import ModelRouter
from unittest.mock import patch

@pytest.mark.stress
@pytest.mark.asyncio
async def test_failover_under_load():
    """Test router failover behavior under load.
    
    Verifies:
    - Failover works correctly under stress
    - Cooldown mechanism functions properly
    - Fallback chains execute correctly
    """
    router = ModelRouter.from_yaml("tests/fixtures/fallback_config.yaml")
    
    # Simulate primary model failures
    failure_count = 0
    
    async def make_request_with_failures():
        """Make request that may fail."""
        nonlocal failure_count
        try:
            response = await router.acomplete(messages=request.messages, model=request.model)
            return {"success": True, "used_fallback": False}
        except Exception as e:
            failure_count += 1
            # Router should have tried fallback
            return {"success": False, "error": str(e)}
    
    # Make 50 concurrent requests
    tasks = [make_request_with_failures() for _ in range(50)]
    results = await asyncio.gather(*tasks)
    
    successful = sum(1 for r in results if r["success"])
    
    print(f"\n=== Failover Test Results ===")
    print(f"Total requests: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    print(f"Failure count: {failure_count}")
    
    # Verify failover worked
    assert successful > 0, "Some requests should succeed via fallback"
```

## Performance Benchmarks

Expected performance characteristics:

### Concurrent Routing
- **100 concurrent requests**: < 10s total time
- **Success rate**: > 95%
- **Average latency**: < 2s per request
- **P99 latency**: < 5s

### Rate Limiting
- **Enforcement accuracy**: > 99%
- **Overhead**: < 10ms per request
- **Memory usage**: < 100MB for 1000 tracked requests

### Capability Execution
- **100 concurrent executions**: < 5s total time
- **Average latency**: < 50ms per execution
- **No race conditions**: 100% success rate

### Failover
- **Failover latency**: < 1s additional overhead
- **Success rate with fallback**: > 90%
- **Cooldown accuracy**: > 95%

## Best Practices

1. **Use realistic load** - Test with production-like request volumes
2. **Measure everything** - Track all relevant metrics
3. **Test failure scenarios** - Verify behavior under errors
4. **Run multiple times** - Ensure consistency
5. **Monitor resources** - Track memory and CPU usage
6. **Use async properly** - Leverage asyncio for concurrency
7. **Clean up resources** - Prevent resource leaks

## Common Patterns

### Memory Profiling

```python
import pytest
import tracemalloc

@pytest.mark.stress
def test_memory_usage():
    """Test memory usage under load."""
    tracemalloc.start()
    
    # Run stress test
    run_stress_test()
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"Current memory: {current / 1024 / 1024:.2f} MB")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
    
    assert peak < 500 * 1024 * 1024, "Memory usage too high"
```

### Latency Distribution

```python
import numpy as np

def analyze_latencies(latencies: list[float]):
    """Analyze latency distribution."""
    latencies_array = np.array(latencies)
    
    print(f"Min: {latencies_array.min():.3f}s")
    print(f"Max: {latencies_array.max():.3f}s")
    print(f"Mean: {latencies_array.mean():.3f}s")
    print(f"Median: {np.median(latencies_array):.3f}s")
    print(f"Std Dev: {latencies_array.std():.3f}s")
    print(f"P50: {np.percentile(latencies_array, 50):.3f}s")
    print(f"P95: {np.percentile(latencies_array, 95):.3f}s")
    print(f"P99: {np.percentile(latencies_array, 99):.3f}s")
```

## Troubleshooting

### Tests Timing Out
- Increase pytest timeout: `pytest --timeout=300`
- Reduce concurrent request count
- Check for deadlocks in async code

### High Memory Usage
- Check for resource leaks
- Ensure proper cleanup in fixtures
- Use memory profiling to identify issues

### Inconsistent Results
- Run tests multiple times
- Check for race conditions
- Ensure deterministic test data

## CI/CD Integration

Stress tests should:
- Run nightly (not on every commit)
- Have longer timeouts
- Report metrics to monitoring system
- Alert on performance regressions

## Related Documentation

- [Main Test README](../README.md)
- [Unit Tests](../unit/README.md)
- [Integration Tests](../integration/README.md)
- [Skye Architecture](../../.kiro/steering/00-rules.md)
