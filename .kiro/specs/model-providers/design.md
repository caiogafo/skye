# Design Document: Model Providers

## Overview

The Model Providers component implements concrete provider integrations for the ModelInterface and VectorEncoderInterface defined in skye-core. This design follows patterns from litellm and llmio while maintaining Skye's modular architecture and naming conventions.

### Key Design Principles

1. **Lazy Loading**: Provider SDKs are imported only when instantiated
2. **Modular Dependencies**: Each provider is an optional extra with minimal dependencies
3. **Transformation Pattern**: Clean separation between skye models and provider formats
4. **Provider Agnostic**: Unified interface regardless of underlying provider
5. **Environment Awareness**: Detect and use pre-installed SDKs (e.g., boto3 in Lambda)

### Supported Providers

**LLM Providers:**
- OpenAI (GPT-4, GPT-3.5, o1, o3)
- Anthropic (Claude 3.x)
- AWS Bedrock (Claude, Titan, Llama, etc.)
- Azure OpenAI
- Google Vertex AI (Gemini, PaLM)

**Embedding Providers:**
- OpenAI (text-embedding-3-small/large, ada-002)
- AWS Bedrock Titan Embeddings
- Cohere Embeddings
- Vertex AI Text Embeddings
- Vertex AI Multimodal Embeddings

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    skye-core (base)                       │
│  - ModelInterface                                           │
│  - VectorEncoderInterface                                   │
│  - CompletionRequest/Response                               │
│  - SkyeMessage types                                      │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ implements
                          │
┌─────────────────────────────────────────────────────────────┐
│              Model Providers (this component)               │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │           Provider Registry                           │ │
│  │  - Discover installed providers                       │ │
│  │  - Instantiate by name                                │ │
│  │  - Validate configuration                             │ │
│  └───────────────────────────────────────────────────────┘ │
│         │        
                                                     │
│  ┌───────────────────────────────────────────────────────┐ │
│  │           Base Provider Classes                       │ │
│  │  - BaseModelProvider (abstract)                       │ │
│  │  - BaseEmbeddingProvider (abstract)                   │ │
│  │  - RequestTransformer (abstract)                      │ │
│  │  - ResponseTransformer (abstract)                     │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │           Concrete Providers                          │ │
│  │  - OpenAIProvider                                     │ │
│  │  - AnthropicProvider                                  │ │
│  │  - BedrockProvider                                    │ │
│  │  - AzureOpenAIProvider                                │ │
│  │  - VertexAIProvider                                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │           Utilities                                   │ │
│  │  - TokenCounter                                       │ │
│  │  - CostCalculator                                     │ │
│  │  - ImageHandler (multimodal)                          │ │
│  │  - LazyImporter                                       │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Code
    │
    ├─> CompletionRequest (skye model)
    │
    ▼
ProviderRegistry.get("openai")
    │
    ▼
OpenAIProvider (implements ModelInterface)
    │
    ├─> RequestTransformer
    │   └─> Convert CompletionRequest → OpenAI format
    │
    ├─> OpenAI SDK (lazy imported)
    │   └─> API Call
    │
    ├─> ResponseTransformer
    │   └─> Convert OpenAI response → CompletionResponse
    │
    ▼
CompletionResponse (skye model)
```

## Components and Interfaces

### 1. Provider Registry

**Purpose**: Central registry for discovering and instantiating providers.

**Implementation**:
```python
from typing import Dict, Type, Optional
from skye.interfaces.model import ModelInterface
from skye.interfaces.vector_encoder import VectorEncoderInterface
from skye.exceptions import ConfigurationError

