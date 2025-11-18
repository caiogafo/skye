"""Advanced Nimbus Example - Implementing Interfaces.

This example demonstrates how to implement Nimbus interfaces:
- Creating a custom ModelInterface implementation
- Building a PromptBuilderInterface for templates
- Implementing a CapabilityInterface for tools
- Using ModelRouterInterface for load balancing
"""

import asyncio
from typing import Iterator, Any, Callable

from nimbus.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from nimbus.messages import UserMessage, AssistantMessage, SystemMessage, NimbusMessage
from nimbus.interfaces.model import ModelInterface
from nimbus.interfaces.prompt import PromptBuilderInterface
from nimbus.interfaces.capability import CapabilityInterface, CapabilitySchema
from nimbus.interfaces.router import ModelRouterInterface, RoutingStrategy


# ===== Model Interface Implementation =====

class MockModel(ModelInterface):
    """A mock model implementation for demonstration."""
    
    def __init__(self, model_name: str, provider: str = "mock"):
        self.model_name = model_name
        self.provider = provider
        self.call_count = 0
    
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Synchronous completion."""
        self.call_count += 1
        last_message = request.messages[-1].content
        response_content = f"[{self.model_name}] Echo: {last_message}"
        
        return CompletionResponse(
            model=self.model_name,
            provider=self.provider,
            content=response_content,
            finish_reason="stop",
            usage=TokenUsage(
                prompt_tokens=len(last_message.split()),
                completion_tokens=len(response_content.split()),
                total_tokens=len(last_message.split()) + len(response_content.split())
            )
        )
    
    def stream(self, request: CompletionRequest) -> Iterator[StreamChunk]:
        """Streaming completion."""
        response = self.complete(request)
        words = response.content.split()
        
        for i, word in enumerate(words):
            yield StreamChunk(id=f"stream_{self.call_count}", delta=word + " ", index=i)
        
        yield StreamChunk(id=f"stream_{self.call_count}", delta="", finish_reason="stop", index=len(words))
    
    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Async completion."""
        await asyncio.sleep(0.1)
        return self.complete(request)
    
    async def astream(self, request: CompletionRequest) -> Iterator[StreamChunk]:
        """Async streaming."""
        return self.stream(request)
    
    def get_model_info(self) -> dict:
        """Return model metadata."""
        return {
            "name": self.model_name,
            "provider": self.provider,
            "capabilities": ["completion", "streaming"],
            "call_count": self.call_count
        }


# ===== Capability Implementation =====

class CalculatorCapability(CapabilityInterface):
    """A simple calculator capability."""
    
    def get_schema(self) -> CapabilitySchema:
        """Return capability schema."""
        return CapabilitySchema(
            name="calculator",
            description="Perform basic arithmetic operations",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["operation", "a", "b"]
            },
            returns={"type": "number"}
        )
    
    def execute(self, **kwargs) -> Any:
        """Execute the calculation."""
        operation = kwargs.get("operation")
        a = kwargs.get("a", 0)
        b = kwargs.get("b", 0)
        
        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else None
        }
        
        return operations.get(operation, lambda x, y: None)(a, b)
    
    async def aexecute(self, **kwargs) -> Any:
        """Async execution."""
        return self.execute(**kwargs)


# ===== Router Implementation =====

