import QtQuick 1.1
import com.nokia.meego 1.0
import "strings.js" as S

// What the home screen of one backup looks like: main grid in order, the
// contents of each folder and the quick launch bar. Drawn from the backup's data.
Page {
    id: page
    orientationLock: PageOrientation.LockPortrait
    property string file: ""
    property string date: ""
    property variant owner
    property variant pv: JSON.parse(backend.preview(file))

    Image { source: "background.png"; y: -36; smooth: false }
    Header {
        id: header
        text: page.date
        subText: S.t(uiLang, "previewSub")
    }

    Flickable {
        id: flick
        anchors { top: header.bottom; left: parent.left; right: parent.right; bottom: bar.top }
        contentWidth: width
        contentHeight: col.height + 24
        flickableDirection: Flickable.VerticalFlick
        clip: true

        Column {
            id: col
            width: parent.width
            Item { width: 1; height: 16 }
            Label {
                visible: !page.pv.ok
                x: 16; width: parent.width - 32
                wrapMode: Text.WordWrap
                text: S.t(uiLang, "readError") + "\n" + page.pv.error
            }
            Grid {
                x: 0
                columns: 4
                Repeater {
                    model: page.pv.ok ? page.pv.grid : []
                    AppTile {
                        name: modelData.name
                        icon: modelData.icon
                        folder: modelData.type == "folder"
                        thumbs: modelData.thumbs ? modelData.thumbs : []
                        missing: modelData.missing
                    }
                }
            }
            Repeater {
                model: page.pv.ok ? page.pv.folders : []
                Column {
                    width: col.width
                    Item { width: 1; height: 12 }
                    Label {
                        x: 16
                        text: modelData.name
                        color: appWindow.accent
                        font.pixelSize: 24
                        font.bold: true
                    }
                    Rectangle { x: 16; width: parent.width - 32; height: 1; color: "#5f7f45" }
                    Item { width: 1; height: 12 }
                    Grid {
                        columns: 4
                        Repeater {
                            model: modelData.items
                            AppTile {
                                name: modelData.name
                                icon: modelData.icon
                                missing: modelData.missing
                            }
                        }
                    }
                }
            }
        }
    }
    ScrollDecorator { flickableItem: flick }

    // quick launch bar as at the bottom of the home screen
    Rectangle {
        id: bar
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 100
        color: "#000000"
        opacity: 0.85
        Rectangle { width: parent.width; height: 1; color: "#333333" }
        Row {
            anchors.centerIn: parent
            Repeater {
                model: page.pv.ok ? page.pv.bar : []
                AppTile {
                    name: modelData.name
                    icon: modelData.icon
                    missing: modelData.missing
                    iconSize: 72
                    showName: false
                }
            }
        }
    }

    tools: ToolBarLayout {
        ToolIcon { iconId: "toolbar-back"; onClicked: pageStack.pop() }
        ToolButton {
            text: S.t(uiLang, "restore")
            anchors.centerIn: parent
            enabled: page.pv.ok
            onClicked: {
                var o = page.owner;
                var f = page.file;
                var d = page.date;
                pageStack.pop();
                o.askRestore(f, d);
            }
        }
    }
}
