import QtQuick 2.3
import Pyblish 0.1
import Pyblish.ListItems 0.1

Item {
    id: browser
    objectName: "instanceBrowser"
    signal settingsEntered(int index)
    signal instanceEntered(int index)
    signal commentEntered(int index)

    Column {
        id: toolbar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 6
        spacing: 5

        Label { text: "Exports for this run"; font.bold: true }

        View {
            width: parent.width
            height: 30
            elevation: -1
            border.width: search.activeFocus ? 1 : 0
            border.color: Theme.primaryColor
            TextInput {
                id: search
                objectName: "instanceSearch"
                anchors.fill: parent
                anchors.margins: 6
                anchors.rightMargin: clearSearch.width + 8
                color: Theme.dark.textColor
                selectionColor: Theme.primaryColor
                selectedTextColor: Theme.backgroundColor
                font.family: "Open Sans"
                font.pixelSize: 12
                clip: true
                selectByMouse: true
                activeFocusOnTab: true
                onTextChanged: app.filterInstances(text)
                Keys.onEscapePressed: text = ""
                Keys.onDownPressed: { exports.forceActiveFocus(); exports.currentIndex = 1 }
                Label {
                    anchors.verticalCenter: parent.verticalCenter
                    width: parent.width
                    text: "Find exports by name... (* and ? supported)"
                    visible: !search.text.length
                    color: Theme.dark.subTextColor
                    elide: Text.ElideRight
                }
            }
            AwesomeButton {
                id: clearSearch
                name: "times"
                size: 24
                iconSize: 12
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                visible: search.text.length > 0
                tooltip: "Clear filter (Escape); keeps checked exports"
                onClicked: { search.text = ""; search.forceActiveFocus() }
            }
        }

        Flow {
            id: actions
            objectName: "instanceSelectionActions"
            width: parent.width
            spacing: 4
            enabled: app.instanceSelectionEditable
            Repeater {
                model: [
                    {label: "Only matching", key: "matching", tip: "Check matching exports and uncheck every other optional export"},
                    {label: "Only selected", key: "picked", tip: "Check highlighted rows, including any outside this filter, and uncheck the rest"},
                    {label: "All", key: "all", tip: "Check every optional export, including those outside the filter"},
                    {label: "Clear checks", key: "clear", tip: "Uncheck every optional export, including those outside the filter"}
                ]
                delegate: FocusScope {
                    objectName: "instanceAction_" + modelData.key
                    width: actionButton.width
                    height: 25
                    activeFocusOnTab: true
                    enabled: modelData.key === "matching" ? app.matchingInstanceCount > 0
                           : modelData.key === "picked" ? app.pickedInstanceCount > 0
                           : app.optionalInstanceCount > 0
                    opacity: enabled && actions.enabled ? 1 : 0.45
                    function apply() {
                        if (modelData.key === "matching") app.checkOnlyMatchingInstances()
                        else if (modelData.key === "picked") app.checkOnlyPickedInstances()
                        else app.setAllInstancesToggled(modelData.key === "all")
                    }
                    Keys.onSpacePressed: apply()
                    Keys.onReturnPressed: apply()
                    Button {
                        id: actionButton
                        text: modelData.label
                        tooltip: modelData.tip
                        height: parent.height
                        padding: 12
                        elevation: 1
                        onClicked: parent.apply()
                    }
                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.color: Theme.primaryColor
                        border.width: parent.activeFocus ? 1 : 0
                    }
                }
            }
        }

        Label {
            objectName: "instanceSelectionSummary"
            width: parent.width
            wrapMode: Text.Wrap
            text: app.enabledInstanceCount + " / " + app.optionalInstanceCount + " checked · "
                + app.matchingInstanceCount + " matching"
                + (app.requiredInstanceCount ? " · " + app.requiredInstanceCount + " required" : "")
        }
        Label {
            objectName: "hiddenSelectionWarning"
            width: parent.width
            wrapMode: Text.Wrap
            visible: app.hiddenEnabledInstanceCount > 0
            color: Theme.dark.warningColor
            text: app.hiddenEnabledInstanceCount + " checked outside the filter — still included."
        }
        Label {
            width: parent.width
            wrapMode: Text.Wrap
            color: Theme.dark.subTextColor
            text: app.pickedInstanceCount + " rows selected · Ctrl/Shift-click for a subset."
        }
        Label {
            width: parent.width
            wrapMode: Text.Wrap
            color: Theme.dark.subTextColor
            text: "Run selection only. Reset restores saved tag states."
        }
        Rectangle { width: parent.width; height: 1; color: Theme.dark.dividerColor }
    }

    List {
        id: exports
        objectName: "exportList"
        model: app.instanceProxy
        selectionEnabled: app.instanceSelectionEditable
        anchors.top: toolbar.bottom
        anchors.topMargin: 5
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        section.property: "object.category"
        section.delegate: SectionItem {
            text: section
            object: app.instanceProxy.itemByName(section)
            onSectionClicked: app.hideSection(!hideState, text)
            onLabelClicked: app.toggleSection(!checkState, text)
        }
        onItemPicked: function(index, extend, rangeSelect) { app.pickInstance(index, extend, rangeSelect) }
        onItemToggled: app.toggleInstance(index)
        onActionTriggered: function(action, index) {
            if (action.name === "options") browser.settingsEntered(index)
            else if (action.name === "solo") app.soloInstance(index)
            else if (action.name === "repair") app.repairInstance(index)
            else if (action.name === "enter") browser.instanceEntered(index)
            else if (action.name === "comment") browser.commentEntered(index)
        }
        Label {
            anchors.top: parent.top
            anchors.topMargin: 34
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width - 12
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            visible: app.optionalInstanceCount > 0 && app.matchingInstanceCount === 0
            text: "No matching exports. Clear or change the filter."
            color: Theme.dark.subTextColor
        }
    }
}
