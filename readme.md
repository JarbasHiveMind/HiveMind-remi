# HiveMind Remi

A small desktop GUI for testing connections to a [HiveMind](https://github.com/JarbasHiveMind/HiveMind-core)
hub. It is built with the [Remi](https://github.com/rawpython/remi) framework,
so the interface is a local web page driven by Python: fill in your hub
credentials, connect, and chat with your assistant.

![demo](./remi.gif)

## Where it sits

HiveMind is a mesh: satellite devices connect to a central
[hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core) hub over an
authenticated, encrypted protocol. Remi is a throwaway **test satellite** — it
wraps the Python [hivemind-bus-client](https://github.com/JarbasHiveMind/hivemind-websocket-client)
in a GUI so you can verify a hub and access key work, and watch utterances and
spoken replies flow, without writing any code.

```
Remi GUI (hivemind-bus-client)  ──encrypted──►  hivemind-core hub  ──►  OVOS / agent
```

## Install

```bash
pip install hivemind-remi
```

Or from source:

```bash
git clone https://github.com/JarbasHiveMind/HiveMind-remi
cd HiveMind-remi
pip install .
```

Dependencies: `remi`, `hivemind-bus-client`.

## Quickstart

### 1. Run a hub and issue an access key

On the machine hosting the assistant, install and run
[hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core):

```bash
hivemind-core add-client      # prints an access key + crypto/password key
hivemind-core listen --port 5678
```

### 2. Launch Remi

```bash
HiveMind-remi
```

Remi serves its GUI as a local web page and opens it in your browser.

### 3. Connect and chat

On the **Connect** tab, fill in:

| Field | Value |
|-------|-------|
| Host | the hub address, e.g. `ws://127.0.0.1` (use `wss://` for TLS) |
| Port | the hub's HiveMind port (default `5678`) |
| Access Key | the key from `hivemind-core add-client` |
| Crypto Key | the crypto/password key for that client |
| Language | the utterance language tag (default `en-us`) |
| Accept self signed | tick if the hub uses a self-signed TLS cert |

Click **Connect** (it waits up to 10 seconds for the handshake). When the status
reads *Connected to HiveMind!*, switch to the **Chat** tab, type a message, and
press **Send**. The assistant's spoken responses appear in the chat log.

## How it works

- `hivemind_remi.HiveMindRemi` is a `remi.App` with two tabs, **Connect** and
  **Chat**.
- On connect it builds a `HiveMessageBusClient` from the form fields
  (`key`, `host`, `port`, `crypto_key`, `ssl` inferred from a `wss://` host) and
  runs it in a background thread, blocking on `connected_event` until the
  handshake completes or times out.
- Sending a message emits a `recognizer_loop:utterance` with the chosen
  language; the app subscribes to `speak` messages and renders them back into
  the chat view.

The `ssl` flag is derived from the host scheme, and **Accept self signed** lets
you connect to a hub with a self-signed certificate during testing.

## License

Apache 2.0 — see [LICENSE](./LICENSE).
