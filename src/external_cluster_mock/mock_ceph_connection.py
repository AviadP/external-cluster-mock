"""Mock Ceph connection for testing external cluster operations."""

import re
from typing import Optional


class CephMockConnection:
    """
    Mock SSH connection that simulates Ceph command responses.

    Matches ocs_ci.utility.connection.Connection interface.
    Used to patch the real Connection class when testing ExternalCluster.

    """

    def __init__(self):
        self.pools: set[str] = set()
        self.crush_rules: set[str] = set()
        self.config_settings: dict[str, str] = {}
        self.command_history: list[str] = []
        self.max_history_size: int = 1000

    def exec_cmd(self, cmd: str, secrets: Optional[list] = None) -> tuple[int, str, str]:
        """
        Execute mock command.

        Args:
            cmd (str): Command to execute.
            secrets (list): Values to mask in command history.

        Returns:
            tuple[int, str, str]: (retcode, stdout, stderr)

        """
        masked_cmd = cmd
        if secrets:
            for secret in secrets:
                masked_cmd = masked_cmd.replace(secret, "***")

        self.command_history.append(masked_cmd)

        if len(self.command_history) > self.max_history_size:
            self.command_history.pop(0)

        return self._route_command(cmd)

    def reset(self) -> None:
        """Reset all state for test isolation."""
        self.pools.clear()
        self.crush_rules.clear()
        self.config_settings.clear()
        self.command_history.clear()

    def _route_command(self, cmd: str) -> tuple[int, str, str]:
        """
        Route command to appropriate handler.

        Args:
            cmd (str): Command to route.

        Returns:
            tuple[int, str, str]: (retcode, stdout, stderr)

        """
        if "ceph config set mon" in cmd:
            return self._handle_config_set(cmd)

        if cmd.strip() == "ceph osd crush rule ls":
            return self._handle_crush_rule_ls()

        if "ceph osd crush rule create-simple" in cmd:
            return self._handle_crush_rule_create(cmd)

        if "ceph osd crush rule rm" in cmd:
            return self._handle_crush_rule_rm(cmd)

        if cmd.strip() == "ceph osd pool ls":
            return self._handle_pool_ls()

        if "ceph osd pool create" in cmd:
            return self._handle_pool_create(cmd)

        if "ceph osd pool set" in cmd:
            return self._handle_pool_set(cmd)

        if "ceph osd pool get" in cmd and "size" in cmd:
            return self._handle_pool_get(cmd)

        if "ceph osd pool delete" in cmd:
            return self._handle_pool_delete(cmd)

        if "ceph osd pool application enable" in cmd:
            return self._handle_pool_app_enable()

        return (1, "", f"Unknown command: {cmd}")

    def _handle_config_set(self, cmd: str) -> tuple[int, str, str]:
        """
        Handle ceph config set mon <key> <value>.

        Args:
            cmd (str): The config set command.

        Returns:
            tuple[int, str, str]: (retcode, stdout, stderr)

        """
        match = re.search(r"ceph config set mon (\S+) (\S+)", cmd)
        if not match:
            return (1, "", "Invalid config set command")

        key, value = match.groups()
        self.config_settings[key] = value
        return (0, "", "")

    def _handle_crush_rule_ls(self) -> tuple[int, str, str]:
        """
        Handle ceph osd crush rule ls.

        Returns:
            tuple[int, str, str]: (retcode, stdout, stderr)

        """
        output = "\n".join(sorted(self.crush_rules))
        return (0, output, "")

    def _handle_crush_rule_create(self, cmd: str) -> tuple[int, str, str]:
        """
        Handle ceph osd crush rule create-simple <name> ...

        Args:
            cmd (str): The create command.

        Returns:
            tuple[int, str, str]: (retcode, stdout, stderr)

        """
        match = re.search(r"ceph osd crush rule create-simple (\S+)", cmd)
        if not match:
            return (1, "", "Invalid crush rule create command")

        rule_name = match.group(1)
        if rule_name in self.crush_rules:
            return (0, "", f"rule {rule_name} already exists")

        self.crush_rules.add(rule_name)
        return (0, "", "")

    def _handle_crush_rule_rm(self, cmd: str) -> tuple[int, str, str]:
        """
        Handle ceph osd crush rule rm <name>.

        Args:
            cmd (str): The remove command.

        Returns:
            tuple[int, str, str]: (retcode, stdout, stderr)

        """
        match = re.search(r"ceph osd crush rule rm (\S+)", cmd)
        if not match:
            return (1, "", "Invalid crush rule rm command")

        rule_name = match.group(1)
        if rule_name not in self.crush_rules:
            return (1, "", f"rule '{rule_name}' does not exist")

        self.crush_rules.discard(rule_name)
        return (0, "", "")

    def _handle_pool_ls(self) -> tuple[int, str, str]:
        """
        Handle ceph osd pool ls.

        Returns:
            tuple[int, str, str]: (retcode, stdout, stderr)

        """
        output = "\n".join(sorted(self.pools))
        return (0, output, "")

    def _handle_pool_create(self, cmd: str) -> tuple[int, str, str]:
        """
        Handle ceph osd pool create <name> ...

        Args:
            cmd (str): The create command.

        Returns:
            tuple[int, str, str]: (retcode, stdout, stderr)

        """
        match = re.search(r"ceph osd pool create (\S+)", cmd)
        if not match:
            return (1, "", "Invalid pool create command")

        pool_name = match.group(1)
        if pool_name in self.pools:
            return (0, f"pool '{pool_name}' already exists", "")

        self.pools.add(pool_name)
        return (0, f"pool '{pool_name}' created", "")

    def _handle_pool_set(self, cmd: str) -> tuple[int, str, str]:
        """
        Handle ceph osd pool set <name> ...

        Args:
            cmd (str): The set command.

        Returns:
            tuple[int, str, str]: (retcode, stdout, stderr)

        """
        match = re.search(r"ceph osd pool set (\S+)", cmd)
        if not match:
            return (1, "", "Invalid pool set command")

        pool_name = match.group(1)
        if pool_name not in self.pools:
            return (1, "", f"pool '{pool_name}' does not exist")

        return (0, "", "")

    def _handle_pool_get(self, cmd: str) -> tuple[int, str, str]:
        """
        Handle ceph osd pool get <name> size.

        Args:
            cmd (str): The get command.

        Returns:
            tuple[int, str, str]: (retcode, stdout, stderr)

        """
        match = re.search(r"ceph osd pool get (\S+) size", cmd)
        if not match:
            return (1, "", "Invalid pool get command")

        pool_name = match.group(1)
        if pool_name not in self.pools:
            return (1, "", f"pool '{pool_name}' does not exist")

        return (0, "size: 1", "")

    def _handle_pool_delete(self, cmd: str) -> tuple[int, str, str]:
        """
        Handle ceph osd pool delete <name> ...

        Args:
            cmd (str): The delete command.

        Returns:
            tuple[int, str, str]: (retcode, stdout, stderr)

        """
        match = re.search(r"ceph osd pool delete (\S+)", cmd)
        if not match:
            return (1, "", "Invalid pool delete command")

        pool_name = match.group(1)
        if pool_name not in self.pools:
            return (1, "", f"pool '{pool_name}' does not exist")

        self.pools.discard(pool_name)
        return (0, f"pool '{pool_name}' removed", "")

    def _handle_pool_app_enable(self) -> tuple[int, str, str]:
        """
        Handle ceph osd pool application enable ...

        Returns:
            tuple[int, str, str]: (retcode, stdout, stderr)

        """
        return (0, "enabled", "")


def _type_check() -> None:
    """Verify CephMockConnection implements CephConnectionProtocol."""
    from .protocols import CephConnectionProtocol

    _: CephConnectionProtocol = CephMockConnection()
