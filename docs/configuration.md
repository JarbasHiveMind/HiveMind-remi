# Configuration

HiveMind-remi has no config file. Everything is entered on the **Connect** tab
of the web GUI and used to build a `HiveMessageBusClient` at connect time.

## Connect-tab fields

| Field | Maps to | Notes |
|-------|---------|-------|
| **Host** | `host` | Server address with scheme, e.g. `ws://127.0.0.1`. Use `wss://` for TLS. The bus client derives the `ssl` flag from the scheme. There is no separate SSL toggle. |
| **Port** | `port` | The server's HiveMind port. Defaults to `5678` when left blank. |
| **Access Key** | `key` | The access key printed by `hivemind-core add-client`. |
| **Password** | `password` | The client password from `hivemind-core add-client`. Optional if a crypto key is used instead. |
| **Crypto Key** | `crypto_key` | The crypto/password key for that client. Blank is sent as `None`. |
| **Language** | the `lang` of each emitted utterance | Defaults to `en-us`. |
| **Accept self signed** | `self_signed` | Tick to connect to a server using a self-signed TLS certificate (testing only). |

## How a connection is built

On **Connect**, the app:

1. tears down any previous client. The 0.9.x client is `NodeIdentity`-backed
   and derives `ssl` from the host scheme, so connection params cannot be
   mutated in place. Every (re)connect builds a fresh client.
2. constructs `HiveMessageBusClient(key, password, crypto_key, host, port,
   useragent, self_signed)`.
3. calls `bus.connect()`, which runs the client in a background thread and
   blocks until the HiveMind handshake completes (or raises on timeout).
4. on success, subscribes to `speak` messages (`bus.on_mycroft("speak", …)`) so
   replies render into the chat view.

The status label reflects each phase: *Disconnected*, *Connecting*, *Connected
to HiveMind!* (or *Connection failed: …* / *Connection timeout*).

## Obtaining credentials

Credentials come from the server side. On the machine running
[hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core):

```bash
hivemind-core add-client      # prints an access key + crypto/password key
hivemind-core listen --port 5678
```

Copy the printed access key and crypto/password key into the matching fields.

---
[← Installation](installation.md) · [Home](index.md) · [Architecture →](architecture.md)
