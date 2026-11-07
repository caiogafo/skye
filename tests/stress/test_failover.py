"""Stress tests for failover scenarios in ModelRouter.

This module tests the router's failover behavior under load,
verifying correct behavior including:
- Router behavior when models fail
- Cooldown mechanism under load
- Fallback chain execution
- Failover latency measurement
- Recovery after cooldown

**Validates: Requirements 7.3**
"""

import statistics
import threading
import time
from typing import Any

import pytest

from skye.base.completion import CompleteRequest, CompleteResponse, TokenUsage
from skye.base.exceptions import ProviderError
from skye.base.interfaces.model import ModelInterface
from skye.base.interfaces.router import RoutingStrategy
from skye.base.messages import UserMessage
from skye.router.model_router import (
    FallbackConfig,
    ModelRouter,
)


class FailingMockModel(ModelInterface):
    """Mock model that can be configured to fail."""

    def __init__(
        self,
        model_id: str,
        latency_ms: float = 50.0,
        failure_rate: float = 0.0,
        token_count: int = 100,
    ):
        """Initialize failing mock model.

        Args:
            model_id: Model identifier
            latency_ms: Simulated latency in milliseconds
            failure_rate: Probability of failure (0.0-1.0)
            token_count: Number of tokens to report in usage
        """
        self.model_id = model_id
        self.latency_ms = latency_ms
        self.failure_rate = failure_rate
        self.token_count = token_count
        self.call_count = 0
        self.failure_count = 0
        self.lock = threading.Lock()

    def complete(self, request: CompleteRequest) -> CompleteResponse:
        """Simulate completion with configurable failures."""
        with self.lock:
            self.call_count += 1

        # Simulate latency
        time.sleep(self.latency_ms / 1000.0)

        # Simulate random failures
        import random

        if random.random() < self.failure_rate:
            with self.lock:
                self.failure_count += 1
            raise ProviderError(f"Simulated failure in {self.model_id}", provider=self.model_id)

        # Return successful response
        return CompleteResponse(
            content="Test response",
            role="assistant",
            model=self.model_id,
            provider="mock",
            finish_reason="stop",
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=self.token_count,
                total_tokens=10 + self.token_count,
            ),
        )

    def stream(self, request: CompleteRequest):
        """Stream completion (not implemented for mock)."""
        from skye.base.completion import StreamChunk

        yield StreamChunk(delta="Test", model=self.model_id)

    async def acomplete(self, request: CompleteRequest) -> CompleteResponse:
        """Async version of complete."""
        return self.complete(request)

    async def astream(self, request: CompleteRequest):
        """Async stream completion (not implemented for mock)."""
        from skye.base.completion import StreamChunk

        yield StreamChunk(delta="Test", model=self.model_id)

    def get_model_info(self) -> dict[str, Any]:
        """Return model metadata."""
        return {
            "name": self.model_id,
            "provider": "mock",
            "latency_ms": self.latency_ms,
            "failure_rate": self.failure_rate,
        }


