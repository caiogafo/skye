#!/usr/bin/env python3
"""
Example: Using ModelRouter with external storage backends for serverless environments.

This example demonstrates how to use the ModelRouter with different storage backends
to maintain state across serverless function invocations.
"""

import asyncio
from nimbus.routes import ModelRouter, ModelTarget, RouteConfig
from nimbus.routes.storage_backends import (
    InMemoryBackend,
    RedisBackend,
    DynamoDBBackend,
    PostgreSQLBackend,
    FileSystemBackend,
    DurableFunctionBackend,
)
from nimbus.interfaces.router import RoutingStrategy
from nimbus.completion import CompletionRequest
from nimbus.messages import UserMessage


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
        key_prefix="nimbus:prod:"
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
        table_name="nimbus-router-state",
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
    print("State will persist in DynamoDB table: nimbus-router-state")


def example_postgresql_storage():
    """Example using PostgreSQL storage."""
    print("\n=== PostgreSQL Storage Example ===")
    
    # Use PostgreSQL for persistent database storage
    postgres_storage = PostgreSQLBackend(
        connection_string="postgresql://user:password@localhost:5432/nimbus",
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
    fs_storage = FileSystemBackend(base_path="/tmp/nimbus_router_state")
    
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="local-models",
                targets=[
                    ModelTarget(
                        model="llama-2-7b",
                        provider="local",
                        api_base="http://localhost:8000",
                        tpm=50000,
                        rpm=500
                    )
                ]
            )
        ],
        storage=fs_storage
    )
    
    print(f"Router created with storage: {type(router.storage_backend).__name__}")
    print("State will persist in /tmp/nimbus_router_state directory")


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
    #     return router.route_request(request)
    
    print("Durable Function storage integrates with AWS Durable Execution SDK")
    print("State persists across workflow steps and retries")


async def example_explicit_initialization():
    """Example showing that storage initialization happens automatically."""
    print("\n=== Automatic Storage Initialization Example ===")
    
    # Create storage backend
    redis_storage = RedisBackend("redis://localhost:6379")
    
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
    
    # Create router with Redis storage
    redis_storage = RedisBackend("redis://localhost:6379")
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
        response = await router.aroute_request(request)
        print(f"Async response received: {response.content[:50]}...")
        
        # Get health metrics asynchronously
        health = await router.aget_model_health("async-model:openai:gpt-3.5-turbo")
        print(f"Model health - Success rate: {health.success_rate:.1%}")
        
    except Exception as e:
        print(f"Request failed (expected in demo): {e}")


def main():
    """Run all examples."""
    print("Nimbus Router Storage Backend Examples")
    print("=" * 50)
    
    # Run sync examples
    example_in_memory_storage()
    example_redis_storage()
    example_dynamodb_storage()
    example_postgresql_storage()
    example_filesystem_storage()
    example_durable_function_storage()
    
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