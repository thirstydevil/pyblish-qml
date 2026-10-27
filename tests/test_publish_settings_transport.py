import unittest
import pyblish.api
from pyblish_qml.ipc import formatting


class TestPublishSettingsTransport(unittest.TestCase):
    def test_settings_affordance_survives_host_to_ui_transport(self):
        context = pyblish.api.Context()
        instance = context.create_instance("Beard")
        instance.data.update(hasPublishSettings=True,
                             publishSettingsSummary="10/18 outputs",
                             tagPublishPlan={"private": object()})
        data = formatting.format_context(context)["children"][0]["data"]
        self.assertIs(data["hasPublishSettings"], True)
        self.assertEqual(data["publishSettingsSummary"], "10/18 outputs")
        self.assertNotIn("tagPublishPlan", data)

    def test_legacy_instances_still_serialize(self):
        context = pyblish.api.Context()
        instance = context.create_instance("Legacy")
        data = formatting.format_instance(instance)["data"]
        self.assertNotIn("hasPublishSettings", data)
