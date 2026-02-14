"""
Pytest Configuration and Fixtures
=================================

Shared fixtures and configuration for all tests.
"""

import sys
from pathlib import Path

import pytest

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_symbols():
    """Sample stock symbols for testing."""
    return ["RELIANCE", "TCS", "INFY", "HDFC"]


@pytest.fixture
def sample_indices():
    """Sample index symbols for testing."""
    return ["^NSEI", "^NSEBANK"]
