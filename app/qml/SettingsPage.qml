import QtQuick 1.1
import com.nokia.meego 1.0
import "strings.js" as S

// Settings of the automatic backup: on/off, how often, at what hour, how many to keep.
Page {
    id: page
    orientationLock: PageOrientation.LockPortrait

    property variant info: JSON.parse(backend.settings())
    property variant cfg: info.ok ? info.settings : { "auto": true, "every": 1, "hour": 3, "keep": 10 }
    property variant keeps: [5, 10, 20, 30]

    function tr(key) { return S.t(uiLang, key) }
    function hourLabel(h) { return (h < 10 ? "0" : "") + h + ":00" }
    function set(key, value) {
        var o = {};
        o[key] = value;
        var r = JSON.parse(backend.saveSettings(JSON.stringify(o)));
        if (r.ok)
            page.info = r;
        else
            appWindow.showBanner(S.a(uiLang, "failed", r.error));
    }

    Image { source: "background.png"; y: -36; smooth: false }
    Header { id: header; text: tr("settings") }

    Flickable {
        id: flick
        anchors { top: header.bottom; bottom: parent.bottom; left: parent.left; right: parent.right }
        contentWidth: width
        contentHeight: col.height + 32
        flickableDirection: Flickable.VerticalFlick
        clip: true

        Column {
            id: col
            width: parent.width

            SwitchRow {
                id: autoRow
                title: tr("autoTitle")
                checked: page.cfg.auto
                onToggled: {
                    if (value) {
                        page.set("auto", true);
                        appWindow.showBanner(S.a(uiLang, "autoOnBanner", page.info.next));
                    } else {
                        offDialog.open();
                    }
                }
            }
            ChoiceRow {
                visible: page.cfg.auto
                title: tr("howOften")
                value: page.cfg.every == 7 ? tr("weekly") : tr("daily")
                onClicked: { everyDialog.selectedIndex = page.cfg.every == 7 ? 1 : 0; everyDialog.open() }
            }
            ChoiceRow {
                visible: page.cfg.auto
                title: tr("atHour")
                value: page.hourLabel(page.cfg.hour)
                onClicked: { hourDialog.selectedIndex = page.cfg.hour; hourDialog.open() }
            }
            ChoiceRow {
                visible: page.cfg.auto
                title: tr("keepTitle")
                value: S.a(uiLang, "keepN", page.cfg.keep)
                onClicked: {
                    var i = 0;
                    for (var k = 0; k < page.keeps.length; ++k)
                        if (page.keeps[k] == page.cfg.keep)
                            i = k;
                    keepDialog.selectedIndex = i;
                    keepDialog.open();
                }
            }
            Item { width: 1; height: 16 }
            Label {
                x: 16; width: parent.width - 32
                visible: page.cfg.auto
                wrapMode: Text.WordWrap
                font.pixelSize: 22
                color: appWindow.accent
                text: S.a(uiLang, "lastAuto", page.info.last ? page.info.last : tr("never"))
                      + "\n" + S.a(uiLang, "nextAuto", page.info.next)
                      + (page.info.skipped ? "\n" + S.a(uiLang, "skippedLine", page.info.skippedAt) : "")
            }
            Item { width: 1; height: 16; visible: page.cfg.auto }
            Button {
                visible: page.cfg.auto
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width - 64
                text: page.info.skipped ? tr("unskip") : tr("skipNext")
                onClicked: {
                    var r = JSON.parse(backend.skipNext(!page.info.skipped));
                    if (!r.ok) {
                        appWindow.showBanner(S.a(uiLang, "failed", r.error));
                        return;
                    }
                    page.info = r;
                    appWindow.showBanner(r.skipped ? S.a2(uiLang, "skippedBanner", r.skippedAt, r.next)
                                                   : S.a(uiLang, "unskippedBanner", r.next));
                }
            }
            Item { width: 1; height: 24; visible: page.cfg.auto }
            Label {
                x: 16; width: parent.width - 32
                wrapMode: Text.WordWrap
                font.pixelSize: 20
                color: "#8c8c8c"
                text: page.cfg.auto ? tr("autoInfo") : tr("autoOffInfo")
            }
        }
    }
    ScrollDecorator { flickableItem: flick }

    SelectionDialog {
        id: everyDialog
        titleText: tr("howOften")
        model: ListModel {
            ListElement { name: "" }
            ListElement { name: "" }
        }
        Component.onCompleted: {
            model.setProperty(0, "name", tr("daily"));
            model.setProperty(1, "name", tr("weekly"));
        }
        onAccepted: page.set("every", selectedIndex == 1 ? 7 : 1)
    }

    SelectionDialog {
        id: hourDialog
        titleText: tr("atHour")
        model: ListModel { id: hours }
        Component.onCompleted: {
            for (var h = 0; h < 24; ++h)
                hours.append({ "name": page.hourLabel(h) });
        }
        onAccepted: page.set("hour", selectedIndex)
    }

    SelectionDialog {
        id: keepDialog
        titleText: tr("keepTitle")
        model: ListModel { id: keepModel }
        Component.onCompleted: {
            for (var k = 0; k < page.keeps.length; ++k)
                keepModel.append({ "name": S.a(uiLang, "keepN", page.keeps[k]) });
        }
        onAccepted: {
            var k = page.keeps[selectedIndex];
            var del = page.info.count + 1 - k;
            if (k < page.cfg.keep && del > 0) {
                keepConfirm.newKeep = k;
                keepConfirm.message = S.a2(uiLang, "keepLowerText", del, k);
                keepConfirm.open();
            } else {
                page.set("keep", k);
            }
        }
    }

    QueryDialog {
        id: offDialog
        titleText: tr("offQ")
        message: tr("offText")
        acceptButtonText: tr("turnOff")
        rejectButtonText: tr("cancel")
        onAccepted: page.set("auto", false)
        onRejected: autoRow.reset()
    }

    QueryDialog {
        id: keepConfirm
        property int newKeep: 10
        titleText: tr("keepTitle")
        acceptButtonText: tr("change")
        rejectButtonText: tr("cancel")
        onAccepted: page.set("keep", newKeep)
    }

    tools: ToolBarLayout {
        ToolIcon { iconId: "toolbar-back"; onClicked: pageStack.pop() }
    }
}