class ProviderRegistry:
    """Registry for model and embedding providers."""
    
    _model_providers: Dict[str, Type[ModelInterface]] = {}
    _embedding_providers: Dict[str, Type[VectorEncoderInterface]] = {}
    
    @classmethod
    def register_model_provider(cls, name: str, provider_class: Type[ModelInterface]) -> None:
        """Register a model provider."""
        cls._model_providers[name] = provider_class
    
    @classmethod
    def register_embedding_provider(cls, name: str, provider_class: Type[VectorEncoderInterface]) -> None:
        """Register an embedding provider."""
        cls._embedding_providers[name] = provider_class
    
    @classmethod
    def get_model_provider(cls, name: str, **config) -> ModelInterface:
        """Instantiate a model provider by name."""
        if name not in cls._model_providers:
            available = ", ".join(cls._model_providers.keys())
            raise ConfigurationError(
                f"Provider '{name}' not found. Available: {available}. "
                f"Install with: pip install skyeai[{name}]"
            )
        return cls._model_providers[name](**config)
    
    @classmethod
    def get_embedding_provider(cls, name: str, **config) -> VectorEncoderInterface:
        """Instantiate an embedding provider by name."""
        if name not in cls._embedding_providers:
            available = ", ".join(cls._embedding_providers.keys())
            raise ConfigurationError(
                f"Embedding provider '{name}' not found. Available: {available}. "
                f"Install with: pip install skyeai[{name}]"
            )
        return cls._embedding_providers[name](**config)
    
    @classmethod
    def list_model_providers(cls) -> list[str]:
        """List all registered model providers."""
        return list(cls._model_providers.keys())
    
    @classmethod
    def list_embedding_providers(cls) -> list[str]:
        """List all registered embedding providers."""
        return list(cls._embedding_providers.keys())
```

### 2. Lazy Import System

**Purpose**: Import provider SDKs only when needed, support pre-installed libraries.

**Implementation**:
```python
from typing import Any, Optional
import importlib
import sys

class LazyImporter:
    """Lazy import utility for optional dependencies."""
    
    @staticmethod
    def import_module(module_name: str, package_name: Optional[str] = None, install_extra: Optional[str] = None) -> Any:
        """
        Lazily import a module, providing helpful error if not installed.
        
        Args:
            module_name: The module to import (e.g., 'openai')
            package_name: The package name for pip (e.g., 'openai')
            install_extra: The skye extra to install (e.g., 'openai')
        """
        try:
            return importlib.import_module(module_name)
        except ImportError as e:
            pkg = package_name or module_name
            extra = install_extra or module_name
            raise ImportError(
                f"The '{module_name}' package is required but not installed. "
                f"Install it with: pip install {pkg} "
                f"or install the skye extra: pip install skyeai[{extra}]"
            ) from e
    
    @staticmethod
    def is_available(module_name: str) -> bool:
        """Check if a module is available without importing it."""
        return module_name in sys.modules or importlib.util.find_spec(module_name) is not None
```

**Usage Example**:
```python
class OpenAIProvider(BaseModelProvider):
    def __init__(self, api_key: str, **kwargs):
        # Only import when instantiated
        openai = LazyImporter.import_module("openai", install_extra="openai")
        self.client = openai.OpenAI(api_key=api_key)
```

### 3. Base Provider Classes

**Purpose**: Abstract base classes that define common provider behavior.

**BaseModelProvider**:
```python
from abc import ABC, abstractmethod
from typing import Iterator, Optional, Dict, Any
from skye.interfaces.model import ModelInterface
from skye.completion import CompletionRequest, CompletionResponse, StreamChunk
from skye.exceptions import ProviderError

