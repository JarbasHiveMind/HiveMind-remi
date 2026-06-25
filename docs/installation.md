# Installation

## From PyPI

```bash
pip install hivemind-remi
```

This installs the `HiveMind-remi` console entry point.

## From source

```bash
git clone https://github.com/JarbasHiveMind/HiveMind-remi
cd HiveMind-remi
pip install .
```

For a development checkout (editable, with the test extras):

```bash
pip install -e ".[test]"      # smoke tests
pip install -e ".[e2e]"       # full HiveMind-side end-to-end stack
```

## Supported Python versions

`>=3.10,<3.13`.

The upper bound is dictated by the upstream `remi` GUI library (last released
2022), which still does `import cgi` — a module removed from the standard
library in Python 3.13. There is no maintained remi release that runs on 3.13,
so this client is capped below it until/unless remi is replaced. The same cap is
why `setuptools` is pinned `<81` (remi imports `pkg_resources` at runtime, which
setuptools removed in 81).

## Running it

```bash
HiveMind-remi
```

Remi serves the GUI as a local web page and opens it in your browser. See
[Configuration](./configuration.md) for what to enter on the Connect tab, and
[Quickstart in the README](../readme.md#quickstart) for bringing up a
hivemind-core server to connect to.
