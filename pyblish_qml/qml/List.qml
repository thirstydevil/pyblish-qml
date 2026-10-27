import QtQuick 2.3
import Pyblish 0.1
import Pyblish.ListItems 0.1 as ListItem


ListView {
    id: list

    property bool selectionEnabled: false
    signal itemPicked(int index, bool extend, bool rangeSelect)
    signal itemToggled(int index)
    signal itemDoubleClicked(int index)
    signal itemRightClicked(int index)
    signal actionTriggered(var action, int index)

    width: 200
    height: 300

    clip: true

    boundsBehavior: Flickable.DragOverBounds
    pixelAligned: true

    Keys.onPressed: function(event) {
        if (!selectionEnabled) return
        if (event.key === Qt.Key_Space) {
            itemToggled(currentIndex)
            event.accepted = true
        } else if (event.key === Qt.Key_Up || event.key === Qt.Key_Down) {
            currentIndex = Math.max(0, Math.min(count - 1,
                currentIndex + (event.key === Qt.Key_Up ? -1 : 1)))
            positionViewAtIndex(currentIndex, ListView.Contain)
            itemPicked(currentIndex, Boolean(event.modifiers & Qt.ControlModifier),
                       Boolean(event.modifiers & Qt.ShiftModifier))
            event.accepted = true
        }
    }

    delegate: ListItem.StandardActions {
        objectName: "publishRow_" + object.name
        selectable: list.selectionEnabled && object.optional
        selected: list.selectionEnabled && object.isPicked
        onPicked: function(mouse) {
            list.currentIndex = index
            list.forceActiveFocus()
            list.itemPicked(index, Boolean(mouse.modifiers & Qt.ControlModifier),
                            Boolean(mouse.modifiers & Qt.ShiftModifier))
        }
        text: (object.label || object.name) + (object.publishSettingsSummary ? " · " + object.publishSettingsSummary : "")
        active: object.optional
        checked: object.isToggled
        hidden: object.isHidden

        width: parent ? parent.width : 0

        status: {
            if (object.isProcessing)
                return "processing"
            if (object.hasError)
                return "error"
            if (object.hasWarning)
                return "warning"
            if (object.succeeded)
                return "success"
            return "default"
        }

        onToggled: itemToggled(index)
        onRightClicked: itemRightClicked(index)

        actions: [
            Action {
                name: "options"
                iconName: "cog"
                tooltip: "Configure publish options for this tag"
                enabled: object.hasPublishSettings
                onTriggered: actionTriggered(this, index)
            },
            Action {
                name: "solo"
                iconName: "bullseye"
                iconSize: 12
                tooltip: "Check only this export for this run"
                enabled: object.itemType == "instance" && object.optional
                onTriggered: actionTriggered(this, index)
            },

            Action {
                name: "repair"
                iconName: "wrench"
                enabled: object.hasError && object.hasRepair ? true : false
                onTriggered: actionTriggered(this, index)
            },

            Action {
                name: "legacyWarning"
                iconName: "exclamation-triangle"
                iconSize: 12
                tooltip: "This plug-in uses deprecated functionality"
                enabled: object.pre11 ? true : false
            },

            Action {
                name: "actionIcon"
                iconName: "adn"
                iconSize: 12
                tooltip: "This plug-in has actions"
                enabled: object.actionsIconVisible ? true : false
                color: object.actionPending ? "white"
                     : object.actionHasError ? Theme.dark.errorColor
                     : Theme.dark.successColor
            },

            Action {
                name: "comment"
                iconName: object.hasComment ? "comment" : "comment-o"
                iconSize: 12
                enabled: object.itemType == "instance" ? true : false
                onTriggered: actionTriggered(this, index)
            },

            Action {
                name: "enter"
                iconName: "angle-right"
                onTriggered: actionTriggered(this, index)
            }
        ]

    }
}
