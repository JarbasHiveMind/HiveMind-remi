"""The app connects with its own identity (HIVEMIND-CRYPTO-1 §2)."""
from unittest.mock import MagicMock, patch

import hivemind_remi
from hivemind_remi import HiveMindRemi


def test_connect_builds_the_client_with_the_apps_own_identity():
    app = HiveMindRemi.__new__(HiveMindRemi)
    app.bus = None
    app.self_signed = False
    identity = MagicMock()
    with patch.object(hivemind_remi, "NodeIdentity", return_value=identity) as ctor, \
         patch.object(hivemind_remi, "HiveMessageBusClient") as client:
        app.connect(access_key="key", password="pw", host="ws://127.0.0.1")
    ctor.assert_called_once_with(app_name="remi")
    assert client.call_args.kwargs["identity"] is identity
