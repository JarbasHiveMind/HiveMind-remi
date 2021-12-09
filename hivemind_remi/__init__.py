from os.path import join, dirname

import remi
import remi.gui as gui
from mycroft_bus_client import Message

from hivemind_bus_client import HiveMessageBusClient


class HiveMindRemi(remi.App):
    platform = "HiveMindRemiV0.1"
    bus = None
    self_signed = False

    def __init__(self, *args, **kwargs):
        super().__init__(static_file_path={'pics': join(dirname(__file__), "res")},
                         *args, **kwargs)

    # hivemind
    def connect(self, access_key, host="ws://127.0.0.1", port=5678, crypto_key=None, self_signed=None):
        if self_signed is not None:
            self.self_signed = self_signed
        if self.bus:
            self.bus.port = port
            self.bus.host = host
            self.bus.crypto_key = crypto_key
            self.bus.key = access_key
            self.bus.ssl = host.startswith("wss:")
        else:
            # connect to hivemind
            self.bus = HiveMessageBusClient(key=access_key,
                                            port=port,
                                            host=host,
                                            crypto_key=crypto_key,
                                            ssl=host.startswith("wss:"),
                                            useragent=self.platform,
                                            self_signed=self.self_signed)

            self.bus.run_in_thread()
            # block until hivemind connects
            print("Waiting for Hivemind connection")
            self.bus.connected_event.wait(timeout=10)

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

        if not self.bus or not self.bus.connected_event.is_set():
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

        form.append([hostbox, portbox, accessbox, cryptobox, langbox, statusbox, certbox])
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
        self.connect(access_key=self.key.text,
                     crypto_key=self.crypto.text,
                     port=self.port.text,
                     host=self.host.text)

        if self.bus and self.bus.connected_event.is_set():
            print(f"Connected to HiveMind! {'wss' if self.bus.ssl else 'ws'}://{self.bus.host}:{self.bus.port}")
            self.status.set_text("Connected to HiveMind!")
            self.clear_chat()
            self.speak("Connected to HiveMind!")
            self.bus.on_mycroft("speak", self.handle_speak)
        else:
            self.status.set_text("Connection timeout")
