import sys
import unittest

from pyblish_qml import control
from pyblish_qml.vendor.Qt import QtCore


def _ensure_app():
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtCore.QCoreApplication(sys.argv)
    return app


class FakeHost(object):
    def __init__(self):
        self.events = []

    def emit(self, signal, **kwargs):
        self.events.append((signal, kwargs))


class TestInstanceSelection(unittest.TestCase):
    def setUp(self):
        _ensure_app()
        self.host = FakeHost()
        self.controller = control.Controller(self.host)
        self.controller.data["state"]["all"] = ["ready"]

        model = self.controller.data["models"]["item"]
        model.add_context({
            "id": "Context",
            "name": "Context",
            "data": {},
        })
        model.add_instance(self._instance("one"))
        model.add_instance(self._instance("two"))

    def tearDown(self):
        self.controller.machine.stop()

    @staticmethod
    def _instance(name):
        return {
            "id": name,
            "name": name,
            "data": {
                "family": "test",
                "families": [],
                "publish": True,
            },
        }

    def _proxy_index(self, item_id):
        proxy = self.controller.instanceProxy
        for index in range(proxy.rowCount()):
            if proxy.item(index).id == item_id:
                return index
        self.fail("Could not find proxy item: {0}".format(item_id))

    def test_all_and_none_ignore_context(self):
        self.assertEqual(self.controller.enabledInstanceCount, 2)
        self.assertEqual(self.controller.optionalInstanceCount, 2)

        self.controller.setAllInstancesToggled(False)

        model = self.controller.data["models"]["item"]
        self.assertTrue(model.instances[0].isToggled)
        self.assertFalse(model.instances[1].isToggled)
        self.assertFalse(model.instances[2].isToggled)
        self.assertEqual(self.controller.enabledInstanceCount, 0)

        self.controller.setAllInstancesToggled(True)
        self.assertTrue(model.instances[1].isToggled)
        self.assertTrue(model.instances[2].isToggled)
        self.assertEqual(self.controller.enabledInstanceCount, 2)

    def test_solo_enables_only_selected_instance(self):
        self.controller.soloInstance(self._proxy_index("two"))

        model = self.controller.data["models"]["item"]
        self.assertFalse(model.instances[1].isToggled)
        self.assertTrue(model.instances[2].isToggled)
        self.assertEqual(self.controller.enabledInstanceCount, 1)

    def test_context_toggle_is_ignored(self):
        errors = []
        self.controller.error.connect(errors.append)

        self.controller.toggleInstance(self._proxy_index("Context"))

        self.assertEqual(errors, [])
        self.assertEqual(self.controller.enabledInstanceCount, 2)

    def test_bulk_change_notifies_qml_once(self):
        notifications = []
        self.controller.instanceSelectionChanged.connect(
            lambda: notifications.append(True)
        )

        self.controller.setAllInstancesToggled(False)

        self.assertEqual(notifications, [True])

    def test_section_change_updates_selection_count(self):
        notifications = []
        self.controller.instanceSelectionChanged.connect(
            lambda: notifications.append(True)
        )

        self.controller.toggleSection(False, "test")

        self.assertEqual(self.controller.enabledInstanceCount, 0)
        self.assertEqual(notifications, [True])


if __name__ == "__main__":
    unittest.main()