class BaseModelProvider(ModelInterface, ABC):
    """Abstract base class for model providers."""
    
    def __init__(self, **config):
        self.config = config
        self._client = None
    
    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize the provider-specific client."""
        pass
    
    @property
    def client(self) -> Any:
        """Lazy-load the client."""
        if self._client is None:
            self._client = self._initialize_client()
        return self._client
    
    @abstractmethod
    def _transform_request(self, request: CompletionRequest) -> Dict[str, Any]:
        """Transform CompletionRequest to provider format."""
        pass
    
    @abstractmethod
    def _transform_response(self, response: Any) -> CompletionResponse:
        """Transform provider response to CompletionResponse."""
        pass
    
    @abstractmethod
    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        """Transform provider stream chunk to StreamChunk."""
        pass
    
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute synchronous completion."""
        try:
            provider_request = self._transform_request(request)
            provider_response = self._call_provider(provider_request)
            return self._transform_response(provider_response)
        except Exception as e:
            raise ProviderError(
                f"Provider call failed: {str(e)}",
                provider=self.get_model_info()["provider"]
            ) from e
    
    @abstractmethod
    def _call_provider(self, request: Dict[str, Any]) -> Any:
        """Make the actual provider API call."""
        pass
    
    def stream(self, request: CompletionRequest) -> Iterator[StreamChunk]:
        """Execute streaming completion."""
        try:
            provider_request = self._transform_request(request)
            provider_request["stream"] = True
            for chunk in self._call_provider_stream(provider_request):
                yield self._transform_stream_chunk(chunk)
        except Exception as e:
            raise ProviderError(
                f"Provider streaming failed: {str(e)}",
                provider=self.get_model_info()["provider"]
            ) from e
    
    @abstractmethod
    def _call_provider_stream(self, request: Dict[str, Any]) -> Iterator[Any]:
        """Make streaming provider API call."""
        pass
    
    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute asynchronous completion."""
        # Default implementation uses sync version
        # Override for true async support
        return self.complete(request)
    
    async def astream(self, request: CompletionRequest) -> Iterator[StreamChunk]:
        """Execute asynchronous streaming completion."""
        # Default implementation uses sync version
        # Override for true async support
        for chunk in self.stream(request):
            yield chunk
```

**BaseEmbeddingProvider**:
```python
from abc import ABC, abstractmethod
from typing import List
from skye.interfaces.vector_encoder import VectorEncoderInterface

class BaseEmbeddingProvider(VectorEncoderInterface, ABC):
    """Abstract base class for embedding providers."""
    
    def __init__(self, model: str, **config):
        self.model = model
        self.config = config
        self._client = None
    
    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize the provider-specific client."""
        pass
    
    @property
    def client(self) -> Any:
        """Lazy-load the client."""
        if self._client is None:
            self._client = self._initialize_client()
        return self._client
    
    def encode(self, text: str) -> List[float]:
        """Encode single text."""
        return self.encode_batch([text])[0]
    
    @abstractmethod
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts."""
        pass
    
    async def aencode(self, text: str) -> List[float]:
        """Async encode single text."""
        results = await self.aencode_batch([text])
        return results[0]
    
    async def aencode_batch(self, texts: List[str]) -> List[List[float]]:
        """Async encode multiple texts."""
        # Default implementation uses sync version
        # Override for true async support
        return self.encode_batch(texts)
    
    @abstractmethod
    def get_vector_dimension(self) -> int:
        """Return vector dimension."""
        pass
```

### 4. Request/Response Transformers

**Purpose**: Convert between skye models and provider-specific formats.

**Message Transformation**:
```python
from typing import List, Dict, Any
from skye.messages import SkyeMessage, UserMessage, AssistantMessage, SystemMessage, CapabilityMessage

class MessageTransformer:
    """Transform skye messages to provider formats."""
    
    @staticmethod
    def to_openai_format(messages: List[SkyeMessage]) -> List[Dict[str, Any]]:
        """Convert to OpenAI message format."""
        result = []
        for msg in messages:
            if isinstance(msg, CapabilityMessage):
                result.append({
                    "role": "tool",
                    "tool_call_id": msg.capability_id,
                    "name": msg.capability_name,
                    "content": msg.content
                })
            else:
                openai_msg = {"role": msg.role, "content": msg.content}
                if isinstance(msg, AssistantMessage) and msg.capability_calls:
                    openai_msg["tool_calls"] = msg.capability_calls
                result.append(openai_msg)
        return result
    
    @staticmethod
    def to_anthropic_format(messages: List[SkyeMessage]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Convert to Anthropic format (separate system message)."""
        system = None
        anthropic_messages = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system = msg.content
            elif isinstance(msg, CapabilityMessage):
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.capability_id,
                        "content": msg.content
                    }]
                })
            else:
                content = msg.content
                if isinstance(msg, AssistantMessage) and msg.capability_calls:
                    content = [{
                        "type": "tool_use",
                        "id": call["id"],
                        "name": call["function"]["name"],
                        "input": call["function"]["arguments"]
                    } for call in msg.capability_calls]
                anthropic_messages.append({
                    "role": msg.role,
                    "content": content
                })
        
        return system, anthropic_messages
    
    @staticmethod
    def to_bedrock_format(messages: List[SkyeMessage]) -> List[Dict[str, Any]]:
        """Convert to Bedrock Converse API format."""
        result = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                result.append({"role": "system", "content": [{"text": msg.content}]})
            elif isinstance(msg, CapabilityMessage):
                result.append({
                    "role": "user",
                    "content": [{
                        "toolResult": {
                            "toolUseId": msg.capability_id,
                            "content": [{"text": msg.content}]
                        }
                    }]
                })
            else:
                content = [{"text": msg.content}]
                if isinstance(msg, AssistantMessage) and msg.capability_calls:
                    content = [{
                        "toolUse": {
                            "toolUseId": call["id"],
                            "name": call["function"]["name"],
                            "input": call["function"]["arguments"]
                        }
                    } for call in msg.capability_calls]
                result.append({"role": msg.role, "content": content})
        return result
