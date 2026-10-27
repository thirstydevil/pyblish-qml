import QtQuick 2.3
Loader {
    width: parent.width
    source: object.reportHtml ? "ValidationReportDelegate.qml" : "LegacyErrorDelegate.qml"
}
