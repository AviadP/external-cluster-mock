"""Tests for ExternalCluster topology exporter methods.

These tests validate the topology exporter logic using mocks.
Must be run from the ocs-ci virtual environment or with ocs-ci on PYTHONPATH.

Run: PYTHONPATH=/path/to/ocs-ci pytest tests/test_topology_exporter.py -v
"""

import json
from unittest.mock import MagicMock, patch

import pytest


# Skip all tests if ocs_ci is not available
pytest.importorskip("ocs_ci", reason="ocs_ci package required")


class TestRunTopologyExporterScript:
    """Tests for run_topology_exporter_script method."""

    @pytest.fixture
    def topology_setup(self):
        """Create ExternalCluster with mocked dependencies."""
        with patch("ocs_ci.utility.connection.Connection"):
            from ocs_ci.deployment.helpers.external_cluster_helpers import (
                ExternalCluster,
                TopologyReplica1Config,
                ZoneConfig,
            )
            from external_cluster_mock import CephMockConnection

            # Create cluster bypassing __init__
            cluster = ExternalCluster.__new__(ExternalCluster)
            cluster.host = "test-host"
            cluster.user = "test-user"
            cluster.password = "test-pass"
            cluster.ssh_key = None
            cluster.jump_host = None
            cluster.rhcs_conn = CephMockConnection()

            # Create topology config
            zones = [
                ZoneConfig(zone_name="zone-a", host_name="osd-0"),
                ZoneConfig(zone_name="zone-b", host_name="osd-1"),
                ZoneConfig(zone_name="zone-c", host_name="osd-2"),
            ]
            topology_config = TopologyReplica1Config(zones=zones)

            return cluster, topology_config, ZoneConfig, TopologyReplica1Config

    def test_builds_correct_topology_params(self, topology_setup):
        """run_topology_exporter_script should build correct params string."""
        cluster, topology_config, _, _ = topology_setup

        captured_params = []

        def mock_run_exporter(params):
            captured_params.append(params)
            return json.dumps([{"name": "test", "kind": "Secret", "data": {}}])

        cluster.run_exporter_script = mock_run_exporter

        cluster.run_topology_exporter_script(topology_config)

        assert len(captured_params) == 1
        params = captured_params[0]

        assert "--rbd-data-pool-name rbd-zone-zone-a" in params
        assert "--topology-pools rbd-zone-zone-a,rbd-zone-zone-b,rbd-zone-zone-c" in params
        assert "--topology-failure-domain-label topology.kubernetes.io/zone" in params
        assert "--topology-failure-domain-values zone-a,zone-b,zone-c" in params
        assert "--format json" in params

    def test_parses_json_output(self, topology_setup):
        """run_topology_exporter_script should parse JSON output correctly."""
        cluster, topology_config, _, _ = topology_setup

        expected_resources = [
            {"name": "rook-csi-rbd-node", "kind": "Secret", "data": {"userID": "csi-rbd-node"}},
            {"name": "rook-ceph-mon-endpoints", "kind": "ConfigMap", "data": {"data": "a=10.0.0.1"}},
        ]

        cluster.run_exporter_script = MagicMock(return_value=json.dumps(expected_resources))

        result = cluster.run_topology_exporter_script(topology_config)

        assert result == expected_resources
        assert len(result) == 2

    def test_raises_on_invalid_json(self, topology_setup):
        """run_topology_exporter_script should raise on invalid JSON output."""
        cluster, topology_config, _, _ = topology_setup
        cluster.run_exporter_script = MagicMock(return_value="not valid json")

        from ocs_ci.ocs.exceptions import ExternalClusterExporterRunFailed

        with pytest.raises(ExternalClusterExporterRunFailed):
            cluster.run_topology_exporter_script(topology_config)

    def test_raises_on_empty_zones(self, topology_setup):
        """run_topology_exporter_script should raise ValueError for empty zones."""
        cluster, _, _, TopologyReplica1Config = topology_setup

        empty_config = TopologyReplica1Config(zones=[])

        with pytest.raises(ValueError, match="cannot be empty"):
            cluster.run_topology_exporter_script(empty_config)

    def test_uses_custom_pool_names(self, topology_setup):
        """run_topology_exporter_script should use custom pool names when provided."""
        cluster, _, ZoneConfig, TopologyReplica1Config = topology_setup

        zones = [
            ZoneConfig(zone_name="zone-a", host_name="osd-0", pool_name="custom-pool-a"),
            ZoneConfig(zone_name="zone-b", host_name="osd-1", pool_name="custom-pool-b"),
        ]
        config = TopologyReplica1Config(zones=zones)

        captured_params = []

        def mock_exporter(params):
            captured_params.append(params)
            return "[]"

        cluster.run_exporter_script = mock_exporter

        cluster.run_topology_exporter_script(config)

        params = captured_params[0]
        assert "--rbd-data-pool-name custom-pool-a" in params
        assert "--topology-pools custom-pool-a,custom-pool-b" in params

    def test_appends_additional_params(self, topology_setup):
        """run_topology_exporter_script should append additional params."""
        cluster, topology_config, _, _ = topology_setup

        captured_params = []

        def mock_exporter(params):
            captured_params.append(params)
            return "[]"

        cluster.run_exporter_script = mock_exporter

        cluster.run_topology_exporter_script(
            topology_config, additional_params="--namespace test-ns"
        )

        params = captured_params[0]
        assert "--namespace test-ns" in params