```

### 5. Multimodal Support

**Purpose**: Handle images, audio, and video inputs for multimodal models.

**ImageHandler**:
```python
import base64
from pathlib import Path
from typing import Union, Dict, Any
from skye.exceptions import ValidationError

class ImageHandler:
    """Handle image inputs for multimodal models."""
    
    @staticmethod
    def process_image(image_input: Union[str, Path, bytes]) -> Dict[str, Any]:
        """
        Process image input into provider-compatible format.
        
        Args:
            image_input: URL, file path, base64 string, or raw bytes
        
        Returns:
            Dict with image data in appropriate format
        """
        if isinstance(image_input, str):
            if image_input.startswith("http://") or image_input.startswith("https://"):
                return {"type": "image_url", "image_url": {"url": image_input}}
            elif image_input.startswith("data:image"):
                return {"type": "image_url", "image_url": {"url": image_input}}
            else:
                # Assume file path
                return ImageHandler.process_image(Path(image_input))
        
        elif isinstance(image_input, Path):
            if not image_input.exists():
                raise ValidationError(f"Image file not found: {image_input}", "image_input", str(image_input))
            
            with open(image_input, "rb") as f:
                image_bytes = f.read()
            
            # Detect mime type from extension
            mime_type = ImageHandler._get_mime_type(image_input.suffix)
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            return {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
            }
        
        elif isinstance(image_bytes, bytes):
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            return {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            }
        
        else:
            raise ValidationError(
                f"Invalid image input type: {type(image_input)}",
                "image_input",
                str(image_input)
            )
    
    @staticmethod
    def _get_mime_type(extension: str) -> str:
        """Get MIME type from file extension."""
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        return mime_types.get(extension.lower(), "image/jpeg")
    
    @staticmethod
    def to_openai_format(image_input: Union[str, Path, bytes]) -> Dict[str, Any]:
        """Convert image to OpenAI format."""
        return ImageHandler.process_image(image_input)
    
    @staticmethod
    def to_anthropic_format(image_input: Union[str, Path, bytes]) -> Dict[str, Any]:
        """Convert image to Anthropic format."""
        processed = ImageHandler.process_image(image_input)
        if processed["type"] == "image_url":
            url = processed["image_url"]["url"]
            if url.startswith("data:"):
                # Extract base64 data
                parts = url.split(",", 1)
                media_type = parts[0].split(";")[0].split(":")[1]
                data = parts[1]
                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": data
                    }
                }
            else:
                return {
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": url
                    }
                }
        return processed
    
    @staticmethod
    def to_bedrock_format(image_input: Union[str, Path, bytes]) -> Dict[str, Any]:
        """Convert image to Bedrock format."""
        processed = ImageHandler.process_image(image_input)
        if processed["type"] == "image_url":
            url = processed["image_url"]["url"]
            if url.startswith("data:"):
                parts = url.split(",", 1)
                media_type = parts[0].split(";")[0].split(":")[1]
                data = parts[1]
                return {
                    "image": {
                        "format": media_type.split("/")[1],
                        "source": {"bytes": base64.b64decode(data)}
                    }
                }
        return processed
