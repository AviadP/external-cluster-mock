"""Protocols defining Ceph connection interfaces."""

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class CephConnectionProtocol(Protocol):
    """
    Protocol for Ceph SSH connection interface.

    Defines the contract for classes that execute Ceph commands via SSH.
    This protocol matches the interface of ocs_ci.utility.connection.Connection.

    Attributes:
        pools (set[str]): Set of pool names.
        crush_rules (set[str]): Set of crush rule names.
        config_settings (dict[str, str]): Configuration key-value pairs.
        command_history (list[str]): List of executed commands.
        max_history_size (int): Maximum commands to retain in history.

    """

    pools: set[str]
    crush_rules: set[str]
    config_settings: dict[str, str]
    command_history: list[str]
    max_history_size: int

    def exec_cmd(
        self, cmd: str, secrets: Optional[list] = None
    ) -> tuple[int, str, str]:
        """
        Execute a command.

        Args:
            cmd (str): Command to execute.
            secrets (Optional[list]): Values to mask in logs.

        Returns:
            tuple[int, str, str]: (return_code, stdout, stderr)

        """
        ...

    def reset(self) -> None:
        """Reset connection state."""
        ...
