"""Tests for CephMockConnection."""

from external_cluster_mock import CephMockConnection


class TestCephMockConnection:
    """Tests for the CephMockConnection class."""

    def test_exec_cmd_records_history(self, mock_conn: CephMockConnection):
        """exec_cmd should record all commands in history."""
        mock_conn.exec_cmd("ceph osd pool ls")
        mock_conn.exec_cmd("ceph osd crush rule ls")

        assert len(mock_conn.command_history) == 2
        assert "ceph osd pool ls" in mock_conn.command_history
        assert "ceph osd crush rule ls" in mock_conn.command_history

    def test_pool_create_adds_to_state(self, mock_conn: CephMockConnection):
        """Pool create should add pool to internal state."""
        retcode, stdout, stderr = mock_conn.exec_cmd("ceph osd pool create mypool 32")

        assert retcode == 0
        assert "mypool" in mock_conn.pools

    def test_pool_ls_returns_pools(self, mock_conn: CephMockConnection):
        """Pool ls should return all pools."""
        mock_conn.pools.add("pool1")
        mock_conn.pools.add("pool2")

        retcode, stdout, stderr = mock_conn.exec_cmd("ceph osd pool ls")

        assert retcode == 0
        assert "pool1" in stdout
        assert "pool2" in stdout

    def test_crush_rule_create_adds_to_state(self, mock_conn: CephMockConnection):
        """Crush rule create should add rule to internal state."""
        retcode, stdout, stderr = mock_conn.exec_cmd(
            "ceph osd crush rule create-simple myrule default osd"
        )

        assert retcode == 0
        assert "myrule" in mock_conn.crush_rules

    def test_crush_rule_ls_returns_rules(self, mock_conn: CephMockConnection):
        """Crush rule ls should return all rules."""
        mock_conn.crush_rules.add("rule1")
        mock_conn.crush_rules.add("rule2")

        retcode, stdout, stderr = mock_conn.exec_cmd("ceph osd crush rule ls")

        assert retcode == 0
        assert "rule1" in stdout
        assert "rule2" in stdout

    def test_pool_get_returns_size(self, mock_conn: CephMockConnection):
        """Pool get size should return size for existing pool."""
        mock_conn.pools.add("testpool")

        retcode, stdout, stderr = mock_conn.exec_cmd("ceph osd pool get testpool size")

        assert retcode == 0
        assert "size: 1" in stdout

    def test_pool_get_fails_for_missing_pool(self, mock_conn: CephMockConnection):
        """Pool get should fail for non-existent pool."""
        retcode, stdout, stderr = mock_conn.exec_cmd("ceph osd pool get missing size")

        assert retcode == 1
        assert "does not exist" in stderr

    def test_pool_delete_removes_from_state(self, mock_conn: CephMockConnection):
        """Pool delete should remove pool from internal state."""
        mock_conn.pools.add("deletepool")

        retcode, stdout, stderr = mock_conn.exec_cmd(
            "ceph osd pool delete deletepool deletepool --yes-i-really-really-mean-it"
        )

        assert retcode == 0
        assert "deletepool" not in mock_conn.pools

    def test_reset_clears_all_state(self, mock_conn: CephMockConnection):
        """Reset should clear all internal state."""
        mock_conn.pools.add("pool1")
        mock_conn.crush_rules.add("rule1")
        mock_conn.config_settings["key1"] = "value1"
        mock_conn.exec_cmd("ceph osd pool ls")

        mock_conn.reset()

        assert len(mock_conn.pools) == 0
        assert len(mock_conn.crush_rules) == 0
        assert len(mock_conn.config_settings) == 0
        assert len(mock_conn.command_history) == 0

    def test_config_set_stores_value(self, mock_conn: CephMockConnection):
        """Config set should store key-value in config_settings."""
        retcode, stdout, stderr = mock_conn.exec_cmd(
            "ceph config set mon mon_allow_pool_size_one true"
        )

        assert retcode == 0
        assert mock_conn.config_settings["mon_allow_pool_size_one"] == "true"

    def test_crush_rule_rm_removes_rule(self, mock_conn: CephMockConnection):
        """Crush rule rm should remove rule from state."""
        mock_conn.crush_rules.add("removerule")

        retcode, stdout, stderr = mock_conn.exec_cmd("ceph osd crush rule rm removerule")

        assert retcode == 0
        assert "removerule" not in mock_conn.crush_rules

    def test_pool_application_enable_succeeds(self, mock_conn: CephMockConnection):
        """Pool application enable should return success."""
        retcode, stdout, stderr = mock_conn.exec_cmd(
            "ceph osd pool application enable mypool rbd"
        )

        assert retcode == 0
