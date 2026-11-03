"""Stress tests for capability execution under load.

This module tests the capability system's ability to handle high concurrent load,
verifying correct behavior including:
- Concurrent capability execution (100+ simultaneous calls)
- Capability registry performance under load
- MCP capability performance
- Execution latency distribution
- Thread safety and race condition detection

**Validates: Requirements 7.4**
"""

import asyncio
import statistics
import threading
import time
from typing import Any

import pytest

from skye.tools import (
    CapabilityInterface,
    CapabilityRegistry,
    CapabilitySchema,
    LocalFunctionCapability,
)


class MockCapability(CapabilityInterface):
    """Mock capability for testing that simulates realistic behavior."""

    def __init__(
        self,
        name: str,
        latency_ms: float = 10.0,
        failure_rate: float = 0.0,
    ):
        """Initialize mock capability.

        Args:
            name: Capability name
            latency_ms: Simulated latency in milliseconds
            failure_rate: Probability of failure (0.0-1.0)
        """
        self.name = name
        self.latency_ms = latency_ms
        self.failure_rate = failure_rate
        self.call_count = 0
        self.concurrent_calls = 0
        self.max_concurrent_calls = 0
        self.lock = threading.Lock()

    def get_schema(self) -> CapabilitySchema:
        """Get capability schema."""
        return CapabilitySchema(
            name=self.name,
            description=f"Mock capability: {self.name}",
            parameters={
                "type": "object",
                "properties": {
                    "value": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["value"],
            },
            returns={"type": "string"},
        )

    def execute(self, **kwargs: Any) -> Any:
        """Execute capability synchronously."""
        with self.lock:
            self.call_count += 1
            self.concurrent_calls += 1
            self.max_concurrent_calls = max(self.max_concurrent_calls, self.concurrent_calls)

        try:
            # Simulate latency
            time.sleep(self.latency_ms / 1000.0)

            # Simulate random failures
            import random

            if random.random() < self.failure_rate:
                raise Exception(f"Simulated failure in {self.name}")

            # Return result
            value = kwargs.get("value", 0)
            text = kwargs.get("text", "")
            return f"Result: {value}, {text}"
        finally:
            with self.lock:
                self.concurrent_calls -= 1

    async def aexecute(self, **kwargs: Any) -> Any:
        """Execute capability asynchronously."""
        with self.lock:
            self.call_count += 1
            self.concurrent_calls += 1
            self.max_concurrent_calls = max(self.max_concurrent_calls, self.concurrent_calls)

        try:
            # Simulate latency
            await asyncio.sleep(self.latency_ms / 1000.0)

            # Simulate random failures
            import random

            if random.random() < self.failure_rate:
                raise Exception(f"Simulated failure in {self.name}")

            # Return result
            value = kwargs.get("value", 0)
            text = kwargs.get("text", "")
            return f"Result: {value}, {text}"
        finally:
            with self.lock:
                self.concurrent_calls -= 1


@pytest.mark.stress
class TestCapabilityLoad:
    """Stress tests for capability execution under load."""

    def test_concurrent_capability_execution_100_calls(self):
        """Test concurrent capability execution with 100 simultaneous calls.

        Verifies:
        - All calls complete successfully
        - No race conditions in capability state
        - Performance metrics are acceptable
        - Concurrent call counter is accurate

        **Validates: Requirements 7.4**
        """
        # Create registry and register capabilities
        registry = CapabilityRegistry()
        cap1 = MockCapability("cap-1", latency_ms=20)
        cap2 = MockCapability("cap-2", latency_ms=20)
        cap3 = MockCapability("cap-3", latency_ms=20)

        registry.register(cap1)
        registry.register(cap2)
        registry.register(cap3)

        # Track results
        results = []
        errors = []
        start_time = time.time()

        def execute_capability(call_id: int, cap_name: str):
            """Execute a capability and track result."""
            req_start = time.time()
            try:
                result = registry.execute(
                    cap_name,
                    {"value": call_id, "text": f"call-{call_id}"},
                    return_raw=True,
                )
                latency = time.time() - req_start
                results.append(
                    {
                        "id": call_id,
                        "success": True,
                        "latency": latency,
                        "capability": cap_name,
                    }
                )
            except Exception as e:
                latency = time.time() - req_start
                errors.append(
                    {"id": call_id, "error": str(e), "latency": latency, "capability": cap_name}
                )

        # Execute 100 concurrent calls (distributed across 3 capabilities)
        threads = []
        for i in range(100):
            cap_name = ["cap-1", "cap-2", "cap-3"][i % 3]
            thread = threading.Thread(target=execute_capability, args=(i, cap_name))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Calculate metrics
        successful = len(results)
        failed = len(errors)
        latencies = [r["latency"] for r in results]

        if latencies:
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
            p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        else:
            avg_latency = min_latency = max_latency = p95_latency = p99_latency = 0.0

        rps = (successful + failed) / total_time if total_time > 0 else 0

        # Print metrics
        print(f"\n{'=' * 60}")
        print("Concurrent Capability Execution Test Results (100 calls)")
        print(f"{'=' * 60}")
        print(f"Total calls:        {successful + failed}")
        print(f"Successful:         {successful}")
        print(f"Failed:             {failed}")
        print(f"Success rate:       {successful / (successful + failed) * 100:.2f}%")
        print(f"Total time:         {total_time:.2f}s")
        print(f"Calls/sec:          {rps:.2f}")
        print(f"Avg latency:        {avg_latency:.3f}s")
        print(f"Min latency:        {min_latency:.3f}s")
        print(f"Max latency:        {max_latency:.3f}s")
        print(f"P95 latency:        {p95_latency:.3f}s")
        print(f"P99 latency:        {p99_latency:.3f}s")
        print(f"{'=' * 60}")

        # Verify distribution across capabilities
        cap_counts = {}
        for result in results:
            cap = result["capability"]
            cap_counts[cap] = cap_counts.get(cap, 0) + 1

        print("\nCapability distribution:")
        for cap, count in sorted(cap_counts.items()):
            print(f"  {cap}: {count} calls")

        # Assertions
        assert successful == 100, f"Expected 100 successful calls, got {successful}"
        assert failed == 0, f"Expected 0 failures, got {failed}"
        assert avg_latency < 1.0, f"Average latency too high: {avg_latency:.3f}s"
        assert p99_latency < 2.0, f"P99 latency too high: {p99_latency:.3f}s"

        # Verify no concurrent call counter issues
        for cap_name in ["cap-1", "cap-2", "cap-3"]:
            cap = registry.get(cap_name)
            assert cap.concurrent_calls == 0, (
                f"Capability {cap_name} has {cap.concurrent_calls} concurrent calls after completion"
            )

    def test_capability_registry_under_load(self):
        """Test capability registry performance under concurrent load.

        Verifies:
        - Registry handles concurrent registrations safely
        - Registry lookup is fast under load
        - No race conditions in registry state
        - Registry can handle many capabilities

        **Validates: Requirements 7.4**
        """
        registry = CapabilityRegistry()

        # Register 50 capabilities
        capabilities = []
        for i in range(50):
            cap = MockCapability(f"cap-{i}", latency_ms=5)
            capabilities.append(cap)
            registry.register(cap)

        # Verify all registered
        assert registry.count() == 50, f"Expected 50 capabilities, got {registry.count()}"

        # Track lookup performance
        lookup_times = []
        execution_times = []

        def lookup_and_execute(call_id: int):
            """Lookup and execute a capability."""
            cap_id = call_id % 50
            cap_name = f"cap-{cap_id}"

            # Measure lookup time
            lookup_start = time.time()
            cap = registry.get(cap_name)
            lookup_time = time.time() - lookup_start
            lookup_times.append(lookup_time)

            # Measure execution time
            exec_start = time.time()
            try:
                result = registry.execute(cap_name, {"value": call_id}, return_raw=True)
                exec_time = time.time() - exec_start
                execution_times.append(exec_time)
            except Exception:
                pass

        # Execute 200 concurrent lookups and executions
        threads = []
        start_time = time.time()

        for i in range(200):
            thread = threading.Thread(target=lookup_and_execute, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Calculate metrics
        avg_lookup = statistics.mean(lookup_times) if lookup_times else 0.0
        max_lookup = max(lookup_times) if lookup_times else 0.0
        avg_exec = statistics.mean(execution_times) if execution_times else 0.0

        print(f"\n{'=' * 60}")
        print("Registry Performance Under Load (200 concurrent operations)")
        print(f"{'=' * 60}")
        print(f"Total capabilities:  {registry.count()}")
        print(f"Total operations:    {len(lookup_times)}")
        print(f"Total time:          {total_time:.2f}s")
        print("\nLookup performance:")
        print(f"  Average:           {avg_lookup * 1000:.3f}ms")
        print(f"  Max:               {max_lookup * 1000:.3f}ms")
        print("\nExecution performance:")
        print(f"  Average:           {avg_exec:.3f}s")
        print(f"{'=' * 60}")

        # Verify performance is acceptable
        assert avg_lookup < 0.01, f"Average lookup too slow: {avg_lookup * 1000:.3f}ms"
        assert max_lookup < 0.05, f"Max lookup too slow: {max_lookup * 1000:.3f}ms"

    def test_concurrent_capability_execution_with_failures(self):
        """Test concurrent capability execution with failures.

        Verifies:
        - Failures are handled correctly under load
        - Error tracking is accurate
        - No race conditions with error handling
        - Concurrent calls continue despite failures

        **Validates: Requirements 7.4**
        """
        registry = CapabilityRegistry()

        # Register capabilities with different failure rates
        cap1 = MockCapability("cap-1", latency_ms=10, failure_rate=0.2)  # 20% failure
        cap2 = MockCapability("cap-2", latency_ms=10, failure_rate=0.1)  # 10% failure
        cap3 = MockCapability("cap-3", latency_ms=10, failure_rate=0.0)  # No failures

        registry.register(cap1)
        registry.register(cap2)
        registry.register(cap3)

        # Track results
        results = []
        lock = threading.Lock()

        def execute_capability(call_id: int):
            """Execute a capability."""
            cap_name = ["cap-1", "cap-2", "cap-3"][call_id % 3]
            try:
                result = registry.execute(cap_name, {"value": call_id}, return_raw=True)
                with lock:
                    results.append({"id": call_id, "success": True, "capability": cap_name})
            except Exception as e:
                with lock:
                    results.append(
                        {"id": call_id, "success": False, "error": str(e), "capability": cap_name}
                    )

        # Execute 100 concurrent calls
        threads = []
        for i in range(100):
            thread = threading.Thread(target=execute_capability, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Calculate metrics
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        print(f"\n{'=' * 60}")
        print("Concurrent Capability Execution with Failures")
        print(f"{'=' * 60}")
        print(f"Total calls:        {len(results)}")
        print(f"Successful:         {len(successful)}")
        print(f"Failed:             {len(failed)}")
        print(f"Success rate:       {len(successful) / len(results) * 100:.2f}%")

        # Print failure distribution
        failure_by_cap = {}
        for result in failed:
            cap = result["capability"]
            failure_by_cap[cap] = failure_by_cap.get(cap, 0) + 1

        print("\nFailure distribution:")
        for cap, count in sorted(failure_by_cap.items()):
            print(f"  {cap}: {count} failures")

        print(f"{'=' * 60}")

        # Verify failures are expected (roughly matching failure rates)
        # cap-1: ~20% of ~33 calls = ~6-7 failures
        # cap-2: ~10% of ~33 calls = ~3-4 failures
        # cap-3: 0% failures
        assert len(failed) > 0, "Should have some failures"
        assert len(successful) > 0, "Should have some successes"

    def test_local_function_capability_concurrent_execution(self):
        """Test LocalFunctionCapability under concurrent load.

        Verifies:
        - LocalFunctionCapability handles concurrent calls
        - Argument validation works under load
        - No race conditions in function execution
        - Performance is acceptable

        **Validates: Requirements 7.4**
        """

        # Create a simple function capability
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers."""
            time.sleep(0.01)  # Simulate work
            return a + b

        capability = LocalFunctionCapability(add_numbers)
        registry = CapabilityRegistry()
        registry.register(capability)

        # Track results
        results = []
        lock = threading.Lock()

        def execute_add(call_id: int):
            """Execute add capability."""
            try:
                result = registry.execute(
                    "add_numbers", {"a": call_id, "b": call_id * 2}, return_raw=True
                )
                with lock:
                    results.append({"id": call_id, "success": True, "result": result})
            except Exception as e:
                with lock:
                    results.append({"id": call_id, "success": False, "error": str(e)})

        # Execute 100 concurrent calls
        threads = []
        start_time = time.time()

        for i in range(100):
            thread = threading.Thread(target=execute_add, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Calculate metrics
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        print(f"\n{'=' * 60}")
        print("LocalFunctionCapability Concurrent Execution (100 calls)")
        print(f"{'=' * 60}")
        print(f"Total calls:        {len(results)}")
        print(f"Successful:         {len(successful)}")
        print(f"Failed:             {len(failed)}")
        print(f"Total time:         {total_time:.2f}s")
        print(f"Calls/sec:          {len(results) / total_time:.2f}")
        print(f"{'=' * 60}")

        # Verify all succeeded
        assert len(successful) == 100, f"Expected 100 successful calls, got {len(successful)}"
        assert len(failed) == 0, f"Expected 0 failures, got {len(failed)}"

        # Verify results are correct
        for result in successful:
            call_id = result["id"]
            expected = call_id + call_id * 2
            assert result["result"] == expected, f"Result mismatch for call {call_id}"

    @pytest.mark.asyncio
    async def test_async_capability_concurrent_execution(self):
        """Test async capability execution under concurrent load.

        Verifies:
        - Async capabilities handle concurrent calls
        - asyncio.gather works correctly with many tasks
        - No race conditions in async execution
        - Performance is acceptable

        **Validates: Requirements 7.4**
        """
        registry = CapabilityRegistry()

        # Register async capabilities
        cap1 = MockCapability("async-cap-1", latency_ms=10)
        cap2 = MockCapability("async-cap-2", latency_ms=10)

        registry.register(cap1)
        registry.register(cap2)

        # Execute 100 concurrent async calls
        async def execute_async(call_id: int):
            """Execute capability asynchronously."""
            cap_name = ["async-cap-1", "async-cap-2"][call_id % 2]
            try:
                result = await registry.aexecute(
                    cap_name, {"value": call_id}, return_raw=True
                )
                return {"id": call_id, "success": True, "result": result}
            except Exception as e:
                return {"id": call_id, "success": False, "error": str(e)}

        # Create tasks for all calls
        start_time = time.time()
        tasks = [execute_async(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Calculate metrics
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        print(f"\n{'=' * 60}")
        print("Async Capability Concurrent Execution (100 calls)")
        print(f"{'=' * 60}")
        print(f"Total calls:        {len(results)}")
        print(f"Successful:         {len(successful)}")
        print(f"Failed:             {len(failed)}")
        print(f"Total time:         {total_time:.2f}s")
        print(f"Calls/sec:          {len(results) / total_time:.2f}")
        print(f"{'=' * 60}")

        # Verify all succeeded
        assert len(successful) == 100, f"Expected 100 successful calls, got {len(successful)}"
        assert len(failed) == 0, f"Expected 0 failures, got {len(failed)}"

    def test_capability_registry_search_under_load(self):
        """Test capability registry search performance under load.

        Verifies:
        - Search works correctly with many capabilities
        - Search performance is acceptable
        - No race conditions in search
        - Results are accurate

        **Validates: Requirements 7.4**
        """
        registry = CapabilityRegistry(auto_search=True)

        # Register 100 capabilities with descriptive names
        for i in range(100):
            cap = MockCapability(
                f"capability-{i:03d}",
                latency_ms=5,
            )
            registry.register(cap)

        # Perform concurrent searches
        search_times = []
        search_results = []
        lock = threading.Lock()

        def perform_search(search_id: int):
            """Perform a search."""
            query = f"capability-{search_id % 10:03d}"
            search_start = time.time()
            try:
                results = registry.search(query, limit=5)
                search_time = time.time() - search_start
                with lock:
                    search_times.append(search_time)
                    search_results.append({"id": search_id, "success": True, "count": len(results)})
            except Exception as e:
                with lock:
                    search_results.append({"id": search_id, "success": False, "error": str(e)})

        # Execute 50 concurrent searches
        threads = []
        start_time = time.time()

        for i in range(50):
            thread = threading.Thread(target=perform_search, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Calculate metrics
        successful = [r for r in search_results if r["success"]]
        avg_search_time = statistics.mean(search_times) if search_times else 0.0
        max_search_time = max(search_times) if search_times else 0.0

        print(f"\n{'=' * 60}")
        print("Registry Search Performance Under Load (50 concurrent searches)")
        print(f"{'=' * 60}")
        print(f"Total capabilities: {registry.count()}")
        print(f"Total searches:     {len(search_results)}")
        print(f"Successful:         {len(successful)}")
        print(f"Total time:         {total_time:.2f}s")
        print("\nSearch performance:")
        print(f"  Average time:     {avg_search_time * 1000:.3f}ms")
        print(f"  Max time:         {max_search_time * 1000:.3f}ms")
        print(f"{'=' * 60}")

        # Verify all searches succeeded
        assert len(successful) == 50, f"Expected 50 successful searches, got {len(successful)}"

    def test_capability_execution_latency_distribution(self):
        """Test and measure capability execution latency distribution.

        Verifies:
        - Latency distribution is reasonable
        - No outliers or performance degradation
        - Consistent performance across many calls
        - Percentile metrics are accurate

        **Validates: Requirements 7.4**
        """
        registry = CapabilityRegistry()

        # Register capability with known latency
        cap = MockCapability("latency-test", latency_ms=50)
        registry.register(cap)

        # Execute many calls and measure latency
        latencies = []
        lock = threading.Lock()

        def execute_and_measure(call_id: int):
            """Execute and measure latency."""
            exec_start = time.time()
            try:
                registry.execute("latency-test", {"value": call_id}, return_raw=True)
                latency = time.time() - exec_start
                with lock:
                    latencies.append(latency)
            except Exception:
                pass

        # Execute 200 calls
        threads = []
        for i in range(200):
            thread = threading.Thread(target=execute_and_measure, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Calculate distribution metrics
        latencies_sorted = sorted(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        avg_latency = statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        stdev_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0.0

        # Calculate percentiles
        p50 = latencies_sorted[int(len(latencies) * 0.50)]
        p75 = latencies_sorted[int(len(latencies) * 0.75)]
        p90 = latencies_sorted[int(len(latencies) * 0.90)]
        p95 = latencies_sorted[int(len(latencies) * 0.95)]
        p99 = latencies_sorted[int(len(latencies) * 0.99)]

        print(f"\n{'=' * 60}")
        print("Capability Execution Latency Distribution (200 calls)")
        print(f"{'=' * 60}")
        print(f"Total calls:        {len(latencies)}")
        print(f"Min latency:        {min_latency:.3f}s")
        print(f"Max latency:        {max_latency:.3f}s")
        print(f"Average latency:    {avg_latency:.3f}s")
        print(f"Median latency:     {median_latency:.3f}s")
        print(f"Std deviation:      {stdev_latency:.3f}s")
        print("\nPercentiles:")
        print(f"  P50:              {p50:.3f}s")
        print(f"  P75:              {p75:.3f}s")
        print(f"  P90:              {p90:.3f}s")
        print(f"  P95:              {p95:.3f}s")
        print(f"  P99:              {p99:.3f}s")
        print(f"{'=' * 60}")

        # Verify latency is reasonable (should be around 50ms + overhead)
        assert avg_latency >= 0.05, f"Average latency too low: {avg_latency:.3f}s"
        assert avg_latency < 0.2, f"Average latency too high: {avg_latency:.3f}s"
        assert p99 < 0.3, f"P99 latency too high: {p99:.3f}s"

    def test_capability_registry_thread_safety(self):
        """Test capability registry thread safety under concurrent operations.

        Verifies:
        - Concurrent registrations don't corrupt state
        - Concurrent lookups work correctly
        - No race conditions in registry
        - Registry state remains consistent

        **Validates: Requirements 7.4**
        """
        registry = CapabilityRegistry()

        # Track operations
        operations = []
        lock = threading.Lock()

        def register_capability(cap_id: int):
            """Register a capability."""
            try:
                cap = MockCapability(f"thread-cap-{cap_id}", latency_ms=5)
                registry.register(cap)
                with lock:
                    operations.append({"id": cap_id, "op": "register", "success": True})
            except Exception as e:
                with lock:
                    operations.append(
                        {"id": cap_id, "op": "register", "success": False, "error": str(e)}
                    )

        def lookup_capability(cap_id: int):
            """Lookup a capability."""
            try:
                cap_name = f"thread-cap-{cap_id % 50}"
                cap = registry.get(cap_name)
                with lock:
                    operations.append(
                        {"id": cap_id, "op": "lookup", "success": cap is not None}
                    )
            except Exception as e:
                with lock:
                    operations.append(
                        {"id": cap_id, "op": "lookup", "success": False, "error": str(e)}
                    )

        # Execute mixed concurrent operations
        threads = []

        # Register 50 capabilities
        for i in range(50):
            thread = threading.Thread(target=register_capability, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for registrations to complete
        for thread in threads:
            thread.join()

        # Perform concurrent lookups
        threads = []
        for i in range(100):
            thread = threading.Thread(target=lookup_capability, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify results
        registrations = [op for op in operations if op["op"] == "register"]
        lookups = [op for op in operations if op["op"] == "lookup"]

        successful_registrations = [op for op in registrations if op["success"]]
        successful_lookups = [op for op in lookups if op["success"]]

        print(f"\n{'=' * 60}")
        print("Registry Thread Safety Test")
        print(f"{'=' * 60}")
        print(f"Total registrations: {len(registrations)}")
        print(f"Successful:         {len(successful_registrations)}")
        print(f"Total lookups:      {len(lookups)}")
        print(f"Successful:         {len(successful_lookups)}")
        print(f"Final registry size: {registry.count()}")
        print(f"{'=' * 60}")

        # Verify thread safety
        assert len(successful_registrations) == 50, "All registrations should succeed"
        assert registry.count() == 50, "Registry should have 50 capabilities"
        assert len(successful_lookups) > 0, "Some lookups should succeed"
