import unittest
from unittest import mock

from pyblish_qml import app, host, ipc


class FakeServer(object):
    def listen(self):
        return None

    def wait(self):
        return 0


class FakeProxy(object):
    def __init__(self, _server):
        self.settings = None

    def show(self, settings):
        self.settings = settings


class TestDemoMain(unittest.TestCase):
    def test_demo_installs_host_toggle_callbacks_for_service_lifetime(self):
        server = FakeServer()

        with mock.patch.object(host, "install_callbacks") as install:
            with mock.patch.object(host, "uninstall_callbacks") as uninstall:
                with mock.patch.object(
                    ipc.server, "Server", return_value=server
                ):
                    with mock.patch.object(ipc.server, "Proxy", FakeProxy):
                        result = app.main(demo=True, targets=["default"])

        self.assertEqual(result, 0)
        install.assert_called_once_with()
        uninstall.assert_called_once_with()

    def test_demo_removes_callbacks_when_server_setup_fails(self):
        with mock.patch.object(host, "install_callbacks") as install:
            with mock.patch.object(host, "uninstall_callbacks") as uninstall:
                with mock.patch.object(
                    ipc.server,
                    "Server",
                    side_effect=RuntimeError("server failed"),
                ):
                    with self.assertRaises(RuntimeError):
                        app.main(demo=True, targets=["default"])

        install.assert_called_once_with()
        uninstall.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
