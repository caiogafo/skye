"""Azure OpenAI: the OpenAI wire format behind an Azure resource and a deployment name.

Example:
    >>> from skye.models.llm.azure import AzureOpenAIProvider
    >>> provider = AzureOpenAIProvider(
    ...     azure_endpoint="https://myresource.openai.azure.com/", api_key="...",
    ...     api_version="2024-02-15-preview", deployment_name="gpt-4",
    ... )
"""

from typing import Any

from skye.base.completion import CompleteRequest
from skye.models.base import BaseModelProvider
from skye.models.llm.openai_compatible import OpenAICompatibleProvider


class AzureOpenAIProvider(OpenAICompatibleProvider):
    """Azure OpenAI expressed as configuration of the OpenAI-compatible adapter.

    Azure differs only in client construction (endpoint + api_version), the deployment name
    standing in for the model, the ``azure_`` metadata prefix and no ``system_fingerprint``.

    Args:
        azure_endpoint: Azure OpenAI endpoint URL (e.g. https://myresource.openai.azure.com/)
        api_key: Azure OpenAI API key
        api_version: Azure OpenAI API version (e.g. 2024-02-15-preview)
        deployment_name: Name of the deployment (e.g. gpt-4)
    """

    provider_name = "azure"
    metadata_prefix = "azure_"
    reports_fingerprint = False

    def __init__(
        self,
        azure_endpoint: str,
        api_key: str,
        api_version: str,
        deployment_name: str,
        **kwargs: Any,
    ) -> None:
        BaseModelProvider.__init__(
            self,
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version,
            deployment_name=deployment_name,
            **kwargs,
        )
        self.azure_endpoint = azure_endpoint
        self.api_key = api_key
        self.api_version = api_version
        self.deployment_name = deployment_name

    def _endpoint_url(self) -> str:
        return (
            f"{self.azure_endpoint.rstrip('/')}/openai/deployments/{self.deployment_name}"
            f"/chat/completions?api-version={self.api_version}"
        )

    def _auth_headers(self) -> dict[str, str]:
        return {"api-key": self.api_key}

    def _model_name(self, request: CompleteRequest) -> str:
        return self.deployment_name


__all__ = ["AzureOpenAIProvider"]