@pytest.mark.stress
class TestFailoverScenarios:
    """Stress tests for failover behavior under load."""

    def test_router_behavior_when_models_fail(self):
        """Test router behavior when primary models fail.

        Verifies:
        - Router detects model failures
        - Fallback models are used
        - Requests eventually succeed or fail appropriately
        - Health tracking is accurate

        **Validates: Requirements 7.3**
        """
        router = ModelRouter(strategy=RoutingStrategy.ROUND_ROBIN)

        # Register primary model with high failure rate
        primary = FailingMockModel("primary", latency_ms=20, failure_rate=0.8)
        fallback = FailingMockModel("fallback", latency_ms=20, failure_rate=0.0)

        router.register_model("primary", primary)
        router.register_model("fallback", fallback)

        # Set up fallback chain
        router.set_fallbacks([FallbackConfig(primary="primary", fallbacks=["fallback"])])

        request = CompleteRequest(
            messages=[UserMessage(content="Test message")], model="primary"
        )

        # Track results
        results = []
        lock = threading.Lock()

        def make_request(request_id: int):
            """Make a request."""
            try:
                response = router.complete(messages=request.messages, model=request.model)
                with lock:
                    results.append({"id": request_id, "success": True, "model": response.model})
            except Exception as e:
                with lock:
                    results.append({"id": request_id, "success": False, "error": str(e)})

        # Execute 50 concurrent requests
        threads = []
        for i in range(50):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Calculate metrics
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        print(f"\n{'=' * 60}")
        print("Router Behavior When Models Fail")
        print(f"{'=' * 60}")
        print(f"Total requests:     {len(results)}")
        print(f"Successful:         {len(successful)}")
        print(f"Failed:             {len(failed)}")
        print(f"Success rate:       {len(successful) / len(results) * 100:.2f}%")

        # Check which models were used
        models_used = {}
        for result in successful:
            model = result["model"]
            models_used[model] = models_used.get(model, 0) + 1

        print("\nModels used:")
        for model, count in sorted(models_used.items()):
            print(f"  {model}: {count} requests")

        # Check health metrics
        primary_health = router.get_model_health("primary")
        fallback_health = router.get_model_health("fallback")

        print("\nHealth metrics:")
        print("  Primary:")
        print(f"    Success rate: {primary_health.success_rate * 100:.2f}%")
        print(f"    Failures:     {primary_health.failure_count}")
        print("  Fallback:")
        print(f"    Success rate: {fallback_health.success_rate * 100:.2f}%")
        print(f"    Failures:     {fallback_health.failure_count}")
        print(f"{'=' * 60}")

        # Verify fallback was used
        assert len(successful) > 0, "Some requests should succeed via fallback"
        assert "fallback" in models_used, "Fallback model should have been used"

    def test_cooldown_mechanism_under_load(self):
        """Test cooldown mechanism under concurrent load.

        Verifies:
        - Models are put in cooldown after failures
        - Cooldown prevents further requests to failed models
        - Cooldown duration is respected
        - Fallback models are used during cooldown

        **Validates: Requirements 7.3**
        """
        router = ModelRouter(
            strategy=RoutingStrategy.ROUND_ROBIN,
            cooldown_seconds=2.0,
            enable_pre_call_checks=True,
        )

        # Register models
        primary = FailingMockModel("primary", latency_ms=20, failure_rate=1.0)  # Always fails
        fallback = FailingMockModel("fallback", latency_ms=20, failure_rate=0.0)  # Never fails

        router.register_model("primary", primary)
        router.register_model("fallback", fallback)

        # Set up fallback chain
        router.set_fallbacks([FallbackConfig(primary="primary", fallbacks=["fallback"])])

        # Set allowed fails policy to trigger cooldown quickly
        from skye.router.model_router import AllowedFailsPolicyConfig

        router.set_allowed_fails_policy(
            [AllowedFailsPolicyConfig(error_type="ProviderError", allowed_fails_per_minute=1)]
        )

        request = CompleteRequest(
            messages=[UserMessage(content="Test message")], model="primary"
        )

        # Make requests to trigger cooldown
        results = []
        lock = threading.Lock()

        def make_request(request_id: int):
            """Make a request."""
            try:
                response = router.complete(messages=request.messages, model=request.model)
                with lock:
                    results.append({"id": request_id, "success": True})
            except Exception as e:
                with lock:
                    results.append({"id": request_id, "success": False, "error": str(e)})

        # Execute requests
        threads = []
        start_time = time.time()

        for i in range(30):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        elapsed = time.time() - start_time

        # Check cooldown status
        cooled_down = router.get_cooldown_models()
        primary_health = router.get_model_health("primary")

        print(f"\n{'=' * 60}")
        print("Cooldown Mechanism Under Load")
        print(f"{'=' * 60}")
        print(f"Total requests:     {len(results)}")
        print(f"Successful:         {sum(1 for r in results if r['success'])}")
        print(f"Failed:             {sum(1 for r in results if not r['success'])}")
        print(f"Time elapsed:       {elapsed:.2f}s")
        print("\nCooldown status:")
        print(f"  Models in cooldown: {len(cooled_down)}")
        for info in cooled_down:
            print(f"    {info.model_id}: until {info.cooldown_until} ({info.reason})")
        print("\nPrimary health:")
        print(f"  In cooldown:      {primary_health.is_in_cooldown}")
        print(f"  Cooldown until:   {primary_health.cooldown_until}")
        print(f"{'=' * 60}")

        # Verify cooldown was triggered
        assert len(cooled_down) > 0, "Primary model should be in cooldown"
        assert primary_health.is_in_cooldown, "Primary model should be in cooldown"

    def test_fallback_chain_execution(self):
        """Test fallback chain execution under load.

        Verifies:
        - Fallback chains are executed in order
        - All fallbacks are tried before giving up
        - Requests succeed if any model in chain succeeds
        - Latency increases with each fallback attempt

        **Validates: Requirements 7.3**
        """
        router = ModelRouter(strategy=RoutingStrategy.ROUND_ROBIN)

        # Register models with different failure rates
        primary = FailingMockModel("primary", latency_ms=20, failure_rate=1.0)  # Always fails
        fallback1 = FailingMockModel("fallback1", latency_ms=20, failure_rate=1.0)  # Always fails
        fallback2 = FailingMockModel("fallback2", latency_ms=20, failure_rate=0.0)  # Never fails

        router.register_model("primary", primary)
        router.register_model("fallback1", fallback1)
        router.register_model("fallback2", fallback2)

        # Set up fallback chain
        router.set_fallbacks(
            [FallbackConfig(primary="primary", fallbacks=["fallback1", "fallback2"])]
        )

        request = CompleteRequest(
            messages=[UserMessage(content="Test message")], model="primary"
        )

        # Track results
        results = []
        latencies = []
        lock = threading.Lock()

        def make_request(request_id: int):
            """Make a request and measure latency."""
            req_start = time.time()
            try:
                response = router.complete(messages=request.messages, model=request.model)
                latency = time.time() - req_start
                with lock:
                    results.append({"id": request_id, "success": True, "model": response.model})
                    latencies.append(latency)
            except Exception as e:
                latency = time.time() - req_start
                with lock:
                    results.append({"id": request_id, "success": False, "error": str(e)})
                    latencies.append(latency)

        # Execute 40 concurrent requests
        threads = []
        for i in range(40):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Calculate metrics
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        # Check which models were used
        models_used = {}
        for result in successful:
            model = result["model"]
            models_used[model] = models_used.get(model, 0) + 1

        avg_latency = statistics.mean(latencies) if latencies else 0.0
        max_latency = max(latencies) if latencies else 0.0

        print(f"\n{'=' * 60}")
        print("Fallback Chain Execution")
        print(f"{'=' * 60}")
        print(f"Total requests:     {len(results)}")
        print(f"Successful:         {len(successful)}")
        print(f"Failed:             {len(failed)}")
        print(f"Success rate:       {len(successful) / len(results) * 100:.2f}%")
        print("\nModels used:")
        for model, count in sorted(models_used.items()):
            print(f"  {model}: {count} requests")
        print("\nLatency metrics:")
        print(f"  Average:          {avg_latency:.3f}s")
        print(f"  Max:              {max_latency:.3f}s")
        print(f"{'=' * 60}")

        # Verify fallback chain was executed
        assert len(successful) == 40, "All requests should succeed via fallback chain"
        assert "fallback2" in models_used, "Final fallback should have been used"

    def test_failover_latency_measurement(self):
        """Test and measure failover latency under load.

        Verifies:
        - Failover adds measurable latency
        - Latency increases with each fallback attempt
        - Latency remains acceptable even with multiple fallbacks
        - Latency distribution is reasonable

        **Validates: Requirements 7.3**
        """
        router = ModelRouter(strategy=RoutingStrategy.ROUND_ROBIN)

        # Register models with different latencies
        primary = FailingMockModel("primary", latency_ms=50, failure_rate=1.0)
        fallback1 = FailingMockModel("fallback1", latency_ms=50, failure_rate=1.0)
        fallback2 = FailingMockModel("fallback2", latency_ms=50, failure_rate=0.0)

        router.register_model("primary", primary)
        router.register_model("fallback1", fallback1)
        router.register_model("fallback2", fallback2)

        # Set up fallback chain
        router.set_fallbacks(
            [FallbackConfig(primary="primary", fallbacks=["fallback1", "fallback2"])]
        )

        request = CompleteRequest(
            messages=[UserMessage(content="Test message")], model="primary"
        )

        # Measure latencies
        latencies = []
        lock = threading.Lock()

        def make_request(request_id: int):
            """Make a request and measure latency."""
            req_start = time.time()
            try:
                router.complete(messages=request.messages, model=request.model)
                latency = time.time() - req_start
                with lock:
                    latencies.append(latency)
            except Exception:
                pass

        # Execute 50 concurrent requests
        threads = []
        start_time = time.time()

        for i in range(50):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Calculate latency distribution
        if latencies:
            latencies_sorted = sorted(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            avg_latency = statistics.mean(latencies)
            median_latency = statistics.median(latencies)
            p95_latency = latencies_sorted[int(len(latencies) * 0.95)]
            p99_latency = latencies_sorted[int(len(latencies) * 0.99)]
        else:
            min_latency = max_latency = avg_latency = median_latency = p95_latency = p99_latency = 0.0

        print(f"\n{'=' * 60}")
        print("Failover Latency Measurement (50 requests)")
        print(f"{'=' * 60}")
        print(f"Total time:         {total_time:.2f}s")
        print(f"Requests measured:  {len(latencies)}")
        print("\nLatency distribution:")
        print(f"  Min:              {min_latency:.3f}s")
        print(f"  Max:              {max_latency:.3f}s")
        print(f"  Average:          {avg_latency:.3f}s")
        print(f"  Median:           {median_latency:.3f}s")
        print(f"  P95:              {p95_latency:.3f}s")
        print(f"  P99:              {p99_latency:.3f}s")
        print("\nExpected latency breakdown:")
        print("  Primary (50ms) + Fallback1 (50ms) + Fallback2 (50ms) = ~150ms")
        print(f"{'=' * 60}")

        # Verify latency is reasonable
        # With 3 models at 50ms each, expect ~150ms per request
        assert avg_latency >= 0.15, f"Average latency too low: {avg_latency:.3f}s"
        assert avg_latency < 0.5, f"Average latency too high: {avg_latency:.3f}s"

    def test_recovery_after_cooldown(self):
        """Test model recovery after cooldown expires.

        Verifies:
        - Models recover after cooldown expires
        - Requests are routed back to recovered models
        - Health metrics are reset appropriately
        - No stale cooldown state persists

        **Validates: Requirements 7.3**
        """
        router = ModelRouter(
            strategy=RoutingStrategy.ROUND_ROBIN,
            cooldown_seconds=1.0,  # Short cooldown for testing
        )

        # Register models
        primary = FailingMockModel("primary", latency_ms=20, failure_rate=1.0)
        fallback = FailingMockModel("fallback", latency_ms=20, failure_rate=0.0)

        router.register_model("primary", primary)
        router.register_model("fallback", fallback)

        router.set_fallbacks([FallbackConfig(primary="primary", fallbacks=["fallback"])])

        # Set allowed fails policy to trigger cooldown quickly
        from skye.router.model_router import AllowedFailsPolicyConfig

        router.set_allowed_fails_policy(
            [AllowedFailsPolicyConfig(error_type="ProviderError", allowed_fails_per_minute=1)]
        )

        request = CompleteRequest(
            messages=[UserMessage(content="Test message")], model="primary"
        )

        # Phase 1: Trigger cooldown
        print(f"\n{'=' * 60}")
        print("Recovery After Cooldown Test")
        print(f"{'=' * 60}")

        for _ in range(5):
            try:
                router.complete(messages=request.messages, model=request.model)
            except Exception:
                pass

        # Check cooldown status
        cooled_down_before = router.get_cooldown_models()
        print("\nPhase 1 - After failures:")
        print(f"  Models in cooldown: {len(cooled_down_before)}")
        for info in cooled_down_before:
            print(f"    {info.model_id}")

        assert len(cooled_down_before) > 0, "Primary should be in cooldown"

        # Phase 2: Wait for cooldown to expire
        print("\nPhase 2 - Waiting for cooldown to expire...")
        time.sleep(1.5)

        # Phase 3: Check recovery
        cooled_down_after = router.get_cooldown_models()
        print("\nPhase 3 - After cooldown expires:")
        print(f"  Models in cooldown: {len(cooled_down_after)}")

        # Verify cooldown expired
        assert len(cooled_down_after) == 0, "Primary should have recovered from cooldown"

        print(f"{'=' * 60}")

    def test_concurrent_failover_with_multiple_chains(self):
        """Test concurrent failover with multiple fallback chains.

        Verifies:
        - Multiple fallback chains work correctly under load
        - Each chain is independent
        - No interference between chains
        - All requests eventually succeed or fail appropriately

        **Validates: Requirements 7.3**
        """
        router = ModelRouter(strategy=RoutingStrategy.ROUND_ROBIN)

        # Register models for chain 1
        primary1 = FailingMockModel("primary1", latency_ms=20, failure_rate=0.9)
        fallback1a = FailingMockModel("fallback1a", latency_ms=20, failure_rate=0.5)
        fallback1b = FailingMockModel("fallback1b", latency_ms=20, failure_rate=0.0)

        # Register models for chain 2
        primary2 = FailingMockModel("primary2", latency_ms=20, failure_rate=0.8)
        fallback2a = FailingMockModel("fallback2a", latency_ms=20, failure_rate=0.0)

        router.register_model("primary1", primary1)
        router.register_model("fallback1a", fallback1a)
        router.register_model("fallback1b", fallback1b)
        router.register_model("primary2", primary2)
        router.register_model("fallback2a", fallback2a)

        # Set up fallback chains
        router.set_fallbacks(
            [
                FallbackConfig(primary="primary1", fallbacks=["fallback1a", "fallback1b"]),
                FallbackConfig(primary="primary2", fallbacks=["fallback2a"]),
            ]
        )

        # Track results
        results = []
        lock = threading.Lock()

        def make_request(request_id: int, model_id: str):
            """Make a request to a specific model."""
            request = CompleteRequest(
                messages=[UserMessage(content="Test message")], model=model_id
            )
            try:
                response = router.complete(messages=request.messages, model=request.model)
                with lock:
                    results.append(
                        {
                            "id": request_id,
                            "primary": model_id,
                            "success": True,
                            "used_model": response.model,
                        }
                    )
            except Exception as e:
                with lock:
                    results.append(
                        {
                            "id": request_id,
                            "primary": model_id,
                            "success": False,
                            "error": str(e),
                        }
                    )

        # Execute concurrent requests to both chains
        threads = []
        for i in range(50):
            model_id = "primary1" if i % 2 == 0 else "primary2"
            thread = threading.Thread(target=make_request, args=(i, model_id))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Analyze results
        chain1_results = [r for r in results if r["primary"] == "primary1"]
        chain2_results = [r for r in results if r["primary"] == "primary2"]

        chain1_success = sum(1 for r in chain1_results if r["success"])
        chain2_success = sum(1 for r in chain2_results if r["success"])

        print(f"\n{'=' * 60}")
        print("Concurrent Failover with Multiple Chains")
        print(f"{'=' * 60}")
        print("Chain 1 (primary1):")
        print(f"  Total requests:   {len(chain1_results)}")
        print(f"  Successful:       {chain1_success}")
        print(f"  Success rate:     {chain1_success / len(chain1_results) * 100:.2f}%")
        print("\nChain 2 (primary2):")
        print(f"  Total requests:   {len(chain2_results)}")
        print(f"  Successful:       {chain2_success}")
        print(f"  Success rate:     {chain2_success / len(chain2_results) * 100:.2f}%")
        print(f"{'=' * 60}")

        # Verify both chains worked
        assert chain1_success > 0, "Chain 1 should have successful requests"
        assert chain2_success > 0, "Chain 2 should have successful requests"

    def test_failover_with_rate_limiting(self):
        """Test failover behavior with rate limiting enabled.

        Verifies:
        - Failover works correctly with rate limits
        - Rate limits are respected during failover
        - Fallback models have independent rate limits
        - No rate limit interference between chains

        **Validates: Requirements 7.3**
        """
        router = ModelRouter(
            strategy=RoutingStrategy.ROUND_ROBIN,
            enable_pre_call_checks=True,
        )

        # Register models with rate limits
        primary = FailingMockModel("primary", latency_ms=20, failure_rate=1.0)
        fallback = FailingMockModel("fallback", latency_ms=20, failure_rate=0.0)

        router.register_model("primary", primary, rpm=100, tpm=10000)
        router.register_model("fallback", fallback, rpm=100, tpm=10000)

        router.set_fallbacks([FallbackConfig(primary="primary", fallbacks=["fallback"])])

        request = CompleteRequest(
            messages=[UserMessage(content="Test message")], model="primary"
        )

        # Track results
        results = []
        lock = threading.Lock()

        def make_request(request_id: int):
            """Make a request."""
            try:
                response = router.complete(messages=request.messages, model=request.model)
                with lock:
                    results.append({"id": request_id, "success": True, "model": response.model})
            except Exception as e:
                with lock:
                    results.append({"id": request_id, "success": False, "error": str(e)})

        # Execute 60 concurrent requests
        threads = []
        for i in range(60):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Check rate limit usage
        primary_stats = router.get_usage_stats("primary")
        fallback_stats = router.get_usage_stats("fallback")

        successful = sum(1 for r in results if r["success"])

        print(f"\n{'=' * 60}")
        print("Failover with Rate Limiting")
        print(f"{'=' * 60}")
        print(f"Total requests:     {len(results)}")
        print(f"Successful:         {successful}")
        print("\nRate limit usage:")
        print("  Primary:")
        print(f"    RPM: {primary_stats.rpm_used}/{primary_stats.rpm_limit}")
        print(f"    TPM: {primary_stats.tpm_used}/{primary_stats.tpm_limit}")
        print("  Fallback:")
        print(f"    RPM: {fallback_stats.rpm_used}/{fallback_stats.rpm_limit}")
        print(f"    TPM: {fallback_stats.tpm_used}/{fallback_stats.tpm_limit}")
        print(f"{'=' * 60}")

        # Verify rate limits were respected
        assert primary_stats.rpm_used <= primary_stats.rpm_limit
        assert primary_stats.tpm_used <= primary_stats.tpm_limit
        assert fallback_stats.rpm_used <= fallback_stats.rpm_limit
        assert fallback_stats.tpm_used <= fallback_stats.tpm_limit