```

### 6. Token Counting and Cost Estimation

**Purpose**: Calculate token usage and estimate costs.

**TokenCounter**:
```python
from typing import List, Optional
from skye.messages import SkyeMessage
from skye.exceptions import ConfigurationError

class TokenCounter:
    """Calculate token counts for different models."""
    
    # Model-specific tokenizers (lazy loaded)
    _tokenizers = {}
    
    @classmethod
    def count_tokens(cls, text: str, model: str) -> int:
        """Count tokens for a given text and model."""
        tokenizer = cls._get_tokenizer(model)
        return len(tokenizer.encode(text))
    
    @classmethod
    def count_message_tokens(cls, messages: List[SkyeMessage], model: str) -> int:
        """Count tokens for a list of messages."""
        total = 0
        for msg in messages:
            # Add message overhead (varies by model)
            total += cls._get_message_overhead(model)
            total += cls.count_tokens(msg.content, model)
        return total
    
    @classmethod
    def _get_tokenizer(cls, model: str):
        """Get tokenizer for model (lazy loaded)."""
        if model not in cls._tokenizers:
            if model.startswith("gpt-"):
                tiktoken = LazyImporter.import_module("tiktoken", install_extra="openai")
                cls._tokenizers[model] = tiktoken.encoding_for_model(model)
            elif model.startswith("claude-"):
                anthropic = LazyImporter.import_module("anthropic", install_extra="anthropic")
                cls._tokenizers[model] = anthropic.get_tokenizer()
            else:
                # Fallback to approximate counting
                cls._tokenizers[model] = cls._approximate_tokenizer()
        return cls._tokenizers[model]
    
    @staticmethod
    def _get_message_overhead(model: str) -> int:
        """Get per-message token overhead."""
        if model.startswith("gpt-4"):
            return 3
        elif model.startswith("gpt-3.5"):
            return 4
        else:
            return 3
    
    @staticmethod
    def _approximate_tokenizer():
        """Approximate tokenizer for unknown models."""
        class ApproximateTokenizer:
            @staticmethod
            def encode(text: str) -> List[int]:
                # Rough approximation: 1 token ≈ 4 characters
                return [0] * (len(text) // 4)
        return ApproximateTokenizer()
```

**CostCalculator**:
```python
from typing import Dict, Optional
from skye.completion import TokenUsage

class CostCalculator:
    """Calculate API costs based on token usage."""
    
    # Pricing data (per 1M tokens)
    PRICING = {
        "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
        "gpt-4": {"prompt": 30.00, "completion": 60.00},
        "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
        "claude-3-opus": {"prompt": 15.00, "completion": 75.00},
        "claude-3-sonnet": {"prompt": 3.00, "completion": 15.00},
        "claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
        # Add more models as needed
    }
    
    @classmethod
    def calculate_cost(cls, model: str, usage: TokenUsage, custom_pricing: Optional[Dict] = None) -> float:
        """
        Calculate cost for a completion.
        
        Args:
            model: Model identifier
            usage: Token usage information
            custom_pricing: Optional custom pricing override
        
        Returns:
            Estimated cost in USD
        """
        pricing = custom_pricing or cls.PRICING.get(model)
        
        if not pricing:
            return 0.0  # Unknown model, can't estimate
        
        prompt_cost = (usage.prompt_tokens / 1_000_000) * pricing["prompt"]
        completion_cost = (usage.completion_tokens / 1_000_000) * pricing["completion"]
        
        return prompt_cost + completion_cost
    
    @classmethod
    def add_custom_pricing(cls, model: str, prompt_price: float, completion_price: float) -> None:
        """Add custom pricing for a model."""
        cls.PRICING[model] = {"prompt": prompt_price, "completion": completion_price}
```

### 7. Concrete Provider Implementations

**OpenAI Provider**:
```python
from typing import Dict, Any, Iterator, Optional
from skye.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from skye.messages import AssistantMessage
from datetime import datetime

class OpenAIProvider(BaseModelProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, api_key: str, api_base: Optional[str] = None, organization: Optional[str] = None, **kwargs):
        super().__init__(api_key=api_key, api_base=api_base, organization=organization, **kwargs)
        self.api_key = api_key
        self.api_base = api_base
        self.organization = organization
    
    def _initialize_client(self) -> Any:
        """Initialize OpenAI client."""
        openai = LazyImporter.import_module("openai", install_extra="openai")
        return openai.OpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            organization=self.organization
        )
    
    def _transform_request(self, request: CompletionRequest) -> Dict[str, Any]:
        """Transform to OpenAI format."""
        openai_request = {
            "model": request.model,
            "messages": MessageTransformer.to_openai_format(request.messages),
            "temperature": request.temperature,
            "stream": request.stream
        }
        
        if request.max_tokens:
            openai_request["max_tokens"] = request.max_tokens
        
        if request.top_p:
            openai_request["top_p"] = request.top_p
        
        if request.stop:
            openai_request["stop"] = request.stop
        
        # Handle structured outputs
        if request.response_schema:
            schema = request.response_schema.model_json_schema()
            openai_request["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": request.response_schema.__name__,
                    "schema": schema,
                    "strict": True
                }
            }
        
        # Handle function calling
        if request.capabilities:
            openai_request["tools"] = request.capabilities
            if request.capability_choice:
                openai_request["tool_choice"] = request.capability_choice
        
        # Provider-specific metadata
        if request.metadata:
            for key, value in request.metadata.items():
                if key.startswith("openai_"):
                    openai_request[key[7:]] = value
        
        return openai_request
    
    def _transform_response(self, response: Any) -> CompletionResponse:
        """Transform OpenAI response to CompletionResponse."""
        choice = response.choices[0]
        message = choice.message
        
        # Parse structured output if present
        structured_output = None
        if hasattr(message, "parsed") and message.parsed:
            structured_output = message.parsed
        
        return CompletionResponse(
            id=response.id,
            model=response.model,
            provider="openai",
            content=message.content or "",
            structured_output=structured_output,
            role="assistant",
            finish_reason=choice.finish_reason,
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            ),
            created_at=datetime.fromtimestamp(response.created),
            metadata={
                "system_fingerprint": response.system_fingerprint,
                "tool_calls": message.tool_calls if hasattr(message, "tool_calls") else None
            }
        )
    
    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        """Transform OpenAI stream chunk."""
        choice = chunk.choices[0]
        return StreamChunk(
            id=chunk.id,
            delta=choice.delta.content or "",
            finish_reason=choice.finish_reason,
            index=choice.index
        )
    
    def _call_provider(self, request: Dict[str, Any]) -> Any:
        """Call OpenAI API."""
        return self.client.chat.completions.create(**request)
    
    def _call_provider_stream(self, request: Dict[str, Any]) -> Iterator[Any]:
        """Call OpenAI streaming API."""
        return self.client.chat.completions.create(**request)
    
    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Async completion using OpenAI async client."""
        openai = LazyImporter.import_module("openai", install_extra="openai")
        async_client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            organization=self.organization
        )
        
        provider_request = self._transform_request(request)
        response = await async_client.chat.completions.create(**provider_request)
        return self._transform_response(response)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata."""
        return {
            "provider": "openai",
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_structured_output": True,
            "supports_multimodal": True
        }
