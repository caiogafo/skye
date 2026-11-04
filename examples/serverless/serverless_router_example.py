#!/usr/bin/env python3
"""
Example: Using ModelRouter with external storage backends for serverless environments.

This example demonstrates how to use the ModelRouter with different storage backends
to maintain state across serverless function invocations.
"""

import asyncio
from skye.router import ModelRouter, ModelTarget, RouteConfig
from skye.store import (
    InMemoryBackend,
    RedisBackend,
    DynamoDBBackend,
    PostgreSQLBackend,
    FileSystemBackend,
    DurableFunctionBackend,
)
from skye.router import RoutingStrategy
from skye import CompletionRequest
from skye import UserMessage


def example_in_memory_storage():
    """Example using in-memory storage (default)."""
    print("=== In-Memory Storage Example ===")
    
    # Default behavior - uses in-memory storage
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="gpt-3.5-turbo",
                targets=[
                    ModelTarget(
                        model="gpt-3.5-turbo",
                        provider="openai",
                        api_key="${OPENAI_API_KEY}",
                        tpm=200000,
                        rpm=2000
                    )
                ],
                strategy=RoutingStrategy.RATE_LIMIT_AWARE
            )
        ]
    )
    
    print(f"Router created with storage: {type(router.storage_backend).__name__}")
    print(f"Available aliases: {router.list_aliases()}")


def example_redis_storage():
    """Example using Redis storage for distributed environments."""
    print("\n=== Redis Storage Example ===")
    
    # Use Redis for persistent state
    redis_storage = RedisBackend(
        redis_url="redis://localhost:6379",
        key_prefix="skye:prod:"
    )
    
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="gpt-4",
                targets=[
                    ModelTarget(
                        model="gpt-4",
                        provider="openai",
                        api_key="${OPENAI_API_KEY}",
                        tpm=100000,
                        rpm=1000
                    )
                ]
            )
        ],
        storage=redis_storage
    )
    
    print(f"Router created with storage: {type(router.storage_backend).__name__}")
    print("State will persist across function invocations via Redis")


def example_dynamodb_storage():
    """Example using DynamoDB storage for AWS serverless."""
    print("\n=== DynamoDB Storage Example ===")
    
    # Use DynamoDB for AWS serverless environments
    dynamodb_storage = DynamoDBBackend(
        table_name="skye-router-state",
        region_name="us-east-1"
    )
    
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="claude-3",
                targets=[
                    ModelTarget(
                        model="claude-3-sonnet-20240229",
                        provider="anthropic",
                        api_key="${ANTHROPIC_API_KEY}",
                        tpm=150000,
                        rpm=1500
                    )
                ]
            )
        ],
        storage=dynamodb_storage
    )
    
    print(f"Router created with storage: {type(router.storage_backend).__name__}")
    print("State will persist in DynamoDB table: skye-router-state")


def example_postgresql_storage():
    """Example using PostgreSQL storage."""
    print("\n=== PostgreSQL Storage Example ===")
    
    # Use PostgreSQL for persistent database storage
    postgres_storage = PostgreSQLBackend(
        connection_string="postgresql://user:password@localhost:5432/skye",
        table_name="router_state"
    )
    
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="mixed-models",
                targets=[
                    ModelTarget(
                        model="gpt-4",
                        provider="openai",
                        api_key="${OPENAI_API_KEY}",
                        tpm=100000,
                        rpm=1000
                    ),
                    ModelTarget(
                        model="claude-3-sonnet-20240229",
                        provider="anthropic",
                        api_key="${ANTHROPIC_API_KEY}",
                        tpm=150000,
                        rpm=1500
                    )
                ],
                strategy=RoutingStrategy.RATE_LIMIT_AWARE
            )
        ],
        storage=postgres_storage
    )
    
    print(f"Router created with storage: {type(router.storage_backend).__name__}")
    print("State will persist in PostgreSQL database")


def example_filesystem_storage():
    """Example using file system storage."""
    print("\n=== File System Storage Example ===")
    
    # Use file system for local persistent storage
    fs_storage = FileSystemBackend(base_path="/tmp/skye_router_state")
    
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="local-models",
                targets=[
                    ModelTarget(
                        model="llama-2-7b",
                        provider="openai",  # any OpenAI-compatible server (vLLM, Ollama, ...)
                        api_key="not-needed",
                        api_base="http://localhost:8000/v1",
                        tpm=50000,
                        rpm=500
                    )
                ]
            )
        ],
        storage=fs_storage
    )
    
    print(f"Router created with storage: {type(router.storage_backend).__name__}")
    print("State will persist in /tmp/skye_router_state directory")


