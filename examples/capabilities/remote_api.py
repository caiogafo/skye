"""Remote API Capability Example.

This example demonstrates how to use remote HTTP APIs as capabilities
that can be invoked by language models.

Features shown:
- Wrapping HTTP APIs as capabilities
- Handling different HTTP methods (GET, POST, PUT, DELETE)
- Error handling and API responses
- Authentication and custom headers
- Both synchronous and asynchronous execution

Note: Set environment variables for API keys:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
"""

import os
import json
import asyncio
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage, CapabilityMessage
from skye.tools import RemoteAPICapability
from skye.tools.schema import CapabilitySchema


def basic_remote_api_example():
    """Basic example of using remote APIs as capabilities."""
    print("=" * 60)
    print("Remote API Capabilities - Basic Example")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = create_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    # Create capability for remote API
    posts_schema = CapabilitySchema(
        name="posts.get_user_posts",
        description="Get posts by a user from JSONPlaceholder",
        parameters={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "User ID (1-10)"
                }
            },
            "required": ["user_id"]
        },
        returns={"type": "array", "description": "List of posts"}
    )
    
    posts_cap = RemoteAPICapability(
        name="posts.get_user_posts",
        description="Get posts by a user from JSONPlaceholder",
        url="https://jsonplaceholder.typicode.com/posts",
        method="GET",
        schema=posts_schema,
        timeout=10.0
    )
    
    # Pass capability directly - no need to convert to dict!
    capabilities = [posts_cap]
    
    print("\nCapabilities defined:")
    for cap in capabilities:
        schema = cap.get_schema()
        print(f"  - {schema.name}: {schema.description}")
    
    print("\nRequest:")
    print(f"  Model: gpt-4")
    print(f"  Message: Get posts from user 1")
    
    try:
        response = provider.complete(
            messages=[
                UserMessage(content="Get posts from user 1 and tell me about them")
            ],
            model="gpt-4",
            capabilities=capabilities
        )
        
        print("\nResponse:")
        print(f"  Content: {response.content[:100]}...")
        
        if response.capability_calls:
            print(f"\n  Capability calls: {len(response.capability_calls)}")
            for call in response.capability_calls:
                func_name = call['function']['name']
                args = call['function']['arguments']
                print(f"    - {func_name}({args})")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def execute_remote_api_example():
    """Example of executing remote API capabilities."""
    print("\n" + "=" * 60)
    print("Remote API Capabilities - Execute Example")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        return
    
    try:
        provider = create_provider("openai", api_key=api_key)
    except ImportError:
        print("⚠️  OpenAI provider not available")
        return
    
    # Create remote API capability
    posts_schema = CapabilitySchema(
        name="posts.get_user_posts",
        description="Get posts by a user from JSONPlaceholder",
        parameters={
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            },
            "required": ["user_id"]
        },
        returns={"type": "array"}
    )
    
    posts_cap = RemoteAPICapability(
        name="posts.get_user_posts",
        description="Get posts by a user from JSONPlaceholder",
        url="https://jsonplaceholder.typicode.com/posts",
        method="GET",
        schema=posts_schema,
        timeout=10.0
    )
    
    # Pass capability directly
    capabilities = [posts_cap]
    
    print("\nStep 1: Request to get posts")
    
    try:
        response = provider.complete(
            messages=[
                UserMessage(content="Get the first 3 posts from user 2")
            ],
            model="gpt-4",
            capabilities=capabilities
        )
        
        print(f"  Assistant: {response.content[:80]}...")
        
        if response.has_capability_calls():
            print(f"\nStep 2: Execute remote API calls automatically")
            print(f"  Found {len(response.capability_calls)} capability call(s)")
            
            # Execute capabilities using the built-in method
            capability_messages = await response.execute_capability_calls()
            
            for msg in capability_messages:
                print(f"  {msg.capability_name}: {msg.content[:100]}...")
            
            print(f"\nStep 3: Continue conversation with results")
            
            # Continue conversation with capability results
            final_response = provider.complete(
                messages=[
                    UserMessage(content="Get the first 3 posts from user 2"),
                    response.to_message(),
                    *capability_messages
                ],
                model="gpt-4",
                capabilities=capabilities
            )
            print(f"  Assistant: {final_response.content}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def async_remote_api_example():
    """Example of executing remote APIs asynchronously."""
    print("\n" + "=" * 60)
    print("Remote API Capabilities - Async Example")
    print("=" * 60)
    
    # Create remote API capability
    posts_schema = CapabilitySchema(
        name="posts.get_user_posts",
        description="Get posts by a user from JSONPlaceholder",
        parameters={
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            },
            "required": ["user_id"]
        },
        returns={"type": "array"}
    )
    
    posts_cap = RemoteAPICapability(
        name="posts.get_user_posts",
        description="Get posts by a user from JSONPlaceholder",
        url="https://jsonplaceholder.typicode.com/posts",
        method="GET",
        schema=posts_schema,
        timeout=10.0
    )
    
    print("\nCapability: posts.get_user_posts")
    schema = posts_cap.get_schema()
    print(f"  Name: {schema.name}")
    print(f"  Description: {schema.description}")
    
    print("\nExecuting async API calls...")
    
    try:
        # Execute multiple API calls concurrently
        tasks = [
            posts_cap.aexecute(user_id=1),
            posts_cap.aexecute(user_id=2),
            posts_cap.aexecute(user_id=3),
        ]
        
        results = await asyncio.gather(*tasks)
        
        for i, result in enumerate(results, 1):
            if isinstance(result, list):
                print(f"\n  User {i}: {len(result)} posts")
                if result:
                    print(f"    First post: {result[0].get('title', 'N/A')[:50]}...")
            else:
                print(f"\n  User {i}: {result}")
        
        print("\n✅ All async API calls completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def api_configuration_example():
    """Example showing different API configurations."""
    print("\n" + "=" * 60)
    print("Remote API Capabilities - Configuration Examples")
    print("=" * 60)
    
    print("\n1. Simple GET API (no authentication):")
    print("""
    capability = RemoteAPICapability(
        name="weather.get_current",
        description="Get current weather",
        url="https://api.open-meteo.com/v1/forecast",
        method="GET"
    )
    """)
    
    print("\n2. API with custom headers:")
    print("""
    capability = RemoteAPICapability(
        name="github.search_repos",
        description="Search GitHub repositories",
        url="https://api.github.com/search/repositories",
        method="GET",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Skye"
        }
    )
    """)
    
    print("\n3. API with basic authentication:")
    print("""
    capability = RemoteAPICapability(
        name="api.protected",
        description="Protected API endpoint",
        url="https://api.example.com/data",
        method="GET",
        auth=("username", "password")
    )
    """)
    
    print("\n4. POST API with JSON body:")
    print("""
    capability = RemoteAPICapability(
        name="api.create_resource",
        description="Create a new resource",
        url="https://api.example.com/resources",
        method="POST",
        schema=CapabilitySchema(
            name="api.create_resource",
            description="Create a new resource",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["name"]
            },
            returns={"type": "object"}
        )
    )
    """)
    
    print("\n5. API with custom timeout:")
    print("""
    capability = RemoteAPICapability(
        name="api.slow_endpoint",
        description="Slow endpoint with custom timeout",
        url="https://api.example.com/slow",
        method="GET",
        timeout=60.0  # 60 second timeout
    )
    """)


async def main():
    """Run all examples."""
    print("\n" + "🔧 " * 20)
    print("SKYE - Remote API Capability Examples")
    print("🔧 " * 20)
    
    try:
        basic_remote_api_example()
        await execute_remote_api_example()
        await async_remote_api_example()
        api_configuration_example()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        print("\nKey points:")
        print("  • Wrap HTTP APIs as capabilities using RemoteAPICapability")
        print("  • Supports GET, POST, PUT, DELETE, PATCH methods")
        print("  • Handle authentication and custom headers")
        print("  • Execute APIs synchronously or asynchronously")
        print("  • Proper error handling for API failures")
        print("  • Works with any provider (OpenAI, Anthropic, Bedrock, etc.)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