```

**Bedrock Provider** (with lazy boto3):
```python
class BedrockProvider(BaseModelProvider):
    """AWS Bedrock provider with optional boto3."""
    
    def __init__(self, region_name: str = "us-east-1", profile_name: Optional[str] = None, **kwargs):
        super().__init__(region_name=region_name, profile_name=profile_name, **kwargs)
        self.region_name = region_name
        self.profile_name = profile_name
    
    def _initialize_client(self) -> Any:
        """Initialize Bedrock client (boto3 optional in Lambda)."""
        # Try to import boto3, but don't fail if it's not installed
        # (it might be pre-installed in Lambda)
        try:
            boto3 = LazyImporter.import_module("boto3", package_name="boto3", install_extra="bedrock")
        except ImportError:
            # Check if boto3 is available in the environment
            import sys
            if "boto3" in sys.modules:
                boto3 = sys.modules["boto3"]
            else:
                raise
        
        session = boto3.Session(
            region_name=self.region_name,
            profile_name=self.profile_name
        )
        return session.client("bedrock-runtime")
    
    def _transform_request(self, request: CompletionRequest) -> Dict[str, Any]:
        """Transform to Bedrock Converse API format."""
        bedrock_request = {
            "modelId": request.model,
            "messages": MessageTransformer.to_bedrock_format(request.messages),
            "inferenceConfig": {
                "temperature": request.temperature
            }
        }
        
        if request.max_tokens:
            bedrock_request["inferenceConfig"]["maxTokens"] = request.max_tokens
        
        if request.top_p:
            bedrock_request["inferenceConfig"]["topP"] = request.top_p
        
        if request.stop:
            bedrock_request["inferenceConfig"]["stopSequences"] = request.stop
        
        # Handle function calling
        if request.capabilities:
            bedrock_request["toolConfig"] = {
                "tools": [{"toolSpec": cap} for cap in request.capabilities]
            }
        
        return bedrock_request
    
    def _call_provider(self, request: Dict[str, Any]) -> Any:
        """Call Bedrock Converse API."""
        return self.client.converse(**request)
    
    def _call_provider_stream(self, request: Dict[str, Any]) -> Iterator[Any]:
        """Call Bedrock streaming API."""
        response = self.client.converse_stream(**request)
        return response["stream"]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata."""
        return {
            "provider": "bedrock",
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_structured_output": False,  # Via function calling
            "supports_multimodal": True
        }
```

**Embedding Provider Example**:
```python
class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider."""
    
    def __init__(self, model: str = "text-embedding-3-small", api_key: Optional[str] = None, **kwargs):
        super().__init__(model=model, **kwargs)
        self.api_key = api_key
    
    def _initialize_client(self) -> Any:
        """Initialize OpenAI client."""
        openai = LazyImporter.import_module("openai", install_extra="openai")
        return openai.OpenAI(api_key=self.api_key)
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    async def aencode_batch(self, texts: List[str]) -> List[List[float]]:
        """Async encode multiple texts."""
        openai = LazyImporter.import_module("openai", install_extra="openai")
        async_client = openai.AsyncOpenAI(api_key=self.api_key)
        
        response = await async_client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    def get_vector_dimension(self) -> int:
        """Return vector dimension."""
        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        return dimensions.get(self.model, 1536)
