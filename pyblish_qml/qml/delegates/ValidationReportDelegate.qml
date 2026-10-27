import QtQuick 2.3
import Pyblish 0.1

Item {
    id: root
    height: content.height + 12
    property bool showDetails: false
    Column {
        id: content
        width: parent.width - 20
        x: 10
        spacing: 6
        TextEdit {
            width: parent.width
            height: contentHeight
            readOnly: true
            selectByMouse: true
            wrapMode: TextEdit.Wrap
            textFormat: TextEdit.RichText
            color: Theme.dark.textColor
            font.family: mainFont.name
            font.pixelSize: 12
            text: object.reportHtml || ""
        }
        Label {
            width: parent.width
            visible: text.length > 0
            text: app.reportActionMessage
            wrapMode: Text.WordWrap
        }
        Flow {
            width: parent.width
            spacing: 8
            Repeater {
                model: JSON.parse(object.reportActions || "[]")
                FocusScope {
                    width: actionButton.width
                    height: actionButton.height
                    activeFocusOnTab: true
                    enabled: app.reportActionsEnabled
                    opacity: enabled ? 1.0 : 0.4
                    Keys.onReturnPressed: app.runReportAction(object.reportId, modelData.id)
                    Keys.onSpacePressed: app.runReportAction(object.reportId, modelData.id)
                    Button {
                        id: actionButton
                        text: modelData.label
                        onClicked: app.runReportAction(object.reportId, modelData.id)
                    }
                }
            }
            FocusScope {
                width: copyButton.width
                height: copyButton.height
                activeFocusOnTab: true
                Keys.onReturnPressed: app.copyValidationReport()
                Keys.onSpacePressed: app.copyValidationReport()
                Button {
                    id: copyButton
                    text: "Copy run report"
                    onClicked: app.copyValidationReport()
                }
            }
            FocusScope {
                width: saveButton.width
                height: saveButton.height
                activeFocusOnTab: true
                enabled: app.reportSaveEnabled
                Keys.onReturnPressed: app.saveValidationReport()
                Keys.onSpacePressed: app.saveValidationReport()
                Button {
                    id: saveButton
                    text: "Save run report..."
                    onClicked: app.saveValidationReport()
                }
            }
        }
        Label {
            text: root.showDetails ? "Hide technical details and check results" : "Show technical details and check results"
            width: parent.width
            wrapMode: Text.WordWrap
            activeFocusOnTab: true
            Keys.onReturnPressed: root.showDetails = !root.showDetails
            Keys.onSpacePressed: root.showDetails = !root.showDetails
            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.showDetails = !root.showDetails }
        }
        TextEdit {
            visible: root.showDetails
            width: parent.width
            height: visible ? contentHeight : 0
            readOnly: true
            selectByMouse: true
            wrapMode: TextEdit.Wrap
            textFormat: TextEdit.PlainText
            color: Theme.dark.textColor
            font.family: mainFont.name
            font.pixelSize: 12
            text: object.reportDetails || ""
        }
    }
}
