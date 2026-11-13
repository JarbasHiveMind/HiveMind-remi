from os.path import join, dirname

import remi
import remi.gui as gui
from ovos_bus_client import Message
from ovos_utils.log import LOG

from hivemind_bus_client import HiveMessageBusClient

from hivemind_remi.version import __version__


class HiveMindRemi(remi.App):
    platform = f"HiveMindRemiV{__version__}"
    bus = None
    self_signed = False

    def __init__(self, *args, **kwargs):
        super().__init__(static_file_path={'pics': join(dirname(__file__), "res")},
                         *args, **kwargs)

    @property
    def connected(self) -> bool:
        """True once the websocket is open and the HiveMind handshake completed."""
        return bool(self.bus
                    and self.bus.connected_event.is_set()
                    and self.bus.handshake_event.is_set())

    # hivemind
    def connect(self, access_key, host="ws://127.0.0.1", port=5678,
                password=None, crypto_key=None, self_signed=None):
        if self_signed is not None:
            self.self_signed = self_signed

        # The 0.9.x client derives ssl from the host scheme and is backed by a
        # NodeIdentity, so connection params can't be mutated in place. Tear down
        # any previous client and build a fresh one on every (re)connect.
        if self.bus is not None:
            try:
                self.bus.close()
            except Exception as e:
                LOG.debug(f"error closing previous HiveMind client: {e}")
            self.bus = None

        port = int(port) if port else 5678
        self.bus = HiveMessageBusClient(key=access_key,
                                        password=password,
                                        crypto_key=crypto_key or None,
                                        host=host,
                                        port=port,
                                        useragent=self.platform,
                                        self_signed=self.self_signed)

        # connect() runs the client in a background thread and blocks until the
        # HiveMind handshake completes (or raises on timeout).
        LOG.info("Waiting for HiveMind connection")
        self.bus.connect()

    # mycroft
    def handle_speak(self, message):
        utterance = message.data["utterance"]
        self.speak(utterance)

    def speak(self, utterance):
        bot = gui.HBox()
        bot_img = gui.Image("/pics:chatbot.svg",
                            height=30, margin='10px')
        bot_utt = gui.Label(text=utterance, width="80%")
        bot.append([bot_img, bot_utt])
        self.chat.append(bot)

    def say(self, utterance):
        self.clear_chat()
        user = gui.HBox()
        user_img = gui.Image("/pics:speech-bubble-line.svg",
                             height=30, margin='10px')
        user_utt = gui.Label(text=utterance, width="80%")
        user.append([user_utt, user_img])

        self.chat.append(user)

        if not self.connected:
            self.speak("I am not connected to the HiveMind!")
        else:
            self.bus.emit(Message("recognizer_loop:utterance",
                                  {"utterances": [utterance],
                                   "lang": self.lang.text}))

    # build GUI
    def get_connect_page(self):
        creds_page = gui.VBox(width='100%', height='100%', margin='auto',
                              style={'display': 'block', 'overflow': 'hidden'})

        form = gui.VBox(margin='30px')

        hostbox = gui.HBox()
        self.host = gui.TextInput(height=30, width=300)
        self.host.set_text("ws://0.0.0.0")
        hostbox.append([gui.Label("Host", width="100"), self.host])

        portbox = gui.HBox()
        self.port = gui.TextInput(height=30, width=300)
        self.port.set_text("5678")
        portbox.append([gui.Label("Port", width="100"), self.port])

        accessbox = gui.HBox()
        self.key = gui.TextInput(height=30, width=300)
        accessbox.append([gui.Label("Access Key", width="100"), self.key])

        passwordbox = gui.HBox()
        self.password = gui.TextInput(height=30, width=300)
        passwordbox.append([gui.Label("Password", width="100"), self.password])

        cryptobox = gui.HBox()
        self.crypto = gui.TextInput(height=30, width=300)
        cryptobox.append([gui.Label("Crypto Key", width="100"), self.crypto])

        langbox = gui.HBox()
        self.lang = gui.TextInput(height=30, width=300)
        self.lang.set_text("en-us")
        langbox.append([gui.Label("Language", width="100"), self.lang])

        statusbox = gui.HBox()
        connectbt = gui.Button('Connect', width=200, height=30)
        connectbt.onclick.connect(self.on_connect_pressed)
        self.status = gui.Label("Status", width="100")
        self.status.set_text("Disconnected")
        statusbox.append([gui.Label("Status", width="100"), self.status, connectbt])

        certbox = gui.HBox()
        self.cert = gui.CheckBox(height=30, width=300)
        self.cert.onchange.connect(self.self_signed_toggle)
        certbox.append([gui.Label("Accept self signed", width="100"), self.cert])

        form.append([hostbox, portbox, accessbox, passwordbox, cryptobox, langbox, statusbox, certbox])
        creds_page.append(form)
        return creds_page

    def get_chat_page(self):
        # --access-key f30935cc4493b15f2c3e85382e1f9bbc --crypto-key 43c4f64f936c6176
        chat_page = gui.VBox(width='100%', height='100%', margin='0px auto',
                             style={'display': 'block', 'overflow': 'hidden'})

        self.chat = gui.VBox(width='100%', height=300, margin='0px auto')
        bot = gui.HBox()
        bot_img = gui.Image("/pics:chatbot.svg",
                            height=30, margin='10px')
        bot_utt = gui.Label(text="Ask me something", width=100)
        bot.append([bot_img, bot_utt])
        self.chat.append(bot)

        inputbox = gui.HBox(width='80%', margin='0px auto')
        self.utterance = gui.TextInput(height=30)
        bt = gui.Button('Send', width=200, height=30)
        bt.onclick.connect(self.on_send_pressed)
        inputbox.append([self.utterance, bt])

        chat_page.append([self.chat, inputbox])
        return chat_page

    def main(self, name='HiveMindRemi'):
        wid = gui.VBox(width='100%', height='100%', margin='0px auto',
                       style={'display': 'block', 'overflow': 'hidden'})
        img = gui.Image("/pics:hivemind-128.png",
                        height=100, margin='10px auto')
        tabs = gui.TabBox(width='90%', height='90%', margin='0px auto',
                          style={'display': 'block', 'overflow': 'hidden'})
        tabs.add_tab(self.get_connect_page(), 'Connect')
        tabs.add_tab(self.get_chat_page(), 'Chat')

        wid.append([img, tabs])
        return wid

    def clear_chat(self):
        for c in list(self.chat.children.values()):
            self.chat.remove_child(c)

    # listener functions
    def self_signed_toggle(self, _, val):
        self.self_signed = val

    def on_send_pressed(self, _):
        self.say(self.utterance.get_text())
        self.utterance.set_text('')

    def on_connect_pressed(self, _):
        self.status.set_text("Connecting")
        try:
            self.connect(access_key=self.key.text,
                         password=self.password.text or None,
                         crypto_key=self.crypto.text,
                         port=self.port.text,
                         host=self.host.text)
        except Exception as e:
            LOG.error(f"failed to connect to HiveMind: {e}")
            self.status.set_text(f"Connection failed: {e}")
            return

        if self.connected:
            scheme = "wss" if self.host.text.startswith("wss:") else "ws"
            LOG.info(f"Connected to HiveMind! {scheme}://{self.host.text}:{self.port.text}")
            self.status.set_text("Connected to HiveMind!")
            self.clear_chat()
            self.speak("Connected to HiveMind!")
            self.bus.on_mycroft("speak", self.handle_speak)
        else:
            self.status.set_text("Connection timeout")
