import sys

from pyblish_qml import ipc
from pyblish_qml.vendor.Qt import QtCore

self = sys.modules[__name__]

self.app = (
    QtCore.QCoreApplication.instance() or
    QtCore.QCoreApplication(sys.argv)
)

self.service = ipc.service.Service()
