import QtQuick 2.3
import Pyblish 0.1


View {
    id: footer

    property alias message: __message
    
    // 0 = Default; 1 = Publishing; 2 = Finished
    property int mode: 0
    property bool paused: false
    property bool hasComment: false
    property bool instanceSelectionEnabled: false
    property string instanceSelectionSummary: ""

    signal publish
    signal validate
    signal pause
    signal stop
    signal reset
    signal save
    signal comment
    signal enableAllInstances
    signal disableAllInstances

    width: 200
    height: 40

    Message {
        id: __message
        anchors.verticalCenter: parent.verticalCenter
    }

    Label {
        anchors.right: row.left
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        color: Theme.dark.subTextColor
        elide: Text.ElideRight
        horizontalAlignment: Text.AlignRight
        text: footer.instanceSelectionSummary
        visible: mode == 0 && text.length > 0
        width: Math.min(150, implicitWidth)
    }

    Row {
        id: row

        anchors {
            right: parent.right
            top: parent.top
            bottom: parent.bottom
            margins: 5
        }

        spacing: 3

        AwesomeButton {
            elevation: 1
            size: 25
            iconSize: 14

            enabled: footer.instanceSelectionEnabled
            opacity: enabled ? 1.0 : 0.5
            tooltip: visible ? "Enable all exports" : ""

            name: "toggle-on"
            visible: mode == 0
            onClicked: footer.enableAllInstances()
        }

        AwesomeButton {
            elevation: 1
            size: 25
            iconSize: 14

            enabled: footer.instanceSelectionEnabled
            opacity: enabled ? 1.0 : 0.5
            tooltip: visible ? "Disable all exports" : ""

            name: "toggle-off"
            visible: mode == 0
            onClicked: footer.disableAllInstances()
        }

        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            color: Theme.dark.dividerColor
            height: 24
            visible: mode == 0
            width: 1
        }

        AwesomeButton {
            elevation: 1

            size: 25
            iconSize: 14

            tooltip: visible ? "Comment.." : ""

            name: hasComment ? "comment" : "comment-o"
            onClicked: footer.comment()
            visible: mode == 0 ? true : false
        }

        AwesomeButton {
            elevation: 1

            size: 25
            iconSize: 14

            tooltip: visible ? "Stop" : ""

            name: "stop"
            visible: mode === 1 ? true : false
            onClicked: footer.stop()
        }

        AwesomeButton {
            elevation: 1
            size: 25
            iconSize: 14

            tooltip: visible ? "Reset" : ""

            name: "refresh"
            visible: mode == 0 || mode == 2 ? true : false
            onClicked: footer.reset()
        }

        AwesomeButton {
            elevation: 1

            size: 25
            iconSize: 14

            tooltip: visible ? "Validate" : ""

            name: "flask"
            visible: mode === 0 ? true : false
            onClicked: footer.validate()
        }

        AwesomeButton {
            elevation: 1
            size: 25
            iconSize: 14

            name: "play"

            tooltip: visible ? "Publish" : ""

            onClicked: footer.publish()

            visible: mode == 0 ? true : false

        }
    }
}
