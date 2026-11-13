# HiveMind-remi documentation

HiveMind-remi is a [Remi](https://github.com/rawpython/remi)-based **web GUI**
client for HiveMind. Remi renders a Python-defined UI as a local web page, so
the whole interface (connection form and chat view) is plain Python with no
HTML/JS to write. It is a throwaway **test satellite**: connect to a
[hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core) server with an
access key and chat with the assistant from the browser.

## Contents

- [Installation](./installation.md): install from PyPI or source, supported
  Python versions.
- [Configuration](./configuration.md): the Connect-tab fields and how the
  client maps them onto the HiveMind bus client.
- [Architecture](./architecture.md): the remi web-GUI design, the two-tab app,
  and how it connects to hivemind-core.
- [Dependencies](./dependencies.md): the 2.x stack and the prerelease-floor
  version policy (pyproject is the single source of truth).
- [Running tests](./testing.md): the smoke suite and the HiveMind-side
  end-to-end suite (real hivemind-core over a loopback WebSocket).

## At a glance

```
Remi web GUI (hivemind-bus-client)  ──encrypted──►  hivemind-core  ──►  OVOS / agent
```

The GUI builds a real `HiveMessageBusClient`, completes the encrypted HiveMind
handshake against a hivemind-core server, emits `recognizer_loop:utterance` for
each message you send, and renders incoming `speak` messages back into the chat
view.
