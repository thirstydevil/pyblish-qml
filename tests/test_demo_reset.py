import sys
import types
import unittest

import pyblish.api

from pyblish_qml import control, util
from pyblish_qml.vendor.Qt import QtCore


def _ensure_app():
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtCore.QCoreApplication(sys.argv)
    return app


class DummyContext(list):
    def __init__(self):
        super(DummyContext, self).__init__()
        self.id = "Context"
        self.name = "Context"
        self.data = {}

    def to_json(self):
        return {
            "name": "Context",
            "id": self.id,
            "data": dict(self.data),
            "children": [],
        }


class DummyPlugin(object):
    def __init__(self):
        self.id = "dummy.collector"
        self.name = "DummyCollector"
        self.label = "Dummy Collector"
        self.optional = True
        self.category = "Collect"
        self.actions = []
        self.order = pyblish.api.Collector.order
        self.doc = ""
        self.type = "Collector"
        self.module = "__test__"
        self.match = pyblish.api.Intersection
        self.hasRepair = False
        self.families = []
        self.contextEnabled = True
        self.instanceEnabled = False
        self.__instanceEnabled__ = False
        self.path = ""
        self.pre11 = False
        self.active = True
        self.targets = ["default"]

    def to_json(self):
        return {
            "pre11": self.pre11,
            "name": self.name,
            "label": self.label,
            "optional": self.optional,
            "category": self.category,
            "actions": list(self.actions),
            "id": self.id,
            "order": self.order,
            "doc": self.doc,
            "type": self.type,
            "module": self.module,
            "match": self.match,
            "hasRepair": self.hasRepair,
            "families": list(self.families),
            "contextEnabled": self.contextEnabled,
            "instanceEnabled": self.instanceEnabled,
            "__instanceEnabled__": self.__instanceEnabled__,
            "path": self.path,
            "active": self.active,
        }


class FakeHost(object):
    def __init__(self):
        self._request_count = 0
        self.cached_context = DummyContext()
        self.cached_discover = [DummyPlugin()]
        self.events = []

    def stats(self):
        return {"totalRequestCount": self._request_count}

    def reset(self):
        self._request_count += 1
        return None

    def context(self):
        self._request_count += 1
        return self.cached_context

    def discover(self):
        self._request_count += 1
        return self.cached_discover

    def emit(self, signal, **kwargs):
        self.events.append((signal, kwargs))

    def update(self, key, value, name):
        return None


class FailingContextHost(FakeHost):
    def context(self):
        raise RuntimeError("context lookup failed")


class FakeItemModel(object):
    class _KeyedList(list):
        def __getitem__(self, index):
            if isinstance(index, int):
                return super(FakeItemModel._KeyedList, self).__getitem__(index)

            for item in self:
                if item.id == index:
                    return item

            raise KeyError(index)

    def __init__(self):
        self.plugins = self._KeyedList()
        self.instances = self._KeyedList()
        self.sections = []

    def reset(self):
        self.plugins = self._KeyedList()
        self.instances = self._KeyedList()
        self.sections = []

    def add_context(self, context):
        item = types.SimpleNamespace(
            id=context["id"],
            name=context["name"],
            data=context["data"],
            hasError=False,
            succeeded=False,
            processed=False,
            isProcessing=False,
            currentProgress=0,
            label=context["data"].get("label"),
            hasComment=False,
        )
        self.instances = self._KeyedList([item])
        return item

    def add_plugin(self, plugin):
        item = types.SimpleNamespace(**plugin)
        item.instanceEnabled = plugin.get("instanceEnabled", False)
        item.compatibleInstances = []
        self.plugins.append(item)
        return item

    def reorder(self, _context):
        return None

    def update_compatibility(self):
        return None


class FakeResultModel(object):
    def reset(self):
        return None

    def add_context(self, _context):
        return None


class TestDemoReset(unittest.TestCase):
    def setUp(self):
        self._orig_defer = util.defer
        util.defer = self._immediate_defer

    def tearDown(self):
        util.defer = self._orig_defer

    @staticmethod
    def _immediate_defer(target, args=None, kwargs=None, callback=None):
        args = args or []
        kwargs = kwargs or {}

        try:
            result = target(*args, **kwargs)
        except Exception as exc:
            result = exc

        if callback:
            callback(result)

        return None

    def test_reset_populates_models(self):
        _ensure_app()

        host = FakeHost()
        controller = control.Controller(host, targets=["default"])
        controller.data["models"]["item"] = FakeItemModel()
        controller.data["models"]["result"] = FakeResultModel()
        controller.data["state"]["all"] = ["ready"]

        # Keep this test deterministic: reset should proceed to completion.
        controller.run = (
            lambda _collectors, _context, callback=None, callback_args=None:
            callback(*(callback_args or []))
        )

        initialised = []
        controller.initialised.connect(lambda: initialised.append(True))

        controller.reset()

        self.assertTrue(initialised)
        self.assertGreater(len(controller.data["models"]["item"].plugins), 0)
        self.assertGreater(len(controller.data["models"]["item"].instances), 0)
        self.assertTrue(host.events)
        self.assertEqual(host.events[-1][0], "reset")

    def test_reset_reports_context_failure(self):
        _ensure_app()

        host = FailingContextHost()
        controller = control.Controller(host, targets=["default"])
        controller.data["models"]["item"] = FakeItemModel()
        controller.data["models"]["result"] = FakeResultModel()
        controller.data["state"]["all"] = ["ready"]

        errors = []
        controller.error.connect(errors.append)

        controller.reset()

        self.assertTrue(errors)
        self.assertIn("host.context(initial)", errors[-1])


if __name__ == "__main__":
    unittest.main()
