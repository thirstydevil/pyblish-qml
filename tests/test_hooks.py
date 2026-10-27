"""The extension points a pipeline fills in (pyblish_qml/hooks.py); nothing here knows a pipeline."""
import errno
import sys
import types
import unittest

import pyblish.api

from pyblish_qml import hooks
from pyblish_qml.ipc import formatting, service

try:
    from unittest import mock
except ImportError:  # Python 2
    import mock


class Guard(object):
    def __init__(self, stale=False):
        self.stale = stale
        self.bound = []
        self.checked = []

    def bind(self, context):
        self.bound.append(context)
        context.data[hooks.SCENE_KEY] = {"generation": "one"}

    def assert_current(self, context):
        self.checked.append(context)
        if self.stale:
            raise RuntimeError("Scene changed")


class Settings(object):
    def __init__(self):
        self.saved = []

    def sections(self, instance):
        return [{"title": instance.name}]

    def save(self, instance, entries, others):
        self.saved.append((instance, entries, others))
        return len(entries)


class HooksTestCase(unittest.TestCase):
    def tearDown(self):
        hooks.unregister(hooks.SCENE_GUARD)
        hooks.unregister(hooks.PUBLISH_SETTINGS)


class TestRegistry(HooksTestCase):
    def test_nothing_is_registered_by_default(self):
        self.assertIsNone(hooks.get(hooks.SCENE_GUARD))
        self.assertIsNone(hooks.get(hooks.PUBLISH_SETTINGS))

    def test_register_replaces_and_unregister_removes(self):
        first, second = Guard(), Guard()
        hooks.register(hooks.SCENE_GUARD, first)
        hooks.register(hooks.SCENE_GUARD, second)
        self.assertIs(hooks.get(hooks.SCENE_GUARD), second)
        hooks.unregister(hooks.SCENE_GUARD)
        self.assertIsNone(hooks.get(hooks.SCENE_GUARD))
        hooks.unregister(hooks.SCENE_GUARD)  # removing what is not there is fine

    def test_an_unknown_extension_point_is_refused(self):
        with self.assertRaises(ValueError):
            hooks.register("scene_gaurd", Guard())


class TestSceneGuard(HooksTestCase):
    def test_without_a_guard_the_service_works_as_before(self):
        svc = service.Service()
        svc._assert_current_scene()
        self.assertNotIn(hooks.SCENE_KEY, svc._context.data)

    def test_reset_binds_the_guard_to_the_new_context(self):
        guard = Guard()
        hooks.register(hooks.SCENE_GUARD, guard)
        svc = service.Service()
        self.assertEqual(guard.bound, [svc._context])
        svc.reset()
        self.assertEqual(len(guard.bound), 2)
        self.assertIs(guard.bound[-1], svc._context)

    def test_the_snapshot_reaches_the_window(self):
        hooks.register(hooks.SCENE_GUARD, Guard())
        svc = service.Service()
        data = formatting.format_context(svc._context)["data"]
        self.assertEqual(data[hooks.SCENE_KEY], {"generation": "one"})

    def test_a_stale_scene_refuses_actions(self):
        guard = Guard(stale=True)
        hooks.register(hooks.SCENE_GUARD, guard)
        svc = service.Service()
        with self.assertRaisesRegex(RuntimeError, "Scene changed"):
            svc.set_instance_selection({})
        with self.assertRaisesRegex(RuntimeError, "Scene changed"):
            svc.repair({"id": "none"})
        self.assertEqual(len(guard.checked), 2)


class TestPublishSettings(HooksTestCase):
    def setUp(self):
        self.svc = service.Service()
        self.one = self.svc._context.create_instance("One")
        self.two = self.svc._context.create_instance("Two")
        self.three = self.svc._context.create_instance("Three")
        for instance in (self.one, self.two):
            instance.data["hasPublishSettings"] = True

    def test_without_a_provider_the_answer_is_an_error_not_a_crash(self):
        result = self.svc.publish_settings(self.one.id)
        self.assertEqual(result, {"ok": False, "error": "No publish settings provider is registered"})

    def test_sections_come_from_the_provider(self):
        hooks.register(hooks.PUBLISH_SETTINGS, Settings())
        result = self.svc.publish_settings(self.one.id)
        self.assertEqual(result, {"ok": True, "name": "One", "sections": [{"title": "One"}]})

    def test_save_passes_the_instance_and_the_other_enabled_instances_that_have_settings(self):
        provider = Settings()
        hooks.register(hooks.PUBLISH_SETTINGS, provider)
        ids = [self.one.id, self.two.id, self.three.id]
        result = self.svc.publish_settings(self.one.id, entries={"a": 1, "b": 2}, enabled_ids=ids)
        self.assertEqual(result, {"ok": True, "count": 2})
        instance, entries, others = provider.saved[0]
        self.assertIs(instance, self.one)
        self.assertEqual(entries, {"a": 1, "b": 2})
        self.assertEqual(others, [self.two])  # not itself, and not Three, which has no settings

    def test_a_stale_scene_blocks_saving(self):
        provider = Settings()
        hooks.register(hooks.PUBLISH_SETTINGS, provider)
        hooks.register(hooks.SCENE_GUARD, Guard(stale=True))
        svc = service.Service()
        instance = svc._context.create_instance("One")
        result = svc.publish_settings(instance.id, entries={"a": 1})
        self.assertEqual(result, {"ok": False, "error": "Scene changed"})
        self.assertEqual(provider.saved, [])


class TestNotifySceneChanged(unittest.TestCase):
    def _server(self, alive=True, closed=False):
        stream = mock.Mock(closed=closed)
        process = mock.Mock(stdin=stream)
        process.poll.return_value = None if alive else 1
        return mock.Mock(popen=process)

    def _host(self, server):
        return types.SimpleNamespace(current_server=lambda: server)

    def test_nothing_happens_without_a_window(self):
        with mock.patch.dict(sys.modules, {"pyblish_qml.host": self._host(None)}):
            self.assertIsNone(hooks.notify_scene_changed("g"))
        sys.modules.pop("pyblish_qml.host", None)
        self.assertIsNone(hooks.notify_scene_changed("g"))

    def test_a_closed_window_is_not_written_to(self):
        for server in (self._server(alive=False), self._server(closed=True)):
            with mock.patch.dict(sys.modules, {"pyblish_qml.host": self._host(server)}):
                with mock.patch("pyblish_qml.ipc.server.Proxy") as proxy:
                    hooks.notify_scene_changed("g")
            proxy.assert_not_called()

    def test_an_open_window_is_told(self):
        server = self._server()
        with mock.patch.dict(sys.modules, {"pyblish_qml.host": self._host(server)}):
            with mock.patch("pyblish_qml.ipc.server.Proxy") as proxy:
                hooks.notify_scene_changed("g")
        proxy.assert_called_once_with(server)
        proxy.return_value.scene_changed.assert_called_once_with("g")

    def test_a_dead_pipe_is_ignored_but_other_errors_are_not(self):
        server = self._server()
        with mock.patch.dict(sys.modules, {"pyblish_qml.host": self._host(server)}):
            with mock.patch("pyblish_qml.ipc.server.Proxy") as proxy:
                proxy.return_value.scene_changed.side_effect = OSError(errno.EPIPE, "broken pipe")
                hooks.notify_scene_changed("g")
                proxy.return_value.scene_changed.side_effect = OSError(errno.EACCES, "denied")
                with self.assertRaises(OSError):
                    hooks.notify_scene_changed("g")


if __name__ == "__main__":
    unittest.main()
