"""Application entry-point"""

# Standard library
import os
import sys
import time
import json
import traceback
import threading

# Local libraries
from . import util, compat, control, settings, ipc
from .vendor.Qt import QtCore, QtGui, QtQuick

MODULE_DIR = os.path.dirname(__file__)
QML_IMPORT_DIR = os.path.join(MODULE_DIR, "qml")
APP_PATH = os.path.join(MODULE_DIR, "qml", "main.qml")
ICON_PATH = os.path.join(MODULE_DIR, "icon.ico")
IS_QT6 = getattr(QtCore, "qVersion", lambda: "0.0.0")().startswith("6.")
FORCE_ON_TOP_HOSTS = {"Blender"}


def _should_force_on_top(client_settings=None):
    env_value = os.environ.get("PYBLISH_QML_FORCE_ON_TOP", "").strip().lower()
    if env_value in {"1", "true", "yes", "on"}:
        return True

    label = None
    if client_settings:
        label = client_settings.get("ContextLabel")

    if not label:
        label = settings.ContextLabel

    return label in FORCE_ON_TOP_HOSTS


class Window(QtQuick.QQuickView):
    """Main application window"""

    def __init__(self, parent=None):
        super(Window, self).__init__(None)
        self.app = parent

        self.setTitle(settings.WindowTitle)

        # Qt6 enum members are not reliably accessible via instance attributes.
        resize_mode = getattr(QtQuick.QQuickView, "SizeRootObjectToView", None)
        if resize_mode is None and hasattr(QtQuick.QQuickView, "ResizeMode"):
            resize_mode = QtQuick.QQuickView.ResizeMode.SizeRootObjectToView
        self.setResizeMode(resize_mode)

        self.resize(*settings.WindowSize)
        self.setMinimumSize(QtCore.QSize(430, 300))

    def event(self, event):
        """Allow GUI to be closed upon holding Shift"""
        if event.type() == QtCore.QEvent.Close:
            modifiers = self.app.queryKeyboardModifiers()
            shift_pressed = QtCore.Qt.ShiftModifier & modifiers
            states = self.app.controller.states

            if shift_pressed:
                print("Force quitted..")
                self.app.controller.host.emit("pyblishQmlCloseForced")
                event.accept()

            elif any(state in states for state in ("ready", "finished")):
                self.app.controller.host.emit("pyblishQmlClose")
                event.accept()

            else:
                print("Not ready, hold SHIFT to force an exit")
                event.ignore()

        return super(Window, self).event(event)


