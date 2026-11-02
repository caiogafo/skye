"""MCP Server Capability Example.

This example demonstrates how to connect to an existing MCP server,
list its tools, and use them as Skye capabilities with language models.

Prerequisites:
- FastMCP installed: pip install skyeai[mcp]
- An MCP server running (update SERVER_URL below)
- OPENAI_API_KEY environment variable set

Example MCP servers you can use:
- FastMCP example servers
- Custom MCP servers
- Third-party MCP servers
"""

import os
import asyncio
from skye.models.registry import provider as create_provider
from skye.base.messages import UserMessage
from skye.tools import MCPCapability


# Configure your MCP server connection here
SERVER_URL = "http://localhost:8000/sse"  # Update this to your MCP server URL
# Or use stdio: SERVER_URL = "my_server.py"
# Or use command: SERVER_URL = ["python", "my_server.py"]


async def main():
    """Connect to MCP server, list tools, and use them with a language model."""
    
    # Check for FastMCP
    try:
        from fastmcp import Client
    except ImportError:
        print("❌ FastMCP not installed")
        print("   Install with: pip install skyeai[mcp]")
        return
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        return
    
    # Get provider
    try:
        provider = create_provider("openai", api_key=api_key)
    except ImportError:
        print("❌ OpenAI provider not available")
        return
    
    print("=" * 60)
    print("MCP Server Capability Example")
    print("=" * 60)
    
    try:
        # Step 1: Connect to MCP server
        print(f"\n📡 Connecting to MCP server: {SERVER_URL}")
        async with Client(SERVER_URL) as client:
            
            # Step 2: List available tools
            print("\n🔍 Listing available tools...")
            tools = await client.list_tools()
            
            if not tools:
                print("⚠️  No tools found on the server")
                return
            
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
            
            # Step 3: Convert tools to Skye capabilities
            print("\n🔧 Converting tools to Skye capabilities...")
            capabilities = []
            for tool in tools:
                capability = MCPCapability(
                    mcp_tool=tool,
                    server_name="mcp_server",
                    cache_schema=True
                )
                capabilities.append(capability)
            
            print(f"✅ Converted {len(capabilities)} capabilities")
            
            # Step 4: Use capabilities with language model
            print("\n💬 Sending request to language model...")
            user_message = "Use the available tools to help me"
            
            response = provider.complete(
                messages=[UserMessage(content=user_message)],
                model="gpt-4",
                capabilities=capabilities
            )
            
            print(f"\n🤖 Model response: {response.content}")
            
            # Step 5: Execute capability calls if any
            if response.has_capability_calls():
                print(f"\n⚙️  Executing {len(response.capability_calls)} capability calls...")
                
                for call in response.capability_calls:
                    print(f"   - {call.name}({call.arguments})")
                
                capability_messages = await response.execute_capability_calls()
                
                print("\n📊 Capability results:")
                for msg in capability_messages:
                    print(f"   - {msg.capability_name}: {msg.content[:100]}...")
                
                # Step 6: Continue conversation with results
                print("\n💬 Continuing conversation with results...")
                final_response = provider.complete(
                    messages=[
                        UserMessage(content=user_message),
                        response.to_message(),
                        *capability_messages
                    ],
                    model="gpt-4",
                    capabilities=capabilities
                )
                
                print(f"\n🤖 Final response: {final_response.content}")
            else:
                print("\n✅ No capability calls needed")
        
        print("\n" + "=" * 60)
        print("✅ Example completed successfully!")
        print("=" * 60)
    
    except ConnectionError as e:
        print(f"\n❌ Connection failed: {e}")
        print(f"   Make sure your MCP server is running at: {SERVER_URL}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Starting MCP Server Example...")
    print(f"   Server URL: {SERVER_URL}")
    print(f"   Update SERVER_URL in the script to match your MCP server\n")
    
    asyncio.run(main())
