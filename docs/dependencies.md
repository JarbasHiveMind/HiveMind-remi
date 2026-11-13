# Dependencies

`pyproject.toml` is the **single source of truth** for packaging. There is no
`requirements.txt`, `setup.py`, `setup.cfg`, or `MANIFEST.in`. Runtime deps
live in `[project.dependencies]`, test deps in `[project.optional-dependencies]`,
and the static `res/` assets ship via `[tool.setuptools.package-data]`.

## Runtime dependencies

| Package | Constraint | Why |
|---------|-----------|-----|
| `hivemind-bus-client` | `>=0.9.2a1,<1.0.0` | The 2.x-stack client: `NodeIdentity`-backed, derives `ssl` from the host scheme. |
| `ovos-bus-client` | `>=2.0.0a3,<3.0.0` | Message type. The 0.9.x bus client requires `>=2.0.0a3`. |
| `remi` | (unpinned) | The web-GUI framework. Caps the supported Python to `<3.13` (it imports the removed-in-3.13 stdlib `cgi`). |
| `ovos-utils` | (unpinned) | Logging (`LOG`). |
| `setuptools` | `<81` | remi imports `pkg_resources` at runtime. setuptools removed it in 81. |

## Test extras

- **`test`**: `pytest` only. Network-free smoke tests that run across the full
  Python matrix in CI.
- **`e2e`**: the full HiveMind-side end-to-end stack: `hivescope`,
  `hivemind-core`, `pytest-timeout`, plus the sibling prereleases hivemind-core
  pulls in. Boots a real hivemind-core server over a loopback WebSocket and
  drives the real remi client. See [testing](./testing.md).

## Version policy: prerelease floors

The 2.x HiveMind stack is still on alpha releases. Per org policy, a prerelease
dependency is declared by pinning it as the **minimum** version
(`pkg>=X.Ya1`), never by forcing `--pre` or adding `pre_install_pip` hacks. pip
and uv then resolve the prerelease with no extra flags.

The `[e2e]` extra also pins the floors of the sibling packages hivemind-core
depends on transitively: `json-database`, `hivemind-plugin-manager`,
`hivemind-sqlite-database`, `hivemind-websocket-protocol`,
`hivemind-json-db-plugin`, `hivemind-ovos-agent-plugin`. Without those
explicit floors a plain install refuses the transitive `aN` constraints (the
prerelease is not "enabled" for a package no top-level requirement names).
Pinning each floor enables exactly those prereleases with **no global
`--pre`**.

This resolves cleanly under uv:

```bash
uv venv --python 3.11 .venv
uv pip install -e ".[e2e]"     # no --pre needed
```

---
[← Architecture](architecture.md) · [Home](index.md) · [Running tests →](testing.md)
