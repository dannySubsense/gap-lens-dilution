"""
pytest configuration for gap-lens-dilution test suite.

Sets asyncio_mode=auto so that all async test functions are automatically
treated as asyncio tests without requiring explicit @pytest.mark.asyncio
decorators. This applies only to this package (tests/).
"""

import pytest


def pytest_configure(config):
    """Register asyncio_mode=auto for this session."""
    config.addinivalue_line("markers", "asyncio: mark test as asyncio")
