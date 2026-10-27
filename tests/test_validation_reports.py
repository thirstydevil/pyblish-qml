"""Host-independent coverage for the deployed validation report protocol."""
import copy
import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
import pyblish.api
import pyblish.plugin
from pyblish_qml import hooks, reporting, report_export
from pyblish_qml.ipc import formatting, service


def report():
    return {'schema_version': 1, 'checks': [
        {'rule': 'Mesh.uvs', 'status': 'failed', 'detail': 'Details', 'findings': [
            {'title': 'Missing UVs', 'description': '<unsafe> & missing',
             'affected': ['mesh1'], 'comparisons': [{'actual': 'none', 'expected': 'map1'}],
             'remedy': 'Create UVs.'}]}]}


def test_render_escapes_notes_and_keeps_remedy():
    heading, html, details = reporting.render_report(report())
    assert heading == 'Publishing blocked'
    assert '&lt;unsafe&gt; &amp; missing' in html
    assert 'Create UVs.' in html and 'map1' in html
    assert 'Mesh.uvs: failed' in details


def test_report_transport_with_schema_validation():
    class Validate(pyblish.api.ContextPlugin):
        def process(self, context):
            raise RuntimeError('ordinary exception')
    result = pyblish.plugin.process(Validate, pyblish.api.Context())
    result['report'] = report()
    result['error_info'] = {'is_validation_error': True}
    with patch.dict('os.environ', {'PYBLISH_SAFE': '1'}):
        payload = formatting.format_result(result)
    assert payload['report'] == result['report']
    assert payload['error_info'] == result['error_info']
    assert 'ordinary exception' in str(payload['error'])
    json.dumps(payload)


def test_records_render_format_arguments_before_transport():
    record = logging.LogRecord('test', logging.ERROR, __file__, 1, 'Missing %s', ('UVs',), None)
    assert formatting.format_record(record)['message'] == 'Missing UVs'


def test_scene_provenance_transport():
    context = pyblish.api.Context()
    context.data[hooks.SCENE_KEY] = {'generation': 'one', 'path': 'scene.ma'}
    assert formatting.format_context(context)['data'][hooks.SCENE_KEY] == context.data[hooks.SCENE_KEY]


def test_atomic_report_export_and_input_preservation(tmp_path):
    value = {'schema_version': 1, 'results': [{'report': report()}]}
    before = copy.deepcopy(value)
    destination = tmp_path / 'report.json'
    report_export.write_report(destination, value)
    assert json.loads(destination.read_text())['results'] == value['results']
    assert value == before
    original = destination.read_bytes()
    with patch.object(report_export.os, 'replace', side_effect=PermissionError('locked')):
        with pytest.raises(PermissionError):
            report_export.write_report(destination, value)
    assert destination.read_bytes() == original
    assert list(tmp_path.iterdir()) == [destination]


def test_cancel_does_not_write():
    with patch.object(report_export, 'choose_report_path', return_value=None), patch.object(report_export, 'write_report') as write:
        assert report_export.save_report({'schema_version': 1, 'results': []}) == {'cancelled': True}
        write.assert_not_called()


def test_invalid_selection_does_not_partially_update_host():
    api = service.Service.__new__(service.Service)
    api._context = pyblish.api.Context()
    instance = api._context.create_instance('mesh')
    instance.data['publish'] = True
    with patch.object(api, '_assert_current_scene'):
        with pytest.raises(ValueError):
            api.set_instance_selection({instance.id: False, 'unknown': False})
        assert instance.data['publish'] is True
        api.set_instance_selection({instance.id: False})
        assert instance.data['publish'] is False
