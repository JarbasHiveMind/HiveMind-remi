# Running tests

There is a single test directory, `tests/`, split into two tiers:

| Path | Tier | Extra | What it does |
|------|------|-------|--------------|
| `tests/test_smoke.py` | smoke | `[test]` | Network-free: import, version, app construction, and that `connect()` builds the client and `say()` no-ops when disconnected (the `HiveMessageBusClient` is mocked). Runs across the full Python matrix. |
| `tests/e2e/` | end-to-end | `[e2e]` | Boots a **real** hivemind-core server and drives the **real** remi client over a real `HiveMessageBusClient`. Runs on Python 3.11. |

## Smoke tests

```bash
pip install -e ".[test]"
pytest tests/test_smoke.py
```

## End-to-end tests

```bash
pip install -e ".[e2e]"     # see docs/dependencies.md (prerelease floors; no --pre)
pytest tests/e2e/
```

### What is real and what is mocked

The e2e suite (`tests/e2e/test_remi_hivemind_e2e.py`) exercises the genuine
production path end to end:

```
browser click (mocked GUI surface)
  → HiveMindRemi.connect() / .say()           # the REAL client logic
  → the REAL HiveMessageBusClient it builds
  → real localhost WebSocket
  → real hivemind-core server (hivescope loopback)
  → agent bus
```

and the reverse for `speak`. Everything between the remi client and the server
is the real HiveMessageBusClient + hivemind-core stack over a localhost
WebSocket (hivescope's `TopologyBuilder().add_master(use_loopback=True)`).

Only two seams are mocked:

1. **The remi browser/GUI surface.** `remi.App.__init__` wires an HTTP request
   handler and the widget tree is normally driven by a real browser. The tests
   build the app with `HiveMindRemi.__new__(...)` (skipping that initialiser)
   and substitute plain stand-in objects for the form fields, the chat
   container, and the status label. The HiveMind logic (`connect`, `say`,
   `handle_speak`) runs unchanged — no browser, no websocket-to-browser, no
   rendered DOM.
2. **Any network beyond localhost.** None is touched; the only socket opened is
   the loopback WebSocket to the in-process hivemind-core server.

There is **no `importorskip` / `skipif`** — the full 2.x stack is a hard `[e2e]`
dependency, so a missing dependency is a hard failure, not a silent skip.

### Coverage

The `tests/conftest.py` hook loudly flags any `xfail` test that starts passing.
CI also runs the whole suite (smoke + e2e) under coverage via the shared
`coverage.yml` workflow with the `e2e` extra.

## How CI runs these

| Workflow | Runs |
|----------|------|
| `build_tests.yml` | smoke (`tests/test_smoke.py`, `[test]`) across Python 3.10–3.12 |
| `e2e_tests.yml` | e2e (`tests/e2e/`, `[e2e]`) on Python 3.11 |
| `coverage.yml` | full `tests/` under coverage (`[e2e]`) on Python 3.11 |
| `lint.yml` | `ruff check` |
| `pip_audit.yml` | dependency vulnerability audit |
| `repo-health.yml` / `release_preview.yml` | repo hygiene + next-version preview |

All reusable workflows are referenced at `OpenVoiceOS/gh-automations@dev`.
