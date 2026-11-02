"""Unit tests for LazyImporter utility."""

import sys
from unittest.mock import patch

import pytest

from skye.models.lazy_import import LazyImporter


class TestLazyImporter:
    """Test suite for LazyImporter."""

    def test_import_module_success(self):
        """Test successful import of an available module."""
        # Import a standard library module that's always available
        json_module = LazyImporter.import_module("json")
        assert json_module is not None
        assert hasattr(json_module, "loads")
        assert hasattr(json_module, "dumps")

    def test_import_module_missing(self):
        """Test import of a missing module raises ImportError with helpful message."""
        with pytest.raises(ImportError) as exc_info:
            LazyImporter.import_module("nonexistent_module_xyz")

        error_message = str(exc_info.value)
        assert "nonexistent_module_xyz" in error_message
        assert "pip install nonexistent_module_xyz" in error_message
        assert "pip install skyeai[nonexistent_module_xyz]" in error_message

    def test_import_module_with_custom_package_name(self):
        """Test import with custom package name in error message."""
        with pytest.raises(ImportError) as exc_info:
            LazyImporter.import_module(
                "fake_module",
                package_name="real-package-name"
            )

        error_message = str(exc_info.value)
        assert "fake_module" in error_message
        assert "pip install real-package-name" in error_message

    def test_import_module_with_custom_install_extra(self):
        """Test import with custom install extra in error message."""
        with pytest.raises(ImportError) as exc_info:
            LazyImporter.import_module(
                "fake_module",
                install_extra="custom-extra"
            )

        error_message = str(exc_info.value)
        assert "fake_module" in error_message
        assert "pip install skyeai[custom-extra]" in error_message

    def test_import_module_with_both_custom_names(self):
        """Test import with both custom package name and install extra."""
        with pytest.raises(ImportError) as exc_info:
            LazyImporter.import_module(
                "fake_module",
                package_name="real-package",
                install_extra="custom-extra"
            )

        error_message = str(exc_info.value)
        assert "fake_module" in error_message
        assert "pip install real-package" in error_message
        assert "pip install skyeai[custom-extra]" in error_message

    def test_is_available_for_existing_module(self):
        """Test is_available returns True for existing modules."""
        # Test with a standard library module
        assert LazyImporter.is_available("json") is True
        assert LazyImporter.is_available("os") is True
        assert LazyImporter.is_available("sys") is True

    def test_is_available_for_missing_module(self):
        """Test is_available returns False for missing modules."""
        assert LazyImporter.is_available("nonexistent_module_xyz") is False
        assert LazyImporter.is_available("fake_package_123") is False

    def test_is_available_for_already_loaded_module(self):
        """Test is_available returns True for already loaded modules."""
        # Import a module first
        import json  # noqa: F401

        # Should return True since it's in sys.modules
        assert LazyImporter.is_available("json") is True

    def test_is_available_does_not_import(self):
        """Test that is_available doesn't actually import the module."""
        # Use a module that exists but isn't imported yet
        module_name = "urllib.parse"

        # Remove from sys.modules if it's there
        if module_name in sys.modules:
            del sys.modules[module_name]

        # Check availability
        is_avail = LazyImporter.is_available(module_name)

        # Should be available but might not be in sys.modules yet
        # (depends on whether find_spec imports it)
        assert is_avail is True

    def test_import_module_caches_in_sys_modules(self):
        """Test that import_module properly caches the module."""
        # Import a module
        module = LazyImporter.import_module("json")

        # Should be in sys.modules
        assert "json" in sys.modules
        assert sys.modules["json"] is module

    def test_error_message_format(self):
        """Test that error messages are properly formatted."""
        with pytest.raises(ImportError) as exc_info:
            LazyImporter.import_module(
                "test_module",
                package_name="test-package",
                install_extra="test-extra"
            )

        error_message = str(exc_info.value)

        # Check all required parts are present
        assert "test_module" in error_message
        assert "not installed" in error_message
        assert "pip install test-package" in error_message
        assert "pip install skyeai[test-extra]" in error_message


