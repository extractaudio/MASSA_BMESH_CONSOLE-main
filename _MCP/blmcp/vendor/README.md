# Vendored Dependencies

This directory holds source snapshots used by the Massa Blender MCP server.

## NodeToPython

- Upstream: <https://github.com/BrendanParmer/NodeToPython>
- Version: `v4.1.0`
- License: GPL-3.0-or-later
- Used by: `ntp_snapshot_graph`
- Refresh:

```bash
uv run --project _MCP python _Scripts/vendor_nodetopython.py
```

## geonodes

- Upstream: <https://github.com/al1brn/geonodes>
- Version: pinned to the commit recorded in `geonodes/.vendored_commit`
- License: GPL-3.0. The pinned upstream snapshot does not currently include a
  root `LICENSE` file, so `_Scripts/vendor_geonodes.py` writes an SPDX license
  notice to `geonodes/LICENSE` after cloning.
- Used by: `geonodes_*` reference and execution tools
- Refresh:

```bash
uv run --project _MCP python _Scripts/vendor_geonodes.py
```
