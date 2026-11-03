"""A component of a Port is validated when built and while it runs; plugins register and are found.

The plugin and registry Ports (Requirement 16.2, 16.3).
"""

from typing import Any

import pytest

from skye.base.exceptions import ConfigurationError, ValidationError
from skye.base.interfaces.model import ModelInterface
from skye.base.interfaces.plugin import PluginInterface
from skye.base.interfaces.registry import ProviderRegistryInterface, get_provider_registry
from skye.models.registry import ProviderRegistry
from skye.utils.validation import validate_interface_compliance


class GoodPlugin(PluginInterface):
    def __init__(self) -> None:
        self.started = False

    def initialize(self) -> None:
        self.started = True

    def shutdown(self) -> None:
        self.started = False

    def get_metadata(self) -> dict[str, Any]:
        return {"name": "good", "version": "1"}


class HalfPlugin(PluginInterface):
    def initialize(self) -> None:
        pass


class ModelPlugin(ModelInterface):
    """A provider plugin: it implements the model Port, enough to be registered."""

    def __init__(self, **config: Any) -> None:
        self.config = config

    def complete(self, request: Any) -> Any: ...
    def stream(self, request: Any) -> Any: ...
    async def acomplete(self, request: Any) -> Any: ...
    async def astream(self, request: Any) -> Any: ...
    def get_capabilities(self) -> dict[str, Any]:
        return {}

    def get_model_info(self) -> dict[str, Any]:
        return {}


def test_a_component_missing_part_of_a_port_cannot_be_built():
    with pytest.raises(TypeError):
        HalfPlugin()
    with pytest.raises(TypeError):
        PluginInterface()


def test_compliance_is_validated_at_runtime_too():
    validate_interface_compliance(GoodPlugin(), PluginInterface)
    with pytest.raises(ValidationError) as caught:
        validate_interface_compliance(HalfPlugin, PluginInterface)
    assert caught.value.details["interface"] == "PluginInterface"


def test_a_plugin_runs_its_lifecycle_through_the_port():
    plugin: PluginInterface = GoodPlugin()
    plugin.initialize()
    assert plugin.get_metadata()["name"] == "good"
    plugin.shutdown()


class TestRegistryPort:
    def setup_method(self):
        self._saved = (
            dict(ProviderRegistry._model_providers),
            dict(ProviderRegistry._embedding_providers),
        )

    def teardown_method(self):
        ProviderRegistry._model_providers, ProviderRegistry._embedding_providers = self._saved

    def test_the_default_registry_implements_the_registry_port(self):
        assert issubclass(ProviderRegistry, ProviderRegistryInterface)
        assert get_provider_registry() is ProviderRegistry

    def test_a_plugin_registers_and_is_found_by_name(self):
        registry = get_provider_registry()
        registry.register_model_provider("plugged", ModelPlugin)
        assert "plugged" in registry.list_model_providers()
        instance = registry.get_model_provider("plugged", api_key="k")
        assert isinstance(instance, ModelPlugin) and instance.config["api_key"] == "k"

    def test_an_incomplete_implementation_fails_when_the_registry_builds_it(self):
        class HalfModel(ModelInterface):
            def complete(self, request: Any) -> Any: ...

        registry = get_provider_registry()
        registry.register_model_provider("half", HalfModel)
        with pytest.raises(ConfigurationError):
            registry.get_model_provider("half")

    def test_an_unknown_name_is_a_configuration_error(self):
        with pytest.raises(ConfigurationError):
            get_provider_registry().get_model_provider("nobody-registered-this")
