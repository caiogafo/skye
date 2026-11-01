"""Basic test to verify test infrastructure."""


def test_import_nimbus():
    """Test that nimbus package can be imported."""
    import nimbus

    assert nimbus.__version__ == "0.1.0"


def test_import_interfaces():
    """Test that interfaces module can be imported."""
    import nimbus.base.interfaces

    assert nimbus.base.interfaces is not None


def test_import_providers():
    """Test that providers module can be imported."""
    import nimbus.models

    assert nimbus.models is not None
