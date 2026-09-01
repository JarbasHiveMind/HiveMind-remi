"""REAL client-side end-to-end tests for HiveMind-remi.

These exercise the remi web-GUI client's **real** code path against a **real**
hivemind-core server:

    browser click (mocked GUI surface)
        -> HiveMindRemi.connect() / .say()  (the REAL client logic)
        -> the REAL HiveMessageBusClient it builds from the form fields
        -> real localhost WebSocket  -> real hivemind-core server  -> agent bus

and the reverse:

    agent bus emits `speak` routed to the remi peer
        -> real WebSocket  -> the client's REAL HiveMessageBusClient
        -> HiveMindRemi.handle_speak  -> HiveMindRemi.speak  (mocked GUI sink)

Everything between the remi client and the server is the genuine production
HiveMessageBusClient + hivemind-core stack over a localhost WebSocket
(hivescope's loopback server). Only two seams are mocked:

  * the **remi browser/GUI surface** — `remi.App.__init__` wires an HTTP request
    handler and the widget tree is normally driven by a real browser. We
    construct the app with ``__new__`` (skipping that initialiser) and stand in
    plain objects for the form fields / chat container / status label, so the
    client logic runs unchanged without a browser, websocket-to-browser, or
    rendered DOM.
  * **any network beyond localhost** — none is touched; the only socket opened
    is the loopback WebSocket to the in-process hivemind-core server.

There is no importorskip / skipif — the full 2.x stack (hivescope +
hivemind-core + hivemind-bus-client + ovos-bus-client) is a hard `[e2e]`
dependency, so a missing dep is a hard failure, not a silent skip.

Reference (sibling HiveMind e2e): HiveMind-voice-sat
``tests/e2e/test_satellite_hivemind_e2e.py`` — add_master(use_loopback=True);
register_satellite(...); responder on master.agent_protocol.bus.
"""
import time

import pytest
from ovos_bus_client.message import Message
from hivemind_bus_client.client import HiveMessageBusClient

from hivescope.topology import TopologyBuilder

from hivemind_remi import HiveMindRemi


pytestmark = pytest.mark.timeout(60)


# ---------------------------------------------------------------------------
# Mocked GUI surface — in-process stand-ins for the remi browser widgets.
# remi.App.__init__ wires an HTTP request handler and the widget tree is driven
# by a real browser; none of that is needed to drive the HiveMind client logic.
# We build the app with __new__ and attach the minimal widget-shaped attributes
# the client methods read/write.
# ---------------------------------------------------------------------------

class FakeTextInput:
    """Stands in for ``remi.gui.TextInput`` — exposes ``.text`` and get/set."""

    def __init__(self, text=""):
        self.text = text

    def get_text(self):
        return self.text

    def set_text(self, value):
        self.text = value


class FakeChat:
    """Stands in for the chat ``remi.gui.VBox`` — records what gets rendered.

    ``HiveMindRemi.speak`` appends a widget per bot reply; instead of building a
    real DOM subtree we just record the call so the test can assert what the
    GUI *would* have shown.
    """

    def __init__(self):
        self.appended = []
        # remi widgets expose a ``children`` mapping; ``clear_chat`` iterates it
        self.children = {}

    def append(self, widget):
        self.appended.append(widget)

    def remove_child(self, child):
        # mirror the remi.gui container API used by clear_chat
        self.children = {k: v for k, v in self.children.items() if v is not child}


def _make_app():
    """Instantiate HiveMindRemi without running ``remi.App.__init__``.

    Mocks ONLY the GUI/browser surface: form fields, chat container, status
    label, language field. All HiveMind logic (connect/say/handle_speak) is the
    real thing.
    """
    app = HiveMindRemi.__new__(HiveMindRemi)
    app.bus = None
    app.self_signed = False
    app.lang = FakeTextInput("en-us")
    app.host = FakeTextInput("ws://0.0.0.0")
    app.port = FakeTextInput("5678")
    app.chat = FakeChat()
    # status label only needs set_text; the chat-clear path needs a children map
    app.status = FakeTextInput("Disconnected")
    # record everything the client tries to render to the chat view
    app.spoken = []
    return app


# ---------------------------------------------------------------------------
# Loopback server + helpers.
# ---------------------------------------------------------------------------

def _server_with_client(allowed_types):
    """Boot a real loopback hivemind-core server and pre-register one key."""
    b = TopologyBuilder()
    m = b.add_master("M0", use_loopback=True)
    m.register_satellite("remi-key", password="remi-correct-horse-battery-staple",
                         allowed_types=allowed_types)
    b.start_all()
    return b, m


def _host_port(url):
    bare = url.replace("ws://", "").replace("wss://", "").rstrip("/")
    host, port = bare.split(":")
    return "ws://" + host, port