class Application(QtGui.QGuiApplication):
    """Pyblish QML wrapper around QGuiApplication

    Provides production and debug launchers along with controller
    initialisation and orchestration.

    """

    shown = QtCore.Signal("QVariant")
    hidden = QtCore.Signal()
    quitted = QtCore.Signal()
    published = QtCore.Signal()
    validated = QtCore.Signal()

    targeted = QtCore.Signal("QVariant")

    risen = QtCore.Signal()
    inFocused = QtCore.Signal()
    outFocused = QtCore.Signal()

    def __init__(self, source, targets=None):
        super(Application, self).__init__(sys.argv)

        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        window = Window(self)
        window.statusChanged.connect(self.on_status_changed)

        engine = window.engine()
        engine.addImportPath(QML_IMPORT_DIR)

        host = ipc.client.Proxy()
        controller = control.Controller(host, targets=targets, parent=window)
        controller.finished.connect(lambda: window.alert(0))

        context = engine.rootContext()
        context.setContextProperty("app", controller)

        self.window = window
        self.engine = engine
        self.controller = controller
        self.host = host
        self.clients = dict()
        self.current_client = None

        self.shown.connect(self.show)
        self.hidden.connect(self.hide)
        self.quitted.connect(self.quit)
        self.published.connect(self.publish)
        self.validated.connect(self.validate)

        self.targeted.connect(self.target)

        self.risen.connect(self.rise)
        self.inFocused.connect(self.inFocus)
        self.outFocused.connect(self.outFocus)

        window.setSource(QtCore.QUrl.fromLocalFile(source))

    def on_status_changed(self, status):
        if status == QtQuick.QQuickView.Error:
            try:
                for error in self.window.errors():
                    print("QML Error: {0}".format(error.toString()))
            except Exception:
                traceback.print_exc()
            self.quit()

    def register_client(self, port):
        self.current_client = port
        self.clients[port] = {
            "lastSeen": time.time()
        }

    def deregister_client(self, port):
        self.clients.pop(port)

    @util.SlotSentinel()
    def show(self, client_settings=None):
        """Display GUI

        Once the QML interface has been loaded, use this
        to display it.

        Arguments:
            port (int): Client asking to show GUI.
            client_settings (dict, optional): Visual settings, see settings.py

        """
        window = self.window

        if client_settings:
            # Apply client-side settings
            settings.from_dict(client_settings)
            window.setWidth(client_settings["WindowSize"][0])
            window.setHeight(client_settings["WindowSize"][1])
            window.setTitle(client_settings["WindowTitle"])
            window.setFramePosition(
                QtCore.QPoint(
                    client_settings["WindowPosition"][0],
                    client_settings["WindowPosition"][1]
                )
            )

        message = list()
        message.append("Settings: ")
        for key, value in settings.to_dict().items():
            message.append("  %s = %s" % (key, value))

        print("\n".join(message))

        window.requestActivate()
        window.showNormal()

        force_on_top = _should_force_on_top(client_settings)

        # Work-around for window appearing behind other windows.
        # Blender runs without a Qt parent window, so keep the publisher on top
        # instead of trying to attach it like a child dialog.
        if force_on_top:
            window.setFlag(QtCore.Qt.WindowStaysOnTopHint, True)
            window.showNormal()
            if hasattr(window, "raise_"):
                window.raise_()
            window.requestActivate()
        elif IS_QT6:
            if hasattr(window, "raise_"):
                window.raise_()
            window.requestActivate()
        else:
            previous_flags = window.flags()
            window.setFlags(previous_flags | QtCore.Qt.WindowStaysOnTopHint)
            window.setFlags(previous_flags)
            window.showNormal()
            window.requestActivate()

        # Give statemachine enough time to boot up
        if not any(state in self.controller.states
                   for state in ["ready", "finished"]):
            util.timer("ready")

            if not self.controller.is_ready():
                print("Warning: Could not enter ready state")

            util.timer_end("ready", "Awaited statemachine for %.2f ms")

        if client_settings:
            auto_validate = client_settings.get('autoValidate', False)
            auto_publish = client_settings.get('autoPublish', False)
            self.controller.data['autoValidate'] = auto_validate
            self.controller.data['autoPublish'] = auto_publish

        self.controller.show.emit()

        # Allow time for QML to initialise
        util.schedule(self.controller.reset, 500, channel="main")

    def hide(self):
        """Hide GUI

        Process remains active and may be shown
        via a call to `show()`

        """
        self.window.hide()

    def rise(self):
        """Rise GUI from hidden"""
        self.window.show()

    def inFocus(self):
        """Set GUI on-top flag"""
        if IS_QT6:
            self.window.setFlag(QtCore.Qt.WindowStaysOnTopHint, True)
            self.window.showNormal()
            self.window.requestActivate()
        else:
            previous_flags = self.window.flags()
            self.window.setFlags(previous_flags |
                                 QtCore.Qt.WindowStaysOnTopHint)
            self.window.setFlags(previous_flags)

    def outFocus(self):
        """Remove GUI on-top flag"""
        if IS_QT6:
            self.window.setFlag(QtCore.Qt.WindowStaysOnTopHint, False)
            self.window.showNormal()
        else:
            previous_flags = self.window.flags()
            self.window.setFlags(previous_flags ^
                                 QtCore.Qt.WindowStaysOnTopHint)
            self.window.setFlags(previous_flags)

    def publish(self):
        """Fire up the publish sequence"""
        self.controller.publish()

    def validate(self):
        """Fire up the validation sequance"""
        self.controller.validate()

    def target(self, targets):
        self.controller.targets = targets

    def listen(self):
        """Listen on incoming messages from host

        TODO(marcus): We can't use this, as we are already listening on stdin
            through client.py. Do use this, we will have to find a way to
            receive multiple signals from the same stdin, and channel them
            to their corresponding source.

        """

        def _listen():
            while True:
                line = self.host.channels["parent"].get()
                payload = json.loads(line)["payload"]

                # We can't call methods directly, as we are running
                # in a thread. Instead, we emit signals that do the
                # job for us.
                signal = {

                    "show": "shown",
                    "hide": "hidden",
                    "quit": "quitted",
                    "publish": "published",
                    "validate": "validated",

                    "target": "targeted",

                    "rise": "risen",
                    "inFocus": "inFocused",
                    "outFocus": "outFocused",

                }.get(payload["name"])

                if not signal:
                    print("'{name}' was unavailable.".format(
                        **payload))
                else:
                    try:
                        getattr(self, signal).emit(
                            *payload.get("args", []))
                    except Exception:
                        traceback.print_exc()

        thread = threading.Thread(target=_listen)
        thread.daemon = True
        thread.start()


def main(demo=False, aschild=False, targets=None):
    """Start the Qt-runtime and show the window

    Arguments:
        aschild (bool, optional): Run as child of parent process

    """

    if aschild:
        print("Starting pyblish-qml")
        compat.main()
        app = Application(APP_PATH, targets)
        app.listen()

        print("Done, don't forget to call `show()`")
        return app.exec_()

    else:
        print("Starting pyblish-qml server..")
        service = ipc.service.MockService() if demo else ipc.service.Service()
        server = ipc.server.Server(service, targets=targets)

        proxy = ipc.server.Proxy(server)
        proxy.show(settings.to_dict())

        server.listen()
        exit_code = server.wait()
        print("pyblish-qml child exited with code: {0}".format(exit_code))
        return exit_code


