"""Extension points for the pipeline that runs Pyblish QML.

Pyblish QML knows nothing about the pipeline around it. A pipeline fills in the points below from its own
code, inside the host process (the process that runs ``ipc.service.Service``), and the service uses what is
registered and does nothing for what is not.

``scene_guard``
    Ties a publish session to one scene, so results from an earlier scene cannot be acted on.

    ``bind(context)``
        Called when the service resets. Store a dict with a ``generation`` entry in
        ``context.data[SCENE_KEY]``; it travels to the window and into saved reports.
    ``assert_current(context)``
        Called before anything that changes or acts on the scene. Raise to refuse.

    When the scene changes, call ``notify_scene_changed(generation)`` so an open window marks its
    results stale.

``publish_settings``
    Per-instance settings shown by the window for instances with ``hasPublishSettings`` set.

    ``sections(instance)``
        A JSON-serialisable description of the instance's settings.
    ``save(instance, entries, others)``
        Store ``entries`` for ``instance`` and return a count. ``others`` are the other enabled
        instances that have settings, for providers whose settings depend on them.

Register from the host process, once, before the window is shown::

    from pyblish_qml import hooks
    hooks.register(hooks.SCENE_GUARD, MyGuard())
"""

import errno
import sys

SCENE_GUARD = "scene_guard"
PUBLISH_SETTINGS = "publish_settings"

#: The key in ``context.data`` that carries the scene guard's snapshot to the window.
SCENE_KEY = "_validation_scene"

_KNOWN = (SCENE_GUARD, PUBLISH_SETTINGS)
_providers = {}


def register(name, provider):
    """Set the provider for an extension point, replacing any earlier one."""
    if name not in _KNOWN:
        raise ValueError("Unknown extension point %r; expected one of %s" % (name, ", ".join(_KNOWN)))
    _providers[name] = provider


def unregister(name):
    """Remove the provider for an extension point, if there is one."""
    _providers.pop(name, None)


def get(name):
    """The provider registered for an extension point, or None."""
    return _providers.get(name)


def notify_scene_changed(generation):
    """Tell an open window the scene changed. Does nothing when no window is open."""
    host = sys.modules.get("pyblish_qml.host")
    server = host.current_server() if host else None
    if server is None:
        return
    process = server.popen
    stream = process.stdin
    if process.poll() is not None or stream is None or stream.closed:
        return

    from .ipc.server import Proxy

    try:
        Proxy(server).scene_changed(generation)
    except (OSError, ValueError) as error:
        # The window can close between the liveness check and the write. Windows may report a dead
        # pipe as EINVAL rather than EPIPE.
        if (
            process.poll() is not None
            or stream.closed
            or isinstance(error, OSError)
            and error.errno in (errno.EPIPE, errno.EBADF, errno.EINVAL)
        ):
            return
        raise
