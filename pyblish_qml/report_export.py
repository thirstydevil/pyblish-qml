"""Save an immutable support snapshot without importing a GUI at module load."""
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile


def write_report(path, report):
    """Atomically replace a user-selected JSON file, preserving it on failure."""
    path = Path(path)
    if path.suffix.lower() != '.json':
        raise ValueError('Choose a report filename ending in .json.')
    snapshot = copy.deepcopy(report)
    if snapshot.get('schema_version') != 1 or not isinstance(snapshot.get('results'), list):
        raise ValueError('Unsupported validation report.')
    snapshot['exported_at_utc'] = datetime.now(timezone.utc).isoformat()
    # Serialize before opening anything so invalid metadata cannot damage a file.
    payload = json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                         dir=str(path.parent), prefix='.validation-report-',
                                         suffix='.tmp', delete=False) as stream:
            temporary = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, str(path))
        temporary = None
    finally:
        if temporary is not None:
            os.unlink(temporary)
    return str(path)


def choose_report_path():
    import pyblish.api
    name = 'validation-report-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.json'
    if 'maya' in pyblish.api.registered_hosts():
        import maya.cmds as cmds
        paths = cmds.fileDialog2(caption='Save validation report', fileMode=0,
                                fileFilter='Validation reports (*.json)',
                                startingDirectory=str(Path.home() / name), dialogStyle=2)
        return paths[0] if paths else None
    from .vendor.Qt import QtWidgets
    path, _ = QtWidgets.QFileDialog.getSaveFileName(
        None, 'Save validation report', str(Path.home() / name), 'Validation reports (*.json)')
    return path or None


def save_report(report):
    """Runs in the host: its native dialog owns overwrite confirmation."""
    snapshot = copy.deepcopy(report)
    try:
        path = choose_report_path()
        if not path:
            return {'cancelled': True}
        return {'path': write_report(path, snapshot)}
    except Exception as error:
        return {'error': 'Could not save report: {}. Choose another location and try again.'.format(error)}
