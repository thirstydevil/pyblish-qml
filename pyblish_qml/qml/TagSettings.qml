import QtQuick 2.3
import QtQuick.Layouts 1.1
import Pyblish 0.1 as P
import Pyblish.ListItems 0.1 as L
import Perspective 0.1 as Perspective

Item {
    id: page
    property QtObject item
    property int instanceIndex: -1
    property var sections: []
    property var draft: ({})
    property int revision: 0
    property bool busy: true
    property string tagName: "Tag options"
    property string message: "Loading options…"
    signal closed()

    function value(section, field) {
        var dependency = revision
        return draft[section.key][field.id]
    }
    function update(section, field, value) {
        draft[section.key][field.id] = value
        revision++
    }
    function selected(section, field, id) {
        var choice = value(section, field)
        return choice.mode === "all" || choice.ids.indexOf(id) !== -1
    }
    function ids(section, field) {
        return field.choices.filter(function(c) { return selected(section, field, c.id) }).map(function(c) { return c.id })
    }
    function groups(field) {
        var result = []
        field.choices.forEach(function(c) { if (result.indexOf(c.group || "Outputs") === -1) result.push(c.group || "Outputs") })
        return result.sort()
    }
    function toggle(section, field, id, checked) {
        var chosen = ids(section, field).filter(function(i) { return i !== id })
        if (checked) chosen.push(id)
        update(section, field, {mode: "selected", ids: chosen})
    }
    Component.onCompleted: app.tagSettings(instanceIndex, "", false)
    Connections {
        target: app
        function onPublishSettingsResult(payload) {
            var result = JSON.parse(payload)
            page.busy = false
            if (!result.ok) { page.message = result.error; return }
            if (result.saved) { page.closed(); return }
            var values = {}
            result.sections.forEach(function(section) { values[section.key] = section.values })
            page.draft = values
            page.sections = result.sections
            page.tagName = result.name
            page.message = "Options are stored on the scene tags. Save Maya before publishing."
        }
    }
    P.ActionBar {
        id: actionBar
        width: parent.width
        actions: [
            P.Action { iconName: "button-back"; enabled: !page.busy; onTriggered: page.closed() },
            P.Action { name: "Tag options" }
        ]
    }
    P.View {
        elevation: 1
        anchors { left: parent.left; right: parent.right; top: actionBar.bottom; bottom: footer.top; topMargin: -1 }
        P.View {
            id: contentPanel
            elevation: -1
            anchors.fill: parent
            anchors.margins: margins
            Perspective.Header {
                id: header
                anchors { top: parent.top; left: parent.left; right: parent.right; leftMargin: 10; rightMargin: 10 }
                P.Spacer { height: 10 }
                Perspective.Gadget {
                    width: parent.width
                    title: page.item ? (page.item.label || page.item.name) : page.tagName
                    subheading: page.item ? page.item.familiesConcatenated : "Publish tag settings"
                    itemType: "instance"
                    duration: page.item ? page.item.duration : 0
                    finishedAt: page.item ? page.item.finishedAt : 0
                    hasError: page.item ? page.item.hasError : false
                    amountFailed: page.item ? page.item.amountFailed : 0
                    amountPassed: page.item ? page.item.amountPassed : 0
                }
                P.Spacer { height: 10 }
            }
            Flickable {
                id: scroll
                anchors { top: header.bottom; bottom: parent.bottom; left: parent.left; right: scrollbar.left; margins: 10 }
                contentWidth: width
                contentHeight: fieldsColumn.height
                boundsBehavior: Flickable.StopAtBounds
                clip: true
                ColumnLayout {
                    id: fieldsColumn
                    width: scroll.width
                    spacing: 14
                    Repeater {
                        model: page.sections
                        delegate: ColumnLayout {
                            id: sectionView
                            property var section: modelData
                            Layout.fillWidth: true
                            spacing: 8
                            P.Label { text: sectionView.section.title; style: "subheading"; font.bold: true }
                            P.Label { text: sectionView.section.description || ""; Layout.fillWidth: true; wrapMode: Text.WordWrap; opacity: 0.7 }
                            Repeater {
                                model: sectionView.section.fields
                                delegate: Loader {
                                    property var field: modelData
                                    property var section: sectionView.section
                                    Layout.fillWidth: true
                                    sourceComponent: field.type === "outputs" ? outputControl : field.type === "bool" ? boolControl : choiceControl
                                }
                            }
                        }
                    }
                }
            }
            P.Scrollbar {
                id: scrollbar
                flickable: scroll
                width: 10
                anchors { top: header.bottom; bottom: parent.bottom; right: parent.right; margins: 5 }
            }
        }
    }
    P.View {
        id: footer
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: footerLayout.implicitHeight + 10
        ColumnLayout {
            id: footerLayout
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 5 }
            spacing: 4
            P.Label { text: page.message; Layout.fillWidth: true; wrapMode: Text.WordWrap; opacity: 0.7 }
            RowLayout {
                Layout.fillWidth: true
                L.Standard {
                    implicitHeight: 20
                    id: applyAll
                    Layout.fillWidth: true
                    active: !page.busy
                    text: "Apply to all checked compatible tags"
                    onClicked: checked = !checked
                }
                P.Button { text: "Cancel"; style: "body1"; elevation: 1; enabled: !page.busy; onClicked: page.closed() }
                P.Button {
                    text: "Apply to scene tags"; style: "body1"; elevation: 1
                    enabled: !page.busy && page.sections.length > 0
                    onClicked: { page.busy = true; app.tagSettings(page.instanceIndex, JSON.stringify(page.draft), applyAll.checked) }
                }
            }
        }
    }
    Component {
        id: boolControl
        L.Standard {
                    implicitHeight: 20
            text: field.label; active: !page.busy
            checked: page.value(section, field)
            onClicked: page.update(section, field, !checked)
        }
    }
    Component {
        id: choiceControl
        ColumnLayout {
            P.Label { text: field.label }
            Repeater {
                model: field.choices
                delegate: L.Standard {
                    implicitHeight: 20
                    Layout.fillWidth: true; text: modelData.label; active: !page.busy
                    checked: page.value(section, field) === modelData.id
                    onClicked: page.update(section, field, modelData.id)
                }
            }
        }
    }
    Component {
        id: outputControl
        ColumnLayout {
            id: outputView
            property string preview: ""
            spacing: 8
            RowLayout {
                Layout.fillWidth: true
                P.Label { text: field.label; font.bold: true; Layout.fillWidth: true }
                P.Label { text: page.ids(section, field).length + " / " + field.choices.length + " outputs"; opacity: 0.7 }
            }
            RowLayout {
                L.Standard {
                    implicitHeight: 20
                    Layout.preferredWidth: 120; active: !page.busy; text: "All outputs"
                    checked: page.value(section, field).mode === "all"
                    onClicked: page.update(section, field, {mode: "all", ids: []})
                }
                L.Standard {
                    implicitHeight: 20
                    Layout.fillWidth: true; active: !page.busy; text: "Selected outputs"
                    checked: page.value(section, field).mode === "selected"
                    onClicked: page.update(section, field, {mode: "selected", ids: page.ids(section, field)})
                }
            }
            RowLayout {
                P.View {
                    Layout.fillWidth: true; Layout.preferredHeight: 30; elevation: -1
                    P.TextField {
                        id: filter
                        anchors { fill: parent; margins: 6 }
                        wrapMode: TextEdit.NoWrap
                        P.Label { text: "Filter outputs…"; visible: !filter.text && !filter.activeFocus; opacity: 0.5 }
                    }
                }
                P.Button {
                    text: "Select missing"; style: "body1"; elevation: 1
                    onClicked: page.update(section, field, {mode: "selected", ids: field.choices.filter(function(c) { return !c.exists }).map(function(c) { return c.id })})
                }
                P.Button { text: "Clear"; style: "body1"; elevation: 1; onClicked: page.update(section, field, {mode: "selected", ids: []}) }
            }
            GridLayout {
                Layout.fillWidth: true
                columns: width > 620 ? 2 : 1
                columnSpacing: 24
                rowSpacing: 12
                Repeater {
                    model: page.groups(field)
                    delegate: ColumnLayout {
                        property string outputGroup: modelData
                        Layout.fillWidth: true; Layout.alignment: Qt.AlignTop
                        spacing: 0
                        P.Label { text: outputGroup; font.bold: true; bottomPadding: 5 }
                        Repeater {
                            model: field.choices.filter(function(c) { return (c.group || "Outputs") === outputGroup }).sort(function(a, b) { return a.label.localeCompare(b.label) })
                            delegate: RowLayout {
                                property var output: modelData
                                visible: !filter.text || output.label.toLowerCase().indexOf(filter.text.toLowerCase()) !== -1
                                Layout.fillWidth: true
                                L.Standard {
                    implicitHeight: 20
                                    Layout.fillWidth: true; active: !page.busy
                                    text: output.label
                                    checked: page.selected(section, field, output.id)
                                    onClicked: { page.toggle(section, field, output.id, !checked); outputView.preview = output.destination }
                                }
                                P.Label { text: output.exists ? "Published" : "Missing"; opacity: output.exists ? 0.45 : 0.9 }
                            }
                        }
                    }
                }
            }
            P.Label { text: "Destination preview"; font.bold: true; topPadding: 8 }
            P.View {
                Layout.fillWidth: true; Layout.preferredHeight: destination.implicitHeight + 16; elevation: -1
                P.TextArea {
                    id: destination
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 8 }
                    wrapMode: Text.WrapAnywhere
                    text: {
                        var choices = field.choices.filter(function(c) { return page.selected(section, field, c.id) })
                        var preview = choices.filter(function(c) { return c.destination === outputView.preview })
                        return preview.length ? preview[0].destination : choices.length ? choices[0].destination : "No outputs selected."
                    }
                }
            }
            P.Label { text: "Unselected published files and metadata links are kept."; Layout.fillWidth: true; wrapMode: Text.WordWrap; opacity: 0.7 }
        }
    }
}