```

## Data Models

All data models are defined in skye-core. This component only implements transformations between skye models and provider-specific formats.

## Error Handling

### Provider Error Wrapping

All provider-specific errors are wrapped in `ProviderError` with context:

```python
try:
    response = self.client.chat.completions.create(**request)
except openai.RateLimitError as e:
    raise ProviderError(
        f"Rate limit exceeded: {str(e)}",
        provider="openai",
        error_type="rate_limit",
        retry_after=e.retry_after
    ) from e
except openai.APIError as e:
    raise ProviderError(
        f"API error: {str(e)}",
        provider="openai",
        error_type="api_error",
        status_code=e.status_code
    ) from e
```

### Retry Logic

Retry logic is implemented in the base provider class:

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class BaseModelProvider(ModelInterface, ABC):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ProviderError,)),
        reraise=True
    )
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        # Implementation
        pass
```

## Testing Strategy

### Unit Tests
- Test each provider's request/response transformation
- Test lazy import system
- Test token counting and cost calculation
- Test multimodal input handling
- Mock provider SDKs to avoid actual API calls

### Integration Tests
- Test actual API calls with real providers (optional, requires API keys)
- Test streaming responses
- Test function calling
- Test structured outputs
- Test multimodal inputs

### Test Structure
```
tests/
├── unit/
│   ├── test_provider_registry.py
│   ├── test_lazy_import.py
│   ├── test_transformers.py
│   ├── test_token_counter.py
│   ├── test_cost_calculator.py
│   ├── test_image_handler.py
│   ├── providers/
│   │   ├── test_openai_provider.py
│   │   ├── test_bedrock_provider.py
│   │   ├── test_anthropic_provider.py
│   │   └── test_embedding_providers.py
├── integration/
│   ├── test_openai_integration.py
│   ├── test_bedrock_integration.py
│   └── test_embeddings_integration.py
└── fixtures/
    ├── mock_responses.py
    └── sample_requests.py
```