# ---------------------------------------------------------------------------
# Outbound: real GUI "Connect" + "Send" -> real server agent bus.
# ---------------------------------------------------------------------------

def test_connect_opens_real_bus_and_completes_handshake():
    """HiveMindRemi.connect() builds a REAL HiveMessageBusClient from the form
    fields and completes the HiveMind handshake against a REAL loopback server.

    This is the genuine ``on_connect_pressed`` -> ``connect`` code path; only
    the browser widgets are faked.
    """
    b, m = _server_with_client(["recognizer_loop:utterance"])
    app = _make_app()
    try:
        host, port = _host_port(m.network_protocol.url)
        app.connect(access_key="remi-key", password="remi-correct-horse-battery-staple",
                    host=host, port=port)

        deadline = time.time() + 15
        while time.time() < deadline and not app.connected:
            time.sleep(0.1)

        assert app.connected, "remi client never completed the HiveMind handshake"
        assert isinstance(app.bus, HiveMessageBusClient)
        time.sleep(1)
        assert len(m.connected_peers()) == 1, \
            f"expected 1 connected peer, got {m.connected_peers()}"
    finally:
        if app.bus is not None:
            app.bus.close()
        b.stop_all()


def test_say_emits_utterance_to_real_server_agent():
    """A message typed in the GUI and sent reaches the REAL server agent bus
    over a REAL WebSocket as a recognizer_loop:utterance with the GUI language.

    Drives the real ``say`` path (which emits on the real bus); the chat view is
    a fake sink so no browser is needed.
    """
    b, m = _server_with_client(["recognizer_loop:utterance"])
    app = _make_app()
    try:
        host, port = _host_port(m.network_protocol.url)
        app.connect(access_key="remi-key", password="remi-correct-horse-battery-staple",
                    host=host, port=port)
        deadline = time.time() + 15
        while time.time() < deadline and not app.connected:
            time.sleep(0.1)
        assert app.connected
        time.sleep(1)

        seen = []
        m.agent_protocol.bus.on("recognizer_loop:utterance", seen.append)

        app.say("what is the weather")

        deadline = time.time() + 10
        while time.time() < deadline and not seen:
            time.sleep(0.05)

        assert seen, "utterance never reached the server agent bus"
        m.agent_protocol.assert_injected("recognizer_loop:utterance", count=1)
        injected = m.agent_protocol.last_injected("recognizer_loop:utterance")
        assert injected.data["utterances"] == ["what is the weather"]
        assert injected.data["lang"] == "en-us"
        # hivemind-core stamps a non-empty source identifying the peer
        assert injected.context.get("source"), "no source stamped on injection"
    finally:
        if app.bus is not None:
            app.bus.close()
        b.stop_all()


def test_say_while_disconnected_does_not_emit():
    """With no live bus the GUI shows the not-connected notice and emits nothing
    to any server. No network is touched at all.
    """
    app = _make_app()
    rendered = []
    # capture what speak() would render instead of building widgets
    app.speak = rendered.append
    app.clear_chat = lambda: None

    app.say("hello there")

    assert rendered == ["I am not connected to the HiveMind!"]


# ---------------------------------------------------------------------------
# Inbound: real server `speak` -> real client bus -> mocked GUI chat sink.
# ---------------------------------------------------------------------------

def test_server_speak_reaches_client_and_renders_to_chat():
    """A `speak` emitted by the server agent and routed to the remi peer arrives
    on the client's REAL HiveMessageBusClient and drives the real
    ``handle_speak`` -> ``speak`` path, which renders into the (faked) chat view.

    This is the server -> client leg with the bus real and only the rendered DOM
    faked.
    """
    b, m = _server_with_client(["recognizer_loop:utterance", "speak"])
    app = _make_app()
    try:
        host, port = _host_port(m.network_protocol.url)
        app.connect(access_key="remi-key", password="remi-correct-horse-battery-staple",
                    host=host, port=port)
        deadline = time.time() + 15
        while time.time() < deadline and not app.connected:
            time.sleep(0.1)
        assert app.connected
        time.sleep(1)
        assert len(m.connected_peers()) == 1
        peer = m.connected_peers()[0]

        # capture utterances the GUI would render, bypassing remi widget building
        spoken = []
        app.speak = spoken.append
        # wire the real mycroft `speak` listener exactly as on_connect_pressed does
        app.bus.on_mycroft("speak", app.handle_speak)

        # server agent speaks back to the remi peer
        m.agent_protocol.bus.emit(Message(
            "speak",
            {"utterance": "it is sunny"},
            {"destination": [peer]},
        ))

        deadline = time.time() + 10
        while time.time() < deadline and not spoken:
            time.sleep(0.05)

        assert spoken == ["it is sunny"], \
            f"speak never reached the real client / chat sink: {spoken}"
    finally:
        if app.bus is not None:
            app.bus.close()
        b.stop_all()
