"""Google Vertex AI Provider Example (Boto3-style Nimbus API).

This version demonstrates:
- Basic completion with Vertex AI (Gemini models)
- Streaming responses
- GCP project and location configuration
- Simple client creation: nimbus.provider("vertex")
"""

import os
import nimbus
from nimbus.messages import UserMessage, SystemMessage


def basic_completion():
    """Basic completion using Vertex AI."""
    print("=" * 60)
    print("Vertex AI - Basic Completion")
    print("=" * 60)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "us-central1")
    
    if not project_id:
        print("⚠️  GCP_PROJECT_ID environment variable not set")
        print("   Set it with: export GCP_PROJECT_ID='your-project-id'")
        return
    
    try:
        client = nimbus.provider(
            "vertex",
            project_id=project_id,
            location=location
        )
    except ImportError as e:
        print(f"⚠️  Error: {e}")
        print("\nTo use Vertex AI, install with: pip install nimbus[vertex]")
        return
    
    messages = [
        SystemMessage("You are a helpful assistant."),
        UserMessage("What is the capital of France?"),
    ]
    
    response = client.complete(
        messages=messages,
        model="gemini-1.5-pro",
        temperature=0.7,
        max_tokens=100,
    )
    
    print("\nResponse:")
    print("  Text:", response.content)
    print("  Model:", response.model)
    print("  Tokens:", response.usage.total_tokens)
    print("  Finish reason:", response.finish_reason)


def streaming_example():
    """Streaming completion using Vertex AI."""
    print("\n" + "=" * 60)
    print("Vertex AI - Streaming")
    print("=" * 60)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "us-central1")
    
    if not project_id:
        print("⚠️  GCP_PROJECT_ID environment variable not set")
        return
    
    client = nimbus.provider(
        "vertex",
        project_id=project_id,
        location=location
    )
    
    messages = [UserMessage("Write a short story about a robot learning to paint.")]
    
    print("\nStreaming response:")
    print("-" * 40)
    
    for chunk in client.stream(messages=messages, model="gemini-1.5-pro"):
        print(chunk.delta, end="", flush=True)
    
    print("\n" + "-" * 40)


def multiple_models():
    """Run the same prompt on different Gemini models."""
    print("\n" + "=" * 60)
    print("Vertex AI - Multiple Models")
    print("=" * 60)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "us-central1")
    
    if not project_id:
        print("⚠️  GCP_PROJECT_ID environment variable not set")
        return
    
    client = nimbus.provider(
        "vertex",
        project_id=project_id,
        location=location
    )
    
    models = [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.0-pro",
    ]
    
    prompt = "What is artificial intelligence?"
    messages = [UserMessage(prompt)]
    
    print(f"\nPrompt: {prompt}")
    print("-" * 40)
    
    for model in models:
        print(f"\nModel: {model}")
        response = client.complete(messages=messages, model=model, max_tokens=80)
        print("  Response:", response.content[:80], "...")
        print("  Tokens:", response.usage.total_tokens)


def cloud_run_example():
    """Example for Google Cloud Run deployment."""
    print("\n" + "=" * 60)
    print("Vertex AI - Cloud Run Deployment")
    print("=" * 60)
    
    print("""
Example Cloud Run service using Nimbus with Vertex AI:

```python
import nimbus
from nimbus.messages import UserMessage
from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize client (uses Application Default Credentials)
client = nimbus.provider(
    "vertex",
    project_id="your-project-id",
    location="us-central1"
)

@app.route("/complete", methods=["POST"])
def complete():
    data = request.json
    messages = [UserMessage(data["prompt"])]
    
    response = client.complete(
        messages=messages,
        model="gemini-1.5-pro"
    )
    
    return jsonify({
        "text": response.content,
        "tokens": response.usage.total_tokens
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

Deployment:
1. Create Dockerfile with nimbus[vertex]
2. Deploy to Cloud Run
3. Set service account with Vertex AI permissions
4. Cloud Run provides authentication automatically
""")


def configuration_example():
    """Example showing Vertex AI configuration options."""
    print("\n" + "=" * 60)
    print("Vertex AI - Configuration")
    print("=" * 60)
    
    print("""
Vertex AI configuration options:

```python
import nimbus

# Basic configuration
client = nimbus.provider(
    "vertex",
    project_id="your-project-id",
    location="us-central1"  # or "europe-west1", "asia-northeast1", etc.
)

# With custom credentials
client = nimbus.provider(
    "vertex",
    project_id="your-project-id",
    location="us-central1",
    credentials_path="/path/to/service-account.json"
)
```

Environment variables:
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_LOCATION="us-central1"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

Authentication methods:
1. Application Default Credentials (recommended for GCP)
2. Service account JSON file
3. gcloud CLI authentication
""")


def main():
    """Run all examples."""
    print("\n" + "🌐 " * 20)
    print("NIMBUS - Vertex AI Provider Examples")
    print("🌐 " * 20)
    
    try:
        basic_completion()
        streaming_example()
        multiple_models()
        cloud_run_example()
        configuration_example()
        
        print("\n" + "=" * 60)
        print("✅ Examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Installed nimbus[vertex]: pip install nimbus[vertex]")
        print("  2. Set GCP_PROJECT_ID environment variable")
        print("  3. Configured GCP authentication (gcloud auth or service account)")
        print("  4. Enabled Vertex AI API in your GCP project")


if __name__ == "__main__":
    main()