## Package Structure

```
skye/
└── src/
    └── skye/
        └── providers/
            ├── __init__.py              # Provider registry, exports
            ├── base.py                  # Base provider classes
            ├── registry.py              # ProviderRegistry
            ├── lazy_import.py           # LazyImporter
            ├── transformers.py          # Message transformers
            ├── multimodal.py            # ImageHandler, AudioHandler
            ├── token_counter.py         # TokenCounter
            ├── cost_calculator.py       # CostCalculator
            ├── openai_provider.py       # OpenAI implementation
            ├── anthropic_provider.py    # Anthropic implementation
            ├── bedrock_provider.py      # Bedrock implementation
            ├── azure_provider.py        # Azure OpenAI implementation
            ├── vertex_provider.py       # Vertex AI implementation
            └── embeddings/
                ├── __init__.py
                ├── openai_embeddings.py
                ├── bedrock_embeddings.py
                ├── cohere_embeddings.py
                └── vertex_embeddings.py
```

## Dependencies

### Optional Dependencies by Provider

```toml
[project.optional-dependencies]
openai = ["openai>=1.0", "tiktoken>=0.5"]
anthropic = ["anthropic>=0.25"]
bedrock = ["boto3>=1.28"]  # Optional in Lambda
azure = ["azure-ai-inference>=1.0.0b1", "azure-identity>=1.15"]
vertex = ["google-cloud-aiplatform>=1.38"]
cohere = ["cohere>=5.0"]

# Convenience bundles
llm-providers = ["openai>=1.0", "anthropic>=0.25", "boto3>=1.28"]
embedding-providers = ["openai>=1.0", "cohere>=5.0"]
all-providers = ["openai>=1.0", "anthropic>=0.25", "boto3>=1.28", "azure-ai-inference>=1.0.0b1", "google-cloud-aiplatform>=1.38", "cohere>=5.0"]
```

## Design Decisions

1. **Lazy Loading**: Providers are only imported when instantiated, reducing startup time and memory
2. **Transformation Pattern**: Clean separation between skye and provider formats makes adding providers easier
3. **Optional boto3**: Bedrock provider works without boto3 dependency in Lambda environments
4. **Unified Multimodal**: ImageHandler provides consistent interface across providers
5. **Cost Tracking**: Built-in cost estimation helps developers monitor spending
6. **Provider Registry**: Central discovery mechanism simplifies provider management
7. **Async Support**: True async implementations where provider SDKs support it

## Future Considerations

- **Caching**: Add response caching layer
- **Load Balancing**: Implement router for distributing requests across providers
- **Fallback**: Automatic fallback to alternative providers on failure
- **Monitoring**: Enhanced metrics and health checks
- **Custom Providers**: Plugin system for user-defined providers
