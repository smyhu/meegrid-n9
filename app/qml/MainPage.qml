import QtQuick 1.1
import com.nokia.meego 1.0
import "strings.js" as S

// List of layout backups. Tap = restore (with a check for missing apps),
// press and hold = delete. Toolbar: save the layout now.
Page {
    id: page
    orientationLock: PageOrientation.LockPortrait
    property int total: 0
    property string current: ""
    property string currentDate: ""
    property string waitId: ""
    property string waitCmd: ""
    property int waitTicks: 0

    property variant auto: JSON.parse(backend.settings())

    function reload() {
        page.auto = JSON.parse(backend.settings());
        model.clear();
        var r = JSON.parse(backend.backups());
        if (!r.ok) {
            emptyText.text = S.t(uiLang, "readError") + "\n" + r.error;
            page.total = 0;
            return;
        }
        emptyText.text = S.t(uiLang, "empty");
        for (var i = 0; i < r.items.length; ++i) {
            var b = r.items[i];
            model.append({ "file": b.file, "date": b.date, "kind": b.kind, "ok": b.ok,
                           "icons": b.icons, "folders": b.folders, "missing": b.missing.length,
                           "thumb": b.ok ? backend.thumb(b.file) : "[]" });
        }
        page.total = r.items.length;
    }
    Component.onCompleted: reload()
    onStatusChanged: if (status == PageStatus.Activating) reload()

    function askRestore(file, date) {
        page.current = file;
        page.currentDate = date;
        var d = JSON.parse(backend.details(file));
        var msg = S.t(uiLang, "restoreInfo");
        if (d.ok && d.folders.length > 0)
            msg += "<br><br>" + S.a(uiLang, "folders", d.folders.join(", "));
        if (d.ok && d.missing.length > 0)
            msg += "<br><br><font color=\"#ff7a6a\">" + S.a(uiLang, "missingInfo", d.missing.join(", ")) + "</font>";
        restoreDialog.titleText = S.a(uiLang, "restoreQ", date);
        restoreDialog.message = msg;
        restoreDialog.open();
    }

    function wait(id, cmd) {
        page.waitId = id;
        page.waitCmd = cmd;
        page.waitTicks = 0;
        poll.start();
    }
    function finished(st) {
        poll.stop();
        page.waitId = "";
        if (st.state == "done")
            appWindow.showBanner(page.waitCmd == "restore" ? S.t(uiLang, "restored") : S.a(uiLang, "saved", st.file));
        else if (st.state == "failed")
            appWindow.showBanner(S.a(uiLang, "failed", S.err(uiLang, st.error)));
        else
            appWindow.showBanner(S.t(uiLang, "noAnswer"));
        reload();
    }

    Timer {
        id: poll
        interval: 500
        repeat: true
        onTriggered: {
            page.waitTicks++;
            var st = JSON.parse(backend.status(page.waitId));
            if (st.state == "done" || st.state == "failed")
                page.finished(st);
            else if (page.waitTicks > 90)
                page.finished({ "state": "timeout" });
        }
    }

    Image { source: "background.png"; y: -36; smooth: false }
    Header {
        id: header
        text: "MeeGrid"
        subText: S.a(uiLang, "subtitle", page.total)
    }
    ListModel { id: model }

    // automatic backup state; tap = settings
    Item {
        id: autoBar
        anchors { top: header.bottom; left: parent.left; right: parent.right }
        height: 56
        Rectangle { anchors.fill: parent; color: "#ffffff"; opacity: autoMouse.pressed ? 0.12 : 0 }
        Label {
            anchors { left: parent.left; right: parent.right; margins: 16; verticalCenter: parent.verticalCenter }
            elide: Text.ElideRight
            font.pixelSize: 20
            color: page.auto.ok && page.auto.settings.auto ? appWindow.accent : "#8c8c8c"
            text: !page.auto.ok ? "" : (!page.auto.settings.auto ? S.t(uiLang, "statusOff")
                  : S.t(uiLang, "statusOn").replace("%1", page.auto.settings.every == 7 ? S.t(uiLang, "weekly") : S.t(uiLang, "daily"))
                        .replace("%2", (page.auto.settings.hour < 10 ? "0" : "") + page.auto.settings.hour + ":00")
                        .replace("%3", page.auto.next.substring(5)))
        }
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#333333" }
        MouseArea { id: autoMouse; anchors.fill: parent; onClicked: pageStack.push(Qt.resolvedUrl("SettingsPage.qml")) }
    }

    ListView {
        id: list
        anchors { top: autoBar.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
        clip: true
        model: model
        delegate: Item {
            width: list.width
            height: 104
            property string thumbJson: model.thumb
            Rectangle {
                anchors.fill: parent
                color: "#ffffff"
                opacity: mouse.pressed ? 0.12 : 0
            }
            // small picture of the first rows of the home screen
            Rectangle {
                id: thumbBox
                anchors { right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter }
                width: 88; height: 88
                radius: 8
                color: "#000000"
                opacity: model.ok ? 1 : 0
                Grid {
                    anchors.centerIn: parent
                    columns: 4
                    spacing: 2
                    Repeater {
                        model: JSON.parse(thumbJson)
                        AppTile {
                            width: 19
                            iconSize: 19
                            showName: false
                            icon: modelData.icon
                            folder: modelData.folder
                            thumbs: modelData.thumbs
                            missing: modelData.missing
                        }
                    }
                }
            }
            Column {
                anchors { left: parent.left; right: thumbBox.left; leftMargin: 16; rightMargin: 12; verticalCenter: parent.verticalCenter }
                Label {
                    width: parent.width
                    text: model.date
                    font.pixelSize: 26
                    font.bold: true
                    elide: Text.ElideRight
                }
                Label {
                    width: parent.width
                    text: S.t(uiLang, "kind_" + model.kind) + " · "
                          + (model.ok ? S.a2(uiLang, "counts", model.icons, model.folders) : S.t(uiLang, "broken"))
                    font.pixelSize: 20
                    color: model.kind == "manual" ? appWindow.accent : "#d0d0d0"
                    elide: Text.ElideRight
                }
                Label {
                    width: parent.width
                    visible: model.missing > 0
                    text: S.a(uiLang, "missingN", model.missing)
                    font.pixelSize: 18
                    color: appWindow.red
                    elide: Text.ElideRight
                }
            }
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#222222" }
            MouseArea {
                id: mouse
                anchors.fill: parent
                enabled: page.waitId == ""
                onClicked: {
                    if (model.ok)
                        pageStack.push(Qt.resolvedUrl("PreviewPage.qml"), { file: model.file, date: model.date, owner: page });
                }
                onPressAndHold: {
                    page.current = model.file;
                    page.currentDate = model.date;
                    ctx.open();
                }
            }
        }
    }
    ScrollDecorator { flickableItem: list }

    Label {
        id: emptyText
        visible: page.total == 0
        anchors { left: parent.left; right: parent.right; margins: 32; verticalCenter: parent.verticalCenter }
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        color: "#8c8c8c"
        font.pixelSize: 26
        text: S.t(uiLang, "empty")
    }

    // busy overlay while the service works
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.75
        visible: page.waitId != ""
        MouseArea { anchors.fill: parent }
    }
    Column {
        anchors.centerIn: parent
        spacing: 24
        visible: page.waitId != ""
        BusyIndicator {
            anchors.horizontalCenter: parent.horizontalCenter
            running: parent.visible
            platformStyle: BusyIndicatorStyle { size: "large" }
        }
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: page.waitCmd == "restore" ? S.t(uiLang, "restoring") : S.t(uiLang, "saving")
            color: appWindow.accent
            font.pixelSize: 26
        }
    }

    QueryDialog {
        id: restoreDialog
        acceptButtonText: S.t(uiLang, "restore")
        rejectButtonText: S.t(uiLang, "cancel")
        onAccepted: {
            var r = JSON.parse(backend.restore(page.current));
            if (r.ok)
                page.wait(r.wait, "restore");
            else
                appWindow.showBanner(S.a(uiLang, "failed", S.err(uiLang, r.error)));
        }
    }

    QueryDialog {
        id: deleteDialog
        acceptButtonText: S.t(uiLang, "delete")
        rejectButtonText: S.t(uiLang, "cancel")
        onAccepted: {
            var r = JSON.parse(backend.remove(page.current));
            if (!r.ok)
                appWindow.showBanner(r.error);
            page.reload();
        }
    }

    ContextMenu {
        id: ctx
        MenuLayout {
            MenuItem {
                text: S.t(uiLang, "delete")
                onClicked: {
                    deleteDialog.titleText = S.a(uiLang, "deleteQ", page.currentDate);
                    deleteDialog.open();
                }
            }
        }
    }

    QueryDialog {
        id: about
        titleText: "MeeGrid"
        message: S.a(uiLang, "version", appVersion) + "<br><br>" + S.t(uiLang, "aboutText") + "<br><br>"
                 + S.t(uiLang, "credit") + "<br><br><a href=\"https://github.com/smyhu/meegrid-n9\">github.com/smyhu/meegrid-n9</a>"
        acceptButtonText: S.t(uiLang, "close")
        onLinkActivated: Qt.openUrlExternally(link)
    }

    QueryDialog {
        id: toPc
        titleText: S.t(uiLang, "toPc")
        message: S.t(uiLang, "toPcText")
        acceptButtonText: S.t(uiLang, "close")
    }

    Menu {
        id: menu
        MenuLayout {
            MenuItem { text: S.t(uiLang, "settings"); onClicked: pageStack.push(Qt.resolvedUrl("SettingsPage.qml")) }
            MenuItem { text: S.t(uiLang, "toPc"); onClicked: toPc.open() }
            MenuItem { text: S.t(uiLang, "about"); onClicked: about.open() }
        }
    }

    tools: ToolBarLayout {
        ToolIcon { iconId: "toolbar-refresh"; onClicked: page.reload() }
        ToolButton {
            text: S.t(uiLang, "saveNow")
            anchors.centerIn: parent
            enabled: page.waitId == ""
            onClicked: {
                var r = JSON.parse(backend.backupNow());
                if (!r.ok)
                    appWindow.showBanner(S.a(uiLang, "failed", S.err(uiLang, r.error)));
                else if (r.wait)
                    page.wait(r.wait, "backup");
                else {
                    appWindow.showBanner(S.a(uiLang, "saved", r.file));
                    page.reload();
                }
            }
        }
        ToolIcon {
            iconId: "toolbar-view-menu"
            onClicked: menu.status == DialogStatus.Closed ? menu.open() : menu.close()
        }
    }
}