class TestApplyTopologyExportResources:
    """Tests for apply_topology_export_resources method."""

    @pytest.fixture
    def cluster_setup(self):
        """Create ExternalCluster with mocked dependencies."""
        with patch("ocs_ci.utility.connection.Connection"):
            from ocs_ci.deployment.helpers.external_cluster_helpers import ExternalCluster
            from external_cluster_mock import CephMockConnection

            cluster = ExternalCluster.__new__(ExternalCluster)
            cluster.host = "test-host"
            cluster.user = "test-user"
            cluster.password = "test-pass"
            cluster.ssh_key = None
            cluster.jump_host = None
            cluster.rhcs_conn = CephMockConnection()

            return cluster

    def test_creates_secrets(self, cluster_setup):
        """apply_topology_export_resources should create secrets."""
        cluster = cluster_setup
        mock_ocp_instance = MagicMock()

        with patch("ocs_ci.deployment.helpers.external_cluster_helpers.OCP", return_value=mock_ocp_instance):
            with patch("ocs_ci.deployment.helpers.external_cluster_helpers.config") as mock_config:
                mock_config.ENV_DATA = {"cluster_namespace": "openshift-storage"}

                resources = [
                    {"name": "rook-csi-rbd-node", "kind": "Secret", "data": {"userID": "test"}},
                ]

                result = cluster.apply_topology_export_resources(resources)

        assert "rook-csi-rbd-node" in result["secrets"]
        mock_ocp_instance.create.assert_called_once()

    def test_creates_configmaps(self, cluster_setup):
        """apply_topology_export_resources should create configmaps."""
        cluster = cluster_setup
        mock_ocp_instance = MagicMock()

        with patch("ocs_ci.deployment.helpers.external_cluster_helpers.OCP", return_value=mock_ocp_instance):
            with patch("ocs_ci.deployment.helpers.external_cluster_helpers.config") as mock_config:
                mock_config.ENV_DATA = {"cluster_namespace": "openshift-storage"}

                resources = [
                    {"name": "rook-ceph-mon-endpoints", "kind": "ConfigMap", "data": {"data": "a=10.0.0.1"}},
                ]

                result = cluster.apply_topology_export_resources(resources)

        assert "rook-ceph-mon-endpoints" in result["configmaps"]

    def test_skips_unknown_kinds(self, cluster_setup):
        """apply_topology_export_resources should skip unknown resource kinds."""
        cluster = cluster_setup
        mock_ocp_instance = MagicMock()

        with patch("ocs_ci.deployment.helpers.external_cluster_helpers.OCP", return_value=mock_ocp_instance):
            with patch("ocs_ci.deployment.helpers.external_cluster_helpers.config") as mock_config:
                mock_config.ENV_DATA = {"cluster_namespace": "openshift-storage"}

                resources = [
                    {"name": "test-sc", "kind": "StorageClass", "data": {}},
                    {"name": "test-secret", "kind": "Secret", "data": {"key": "val"}},
                ]

                result = cluster.apply_topology_export_resources(resources)

        assert result["secrets"] == ["test-secret"]
        assert result["configmaps"] == []

    def test_handles_multiple_resources(self, cluster_setup):
        """apply_topology_export_resources should handle multiple resources."""
        cluster = cluster_setup
        mock_ocp_instance = MagicMock()

        with patch("ocs_ci.deployment.helpers.external_cluster_helpers.OCP", return_value=mock_ocp_instance):
            with patch("ocs_ci.deployment.helpers.external_cluster_helpers.config") as mock_config:
                mock_config.ENV_DATA = {"cluster_namespace": "openshift-storage"}

                resources = [
                    {"name": "secret-1", "kind": "Secret", "data": {}},
                    {"name": "secret-2", "kind": "Secret", "data": {}},
                    {"name": "cm-1", "kind": "ConfigMap", "data": {}},
                    {"name": "cm-2", "kind": "ConfigMap", "data": {}},
                ]

                result = cluster.apply_topology_export_resources(resources)

        assert result["secrets"] == ["secret-1", "secret-2"]
        assert result["configmaps"] == ["cm-1", "cm-2"]
        assert mock_ocp_instance.create.call_count == 4

    def test_returns_empty_for_empty_input(self, cluster_setup):
        """apply_topology_export_resources should return empty lists for empty input."""
        cluster = cluster_setup
        mock_ocp_class = MagicMock()

        with patch("ocs_ci.deployment.helpers.external_cluster_helpers.OCP", mock_ocp_class):
            with patch("ocs_ci.deployment.helpers.external_cluster_helpers.config") as mock_config:
                mock_config.ENV_DATA = {"cluster_namespace": "openshift-storage"}

                result = cluster.apply_topology_export_resources([])

        assert result == {"secrets": [], "configmaps": []}
        mock_ocp_class.assert_not_called()
