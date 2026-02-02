# External Cluster Mock

Mock Ceph connection for testing ExternalCluster replica-1 operations.

## Installation

```bash
pip install -e .

# With test dependencies
pip install -e ".[test]"
```

## Interface

The mock implements `CephConnectionProtocol`:

```python
from external_cluster_mock import CephConnectionProtocol

def my_function(conn: CephConnectionProtocol) -> None:
    retcode, stdout, stderr = conn.exec_cmd("ceph osd pool ls")
```

You can also use runtime checks:

```python
from external_cluster_mock import CephConnectionProtocol, CephMockConnection

conn = CephMockConnection()
assert isinstance(conn, CephConnectionProtocol)  # True
```

## Standalone Usage

```python
from external_cluster_mock import CephMockConnection

# Create mock
conn = CephMockConnection()

# Execute commands
retcode, stdout, stderr = conn.exec_cmd("ceph osd pool create mypool 32")
assert retcode == 0
assert "mypool" in conn.pools

# Check command history
assert "ceph osd pool create mypool 32" in conn.command_history

# Reset state between tests
conn.reset()
```

## Usage with ocs-ci (optional)

If testing with ocs-ci's ExternalCluster:

```python
from unittest.mock import patch
from external_cluster_mock import CephMockConnection

mock_conn = CephMockConnection()

with patch("ocs_ci.deployment.helpers.external_cluster_helpers.Connection"):
    from ocs_ci.deployment.helpers.external_cluster_helpers import ExternalCluster
    cluster = ExternalCluster(host="x", user="y", password="z")
    cluster.rhcs_conn = mock_conn

    cluster.enable_replica_one_pools()

    assert "ceph config set mon mon_allow_pool_size_one true" in mock_conn.command_history
```

## Supported Commands

| Command Pattern | Behavior |
|-----------------|----------|
| `ceph config set mon <key> <val>` | Stores in `config_settings` |
| `ceph osd crush rule ls` | Returns newline-joined `crush_rules` |
| `ceph osd crush rule create-simple <name> ...` | Adds to `crush_rules` |
| `ceph osd crush rule rm <name>` | Removes from `crush_rules` |
| `ceph osd pool ls` | Returns newline-joined `pools` |
| `ceph osd pool create <name> ...` | Adds to `pools` |
| `ceph osd pool set <name> ...` | Returns success |
| `ceph osd pool get <name> size` | Returns `size: 1` or error |
| `ceph osd pool delete <name> ...` | Removes from `pools` |
| `ceph osd pool application enable ...` | Returns success |

## Running Tests

```bash
pytest tests/ -v
```
