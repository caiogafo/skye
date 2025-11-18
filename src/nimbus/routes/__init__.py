"""Routes package for model routing and load balancing.

This package provides routing capabilities for load balancing across multiple
model deployments with custom aliases.

Example:
    >>> from nimbus import routes as rt
    >>>
    >>> # Define routes
    >>> registry = rt.RouterRegistry([
    ...     rt.RouteConfig(
    ...         alias="gpt-3.5-turbo",
    ...         targets=[
    ...             rt.ModelTarget(
    ...                 model="azure/chatgpt-v-2",
    ...                 provider="azure",
    ...                 api_key="..."
    ...             ),
    ...             rt.ModelTarget(
    ...                 model="gpt-3.5-turbo",
    ...                 provider="openai",
    ...                 api_key="..."
    ...             )
    ...         ],
    ...         strategy="round-robin"
    ...     )
    ... ])
    >>>
    >>> # Use with client
    >>> import nimbus
    >>> client = nimbus.provider("openai", router=registry)
    >>> response = client.complete(messages=[...], model="gpt-3.5-turbo")
"""

from nimbus.routes.registry import (
    ModelTarget,
    RouteConfig,
    RouterRegistry,
    RoutingStrategy,
)

__all__ = [
    "RouterRegistry",
    "RouteConfig",
    "ModelTarget",
    "RoutingStrategy",
]