class SimpleRouter(ModelRouterInterface):
    """A simple round-robin router."""
    
    def __init__(self):
        self.models = {}
        self.model_list = []
        self.current_index = 0
        self.strategy = RoutingStrategy.ROUND_ROBIN
    
    def register_model(self, model_id: str, model: Any) -> None:
        self.models[model_id] = model
        self.model_list.append(model_id)
    
    def select_model(self, request: CompletionRequest) -> str:
        if not self.model_list:
            raise ValueError("No models registered")
        model_id = self.model_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.model_list)
        return model_id
    
    def route_request(self, request: CompletionRequest) -> CompletionResponse:
        model_id = self.select_model(request)
        return self.models[model_id].complete(request)
    
    async def aroute_request(self, request: CompletionRequest) -> CompletionResponse:
        model_id = self.select_model(request)
        return await self.models[model_id].acomplete(request)
    
    def mark_model_failed(self, model_id: str) -> None:
        pass
    
    def get_model_health(self, model_id: str) -> dict[str, Any]:
        return {"status": "healthy"}
    
    def set_routing_strategy(self, strategy: RoutingStrategy) -> None:
        self.strategy = strategy
    
    def set_fallbacks(self, fallbacks: list[dict]) -> None:
        pass
    def set_retry_policy(self, retry_policy: dict[str, int]) -> None:
        pass
    def set_allowed_fails_policy(self, allowed_fails: dict[str, int]) -> None:
        pass
    def set_cooldown_time(self, cooldown_seconds: float) -> None:
        pass
    def enable_pre_call_checks(self, enabled: bool = True) -> None:
        pass
    def set_rate_limits(self, model_id: str, tpm: int | None = None, rpm: int | None = None) -> None:
        pass
    def get_usage_stats(self, model_id: str) -> dict:
        return {"tpm_used": 0, "rpm_used": 0}
    def get_cooldown_models(self) -> list[dict]:
        return []
    def set_model_tags(self, model_id: str, tags: list[str]) -> None:
        pass
    def route_with_tags(self, request: CompletionRequest, required_tags: list[str]) -> CompletionResponse:
        return self.route_request(request)


# ===== Examples =====

def model_interface_example():
    """Demonstrate ModelInterface usage."""
    print("=" * 60)
    print("ModelInterface Example")
    print("=" * 60)
    
    model = MockModel("mock-gpt-4", "mock-provider")
    request = CompletionRequest(
        messages=[UserMessage(content="Hello, how are you?")],
        model="mock-gpt-4"
    )
    
    response = model.complete(request)
    print(f"\nModel: {response.model}")
    print(f"Response: {response.content}")
    print(f"Tokens: {response.usage.total_tokens}")
    
    info = model.get_model_info()
    print(f"\nModel Info: {info['name']} ({info['provider']})")
    print(f"Calls made: {info['call_count']}")


def capability_example():
    """Demonstrate CapabilityInterface usage."""
    print("\n" + "=" * 60)
    print("CapabilityInterface Example")
    print("=" * 60)
    
    calc = CalculatorCapability()
    schema = calc.get_schema()
    
    print(f"\nCapability: {schema.name}")
    print(f"Description: {schema.description}")
    
    result = calc.execute(operation="add", a=5, b=3)
    print(f"\nCalculation: 5 + 3 = {result}")
    
    result = calc.execute(operation="multiply", a=4, b=7)
    print(f"Calculation: 4 × 7 = {result}")


def router_example():
    """Demonstrate ModelRouterInterface usage."""
    print("\n" + "=" * 60)
    print("ModelRouterInterface Example")
    print("=" * 60)
    
    router = SimpleRouter()
    router.register_model("model-1", MockModel("model-1"))
    router.register_model("model-2", MockModel("model-2"))
    router.register_model("model-3", MockModel("model-3"))
    
    request = CompletionRequest(
        messages=[UserMessage(content="Test message")],
        model="any"
    )
    
    print("\nRouting 5 requests (round-robin):")
    for i in range(5):
        response = router.route_request(request)
        print(f"  Request {i+1} → {response.model}")


async def async_example():
    """Demonstrate async operations."""
    print("\n" + "=" * 60)
    print("Async Operations Example")
    print("=" * 60)
    
    model = MockModel("async-model")
    request = CompletionRequest(
        messages=[UserMessage(content="Async test")],
        model="async-model"
    )
    
    print("\nExecuting async completion...")
    response = await model.acomplete(request)
    print(f"Response: {response.content}")


def main():
    """Run all examples."""
    print("\n" + "🚀 " * 20)
    print("NIMBUS - Interface Implementation Examples")
    print("🚀 " * 20 + "\n")
    
    model_interface_example()
    capability_example()
    router_example()
    asyncio.run(async_example())
    
    print("\n" + "=" * 60)
    print("✅ All interface examples completed!")
    print("=" * 60)
    print("\nThese examples show how to:")
    print("  ✓ Implement ModelInterface for custom providers")
    print("  ✓ Create CapabilityInterface for tool calling")
    print("  ✓ Use ModelRouterInterface for load balancing")
    print("  ✓ Handle async operations")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
