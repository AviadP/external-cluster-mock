"""Test fixtures for external_cluster_mock."""

import pytest

from external_cluster_mock import CephMockConnection


@pytest.fixture
def mock_conn() -> CephMockConnection:
    """
    Provide a fresh CephMockConnection instance.

    Returns:
        CephMockConnection: A new mock connection instance.

    """
    return CephMockConnection()