def example_durable_function_storage():
    """Example using AWS Durable Function storage."""
    print("\n=== Durable Function Storage Example ===")
    
    # This would be used inside an AWS Lambda with Durable Execution SDK
    # from aws_durable_execution_sdk import DurableContext, durable_execution
    
    # @durable_execution
    # def lambda_handler(event, context: DurableContext):
    #     # Use durable context for state persistence
    #     durable_storage = DurableFunctionBackend(context)
    #     
    #     router = ModelRouter(
    #         routes=[...],
    #         storage=durable_storage
    #     )
    #     
    #     # Process requests with persistent state
    #     return router.complete(
    #         messages=request.messages,
    #         model=request.model
    #     )
    
    print("Durable Function storage integrates with AWS Durable Execution SDK")
    print("State persists across workflow steps and retries")


async def example_explicit_initialization():
    """Example showing that storage initialization happens automatically."""
    print("\n=== Automatic Storage Initialization Example ===")
    
    # Create the storage backend (a file system backend here; Redis or DynamoDB work the same way)
    redis_storage = FileSystemBackend(base_path="/tmp/skye_router_state")
    
    # Create router - connect() is called automatically during initialization
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="auto-initialized-model",
                targets=[
                    ModelTarget(
                        model="gpt-3.5-turbo",
                        provider="openai",
                        api_key="${OPENAI_API_KEY}",
                        tpm=200000,
                        rpm=2000
                    )
                ]
            )
        ],
        storage=redis_storage
    )
    
    print("✅ Router created - storage backend connect() called automatically")
    print("No need to manually call storage.connect() - it's handled internally")


async def example_async_usage():
    """Example showing async usage with external storage."""
    print("\n=== Async Usage Example ===")
    
    # Create router with an external storage backend (a file system backend here; Redis or DynamoDB work the same way)
    redis_storage = FileSystemBackend(base_path="/tmp/skye_router_state")
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="async-model",
                targets=[
                    ModelTarget(
                        model="gpt-3.5-turbo",
                        provider="openai",
                        api_key="${OPENAI_API_KEY}",
                        tpm=200000,
                        rpm=2000
                    )
                ]
            )
        ],
        storage=redis_storage
    )
    
    # Create a sample request
    request = CompletionRequest(
        messages=[UserMessage(content="Hello, world!")],
        model="async-model"
    )
    
    try:
        # Use async routing (recommended for external storage)
        response = await router.acomplete(messages=request.messages, model=request.model)
        print(f"Async response received: {response.content[:50]}...")
        
        # Get health metrics asynchronously
        health = await router.aget_model_health("async-model:openai:gpt-3.5-turbo")
        print(f"Model health - Success rate: {health.success_rate:.1%}")
        
    except Exception as e:
        print(f"Request failed: {e}")


def main():
    """Run all examples."""
    print("Skye Router Storage Backend Examples")
    print("=" * 50)
    
    # Run sync examples. A backend whose library is not installed is skipped with a hint:
    # Redis comes with the `memory` extra (pip install skyeai[memory]), PostgreSQL with the `postgres` extra, DynamoDB needs boto3.
    import importlib.util

    for example, needs, install in (
        (example_in_memory_storage, None, None),
        (example_redis_storage, "redis", "pip install skyeai[memory]"),
        (example_dynamodb_storage, "boto3", "pip install boto3"),
        (example_postgresql_storage, "asyncpg", "pip install skyeai[postgres]"),
        (example_filesystem_storage, None, None),
        (example_durable_function_storage, None, None),
    ):
        if needs and importlib.util.find_spec(needs) is None:
            print(f"\n  skipped {example.__name__}: `{needs}` is not installed ({install})")
            continue
        try:
            example()
        except ImportError as e:
            print(f"  skipped ({example.__name__}): {e}")
    
    # Run async examples
    print("\nRunning async examples...")
    try:
        asyncio.run(example_explicit_initialization())
        asyncio.run(example_async_usage())
    except Exception as e:
        print(f"Async examples failed (expected without real backends): {e}")
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nKey Benefits:")
    print("- In-memory: Fast, no dependencies, good for single-instance apps")
    print("- Redis: Distributed, fast, good for microservices")
    print("- DynamoDB: Serverless, managed, good for AWS Lambda")
    print("- PostgreSQL: ACID compliance, complex queries, good for traditional apps")
    print("- FileSystem: Simple persistence, good for local development")
    print("- DurableFunction: Workflow persistence, good for AWS Step Functions")
    print("\nStorage Initialization:")
    print("- connect() method is called automatically during ModelRouter initialization")
    print("- No need to manually initialize storage backends")
    print("- Works seamlessly with all storage backend types")


if __name__ == "__main__":
    main()