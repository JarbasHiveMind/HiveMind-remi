"""Smoke tests for hivemind-remi.

These exercise package import, the computed version, and construction of the
REMI app without starting the web server or connecting to a HiveMind hub.
"""
import unittest
from unittest.mock import MagicMock, patch


class TestPackage(unittest.TestCase):
    def test_import_and_version(self):
        import hivemind_remi
        from hivemind_remi.version import __version__

        # the package imports cleanly and exposes the app class
        self.assertTrue(hasattr(hivemind_remi, "HiveMindRemi"))
        self.assertIsInstance(__version__, str)
        # e.g. "0.1.0" or "0.1.0a1"
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+(a\d+)?$")

    def test_app_class_importable(self):
        from hivemind_remi import HiveMindRemi

        self.assertTrue(issubclass(HiveMindRemi, object))
        self.assertTrue(HiveMindRemi.platform.startswith("HiveMindRemiV"))


class TestApp(unittest.TestCase):
    def _make_app(self):
        """Instantiate HiveMindRemi without running remi.App.__init__.

        remi.App.__init__ wires up an HTTP request handler; we only want the
        HiveMind client logic, so we bypass the base initialiser entirely.
        """
        from hivemind_remi import HiveMindRemi

        app = HiveMindRemi.__new__(HiveMindRemi)
        app.bus = None
        app.self_signed = False
        return app

    def test_not_connected_by_default(self):
        app = self._make_app()
        self.assertFalse(app.connected)

    def test_connect_builds_client_without_network(self):
        app = self._make_app()

        fake_bus = MagicMock()
        with patch("hivemind_remi.HiveMessageBusClient",
                   return_value=fake_bus) as mock_client:
            app.connect(access_key="key", password="pw",
                        host="ws://127.0.0.1", port="5678")

        # client constructed with the modern 0.9.x signature (no `ssl=` kwarg)
        self.assertEqual(mock_client.call_count, 1)
        _, kwargs = mock_client.call_args
        self.assertEqual(kwargs["key"], "key")
        self.assertEqual(kwargs["password"], "pw")
        self.assertEqual(kwargs["host"], "ws://127.0.0.1")
        self.assertEqual(kwargs["port"], 5678)
        self.assertNotIn("ssl", kwargs)
        # connect() should be driven, not the legacy run_in_thread + manual wait
        fake_bus.connect.assert_called_once()

    def test_say_when_disconnected_does_not_emit(self):
        app = self._make_app()
        app.speak = MagicMock()
        app.clear_chat = MagicMock()
        app.chat = MagicMock()
        app.lang = MagicMock(text="en-us")

        app.say("hello")

        app.speak.assert_called_once_with("I am not connected to the HiveMind!")


if __name__ == "__main__":
    unittest.main()
