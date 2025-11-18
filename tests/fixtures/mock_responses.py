"""Mock API responses for testing provider implementations.

This module provides mock responses from various provider APIs to enable
testing without making actual API calls.
"""

from typing import Any

# OpenAI Mock Responses
OPENAI_COMPLETION_RESPONSE = {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "gpt-4",
    "system_fingerprint": "fp_44709d6fcb",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I assist you today?",
            },
            "finish_reason": "stop",
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 9,
        "total_tokens": 19,
    },
}

OPENAI_STREAMING_CHUNK = {
    "id": "chatcmpl-123",
    "object": "chat.completion.chunk",
    "created": 1677652288,
    "model": "gpt-4",
    "system_fingerprint": "fp_44709d6fcb",
    "choices": [
        {
            "index": 0,
            "delta": {"content": "Hello"},
            "finish_reason": None,
        }
    ],
}

OPENAI_EMBEDDING_RESPONSE = {
    "object": "list",
    "data": [
        {
            "object": "embedding",
            "embedding": [0.1] * 1536,
            "index": 0,
        }
    ],
    "model": "text-embedding-3-small",
    "usage": {
        "prompt_tokens": 5,
        "total_tokens": 5,
    },
}


# Anthropic Mock Responses
ANTHROPIC_COMPLETION_RESPONSE = {
    "id": "msg_123",
    "type": "message",
    "role": "assistant",
    "content": [{"type": "text", "text": "Hello! How can I assist you today?"}],
    "model": "claude-3-opus-20240229",
    "stop_reason": "end_turn",
    "stop_sequence": None,
    "usage": {
        "input_tokens": 10,
        "output_tokens": 9,
    },
}

ANTHROPIC_STREAMING_CHUNK = {
    "type": "content_block_delta",
    "index": 0,
    "delta": {"type": "text_delta", "text": "Hello"},
}


# Bedrock Mock Responses
BEDROCK_CONVERSE_RESPONSE = {
    "output": {
        "message": {
            "role": "assistant",
            "content": [{"text": "Hello! How can I assist you today?"}],
        }
    },
    "stopReason": "end_turn",
    "usage": {
        "inputTokens": 10,
        "outputTokens": 9,
        "totalTokens": 19,
    },
    "metrics": {"latencyMs": 234},
}

BEDROCK_EMBEDDING_RESPONSE = {
    "embedding": [0.1] * 1024,
    "inputTextTokenCount": 5,
}


# Azure OpenAI Mock Responses (similar to OpenAI)
AZURE_COMPLETION_RESPONSE = OPENAI_COMPLETION_RESPONSE.copy()


# Vertex AI Mock Responses
VERTEX_COMPLETION_RESPONSE = {
    "candidates": [
        {
            "content": {
                "role": "model",
                "parts": [{"text": "Hello! How can I assist you today?"}],
            },
            "finish_reason": "STOP",
            "safety_ratings": [],
        }
    ],
    "usage_metadata": {
        "prompt_token_count": 10,
        "candidates_token_count": 9,
        "total_token_count": 19,
    },
}

VERTEX_EMBEDDING_RESPONSE = {
    "predictions": [{"embeddings": {"values": [0.1] * 768}}],
}


# Cohere Mock Responses
COHERE_EMBEDDING_RESPONSE = {
    "id": "embed-123",
    "embeddings": [[0.1] * 1024],
    "texts": ["sample text"],
    "meta": {"api_version": {"version": "1"}},
}


def get_mock_response(provider: str, response_type: str) -> dict[str, Any]:
    """Get a mock response for a specific provider and response type.

    Args:
        provider: Provider name (openai, anthropic, bedrock, azure, vertex, cohere)
        response_type: Type of response (completion, streaming, embedding)

    Returns:
        Mock response dictionary

    Raises:
        ValueError: If provider or response_type is not supported
    """
    mock_responses: dict[str, dict[str, dict[str, Any]]] = {
        "openai": {
            "completion": OPENAI_COMPLETION_RESPONSE,
            "streaming": OPENAI_STREAMING_CHUNK,
            "embedding": OPENAI_EMBEDDING_RESPONSE,
        },
        "anthropic": {
            "completion": ANTHROPIC_COMPLETION_RESPONSE,
            "streaming": ANTHROPIC_STREAMING_CHUNK,
        },
        "bedrock": {
            "completion": BEDROCK_CONVERSE_RESPONSE,
            "embedding": BEDROCK_EMBEDDING_RESPONSE,
        },
        "azure": {
            "completion": AZURE_COMPLETION_RESPONSE,
            "streaming": OPENAI_STREAMING_CHUNK,
        },
        "vertex": {
            "completion": VERTEX_COMPLETION_RESPONSE,
            "embedding": VERTEX_EMBEDDING_RESPONSE,
        },
        "cohere": {
            "embedding": COHERE_EMBEDDING_RESPONSE,
        },
    }

    if provider not in mock_responses:
        raise ValueError(f"Unknown provider: {provider}")

    provider_responses = mock_responses[provider]
    if response_type not in provider_responses:
        raise ValueError(f"Unknown response type '{response_type}' for provider '{provider}'")

    return provider_responses[response_type]