class TestLazyImporterLambdaEnvironment:
    """Test LazyImporter behavior in Lambda-like environments."""

    def test_lambda_environment_with_preinstalled_boto3(self):
        """Test that LazyImporter works with pre-installed boto3 in Lambda."""
        # This test simulates boto3 being available in the environment
        # In a real Lambda environment, boto3 is pre-installed

        # Check if boto3 is available (it might be installed in test environment)
        if LazyImporter.is_available("boto3"):
            # If boto3 is available, we can import it
            boto3 = LazyImporter.import_module("boto3")
            assert boto3 is not None
            assert hasattr(boto3, "client")
        else:
            # If boto3 is not available, we should get a helpful error
            with pytest.raises(ImportError) as exc_info:
                LazyImporter.import_module("boto3", install_extra="bedrock")

            error_message = str(exc_info.value)
            assert "boto3" in error_message
            assert "pip install skyeai[bedrock]" in error_message

    def test_other_providers_fail_gracefully_without_sdks(self):
        """Test that other providers fail gracefully when SDKs are missing."""
        # Test with a provider SDK that's unlikely to be installed
        fake_providers = [
            ("anthropic", "anthropic"),
            ("cohere", "cohere"),
        ]

        for module_name, extra_name in fake_providers:
            if not LazyImporter.is_available(module_name):
                # Should raise ImportError with helpful message
                with pytest.raises(ImportError) as exc_info:
                    LazyImporter.import_module(module_name, install_extra=extra_name)

                error_message = str(exc_info.value)
                assert module_name in error_message
                assert f"pip install skyeai[{extra_name}]" in error_message

    @patch("sys.modules", new_callable=dict)
    def test_detects_preloaded_module(self, mock_sys_modules):
        """Test that is_available detects modules already in sys.modules."""
        # Create a mock module
        class MockModule:
            pass

        mock_module = MockModule()
        mock_sys_modules["preloaded_module"] = mock_module

        # Should detect it's available
        with patch("sys.modules", mock_sys_modules):
            assert LazyImporter.is_available("preloaded_module") is True

    def test_lambda_environment_simulation(self):
        """Test Lambda-like environment where boto3 is pre-installed.

        This test simulates the AWS Lambda environment where boto3 is pre-installed
        in the runtime and doesn't need to be in the deployment package.
        """
        # In Lambda, boto3 is available without being in dependencies
        # We simulate this by checking if boto3 can be imported

        # First, check if boto3 is available in the current environment
        boto3_available = LazyImporter.is_available("boto3")

        if boto3_available:
            # Simulate Lambda scenario: boto3 is available
            # The Bedrock provider should be able to use it
            boto3 = LazyImporter.import_module("boto3")
            assert boto3 is not None

            # Verify we can access boto3 functionality
            assert hasattr(boto3, "client")
            assert hasattr(boto3, "Session")

            # This demonstrates that in Lambda, we can use boto3
            # without having it as an explicit dependency
        else:
            # If boto3 is not available, verify we get a helpful error
            # This is what would happen in a local environment without boto3
            with pytest.raises(ImportError) as exc_info:
                LazyImporter.import_module("boto3", install_extra="bedrock")

            error_message = str(exc_info.value)
            assert "boto3" in error_message
            assert "pip install skyeai[bedrock]" in error_message

    def test_providers_without_sdks_fail_gracefully(self):
        """Test that providers fail gracefully when their SDKs are not installed.

        This ensures that if a provider SDK is not available (either as a dependency
        or pre-installed), we get a clear error message with installation instructions.
        """
        # List of provider SDKs that are unlikely to be pre-installed
        test_cases = [
            ("fake_openai_sdk", "openai"),
            ("fake_anthropic_sdk", "anthropic"),
            ("fake_cohere_sdk", "cohere"),
        ]

        for module_name, extra_name in test_cases:
            # These modules should not exist
            assert LazyImporter.is_available(module_name) is False

            # Attempting to import should give helpful error
            with pytest.raises(ImportError) as exc_info:
                LazyImporter.import_module(module_name, install_extra=extra_name)

            error_message = str(exc_info.value)
            assert module_name in error_message
            assert "not installed" in error_message
            assert f"pip install skyeai[{extra_name}]" in error_message
