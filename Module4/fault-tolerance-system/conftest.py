import os
import sys

import pytest

# Tests import `resilience`, `orders`, `inventory`, `observability` and `chaos`
# as top-level packages, so the project root must be importable.
sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture
def anyio_backend():
    """anyio's pytest plugin needs this to run @pytest.mark.anyio tests."""
    return "asyncio"
