# Architecture

HiveMind-remi is a single [Remi](https://github.com/rawpython/remi) application
that doubles as a HiveMind satellite. This page explains the web-GUI design and
how the client connects to hivemind-core.

## The remi web-GUI model

Remi is a Python GUI library that renders its widget tree as a **local web
page** and drives it over a websocket to the browser. The developer writes only
Python, no HTML/JS. `remi.start(HiveMindRemi, standalone=True)` (in
`hivemind_remi/__main__.py`) starts that local HTTP/websocket server and opens
the page in the default browser.

`hivemind_remi.HiveMindRemi` subclasses `remi.App`. Its `main()` builds the
widget tree: a logo image and a `TabBox` with two tabs.

```
HiveMindRemi (remi.App)
└── VBox
    ├── Image  (HiveMind logo)
    └── TabBox
        ├── "Connect"  → get_connect_page()   # host/port/key/password/crypto/lang/self-signed form
        └── "Chat"     → get_chat_page()       # scrolling chat VBox + input box + Send
```

Browser interactions arrive as remi widget callbacks:

- `on_connect_pressed` → `connect(...)`
- `on_send_pressed` → `say(...)`
- `self_signed_toggle` → flips the `self_signed` flag

The static assets (logo, chat/speech-bubble icons) are served from the package's
`res/` directory, registered via `static_file_path={'pics': …}` in `__init__`
and referenced as `/pics:<file>`.

## Connection to hivemind-core

The GUI is a thin shell over a real
[hivemind-bus-client](https://github.com/JarbasHiveMind/hivemind-websocket-client)
`HiveMessageBusClient`. There is no intermediate process. The remi app **is**
the satellite.

```
                        recognizer_loop:utterance
  ┌───────────────┐   ───────────────────────────►   ┌──────────────┐      ┌─────────────┐
  │  Remi web GUI │     encrypted HiveMind proto      │ hivemind-core│ ───► │ OVOS / agent│
  │  (HiveMessage │   ◄───────────────────────────    │   server     │ ◄─── │     bus     │
  │   BusClient)  │            speak                   └──────────────┘      └─────────────┘
  └───────────────┘
```

### Outbound: sending a message

`say(utterance)` clears the chat, renders the user bubble, and, if connected,
emits a `recognizer_loop:utterance` `Message` on the bus carrying
`{"utterances": [utterance], "lang": <Language field>}`. hivemind-core decrypts
it, stamps a `source` identifying this peer, and injects it onto the assistant's
agent bus. If not connected, `say` instead renders *"I am not connected to the
HiveMind!"* and emits nothing.

### Inbound: receiving a reply

On a successful connect the app subscribes with
`bus.on_mycroft("speak", self.handle_speak)`. When the agent emits a `speak`
destined for this peer, hivemind-core routes it back over the encrypted
WebSocket. `handle_speak` extracts `message.data["utterance"]` and `speak()`
renders a bot bubble into the chat view.

### Connection lifecycle

`connect()` always builds a **fresh** client. The 0.9.x `HiveMessageBusClient`
is `NodeIdentity`-backed and derives `ssl` from the host scheme, so a previous
client is closed and discarded rather than reconfigured. `bus.connect()` runs
the socket loop in a background thread and blocks on the HiveMind handshake.
The `connected` property is true only once **both** `connected_event` and
`handshake_event` are set.

## Why it is "throwaway"

There is no persistence, no audio, and no wake word, just a form and a chat
log. Its job is to confirm that a server address and access key work and to
watch utterances and replies flow, which makes it useful for validating a
hivemind-core deployment before wiring up a real satellite.

---
[← Configuration](configuration.md) · [Home](index.md) · [Dependencies →](dependencies.md)
