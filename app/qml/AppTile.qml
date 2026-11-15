import QtQuick 1.1
import com.nokia.meego 1.0

// One launcher entry as on the home screen: app icon or folder (2x2 mini
// icons) with the name below. Apps not installed now are dimmed.
Item {
    id: tile
    property string name: ""
    property string icon: ""
    property bool folder: false
    property variant thumbs: []
    property bool missing: false
    property int iconSize: 80
    property bool showName: true
    width: 120
    height: showName ? iconSize + 44 : iconSize
    opacity: missing ? 0.35 : 1

    // placeholder: grey squircle with the first letter (no icon / icon not found)
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        width: tile.iconSize; height: tile.iconSize
        radius: tile.iconSize * 0.22
        color: "#3a3a3a"
        visible: !tile.folder && img.status != Image.Ready
        Text {
            anchors.centerIn: parent
            text: tile.name.substring(0, 1).toUpperCase()
            color: "#cfeca0"
            font.pixelSize: tile.iconSize * 0.45
            font.bold: true
        }
    }
    Image {
        id: img
        anchors.horizontalCenter: parent.horizontalCenter
        width: tile.iconSize; height: tile.iconSize
        sourceSize.width: tile.iconSize; sourceSize.height: tile.iconSize
        smooth: true
        source: tile.folder ? "" : tile.icon
        visible: !tile.folder
    }
    // folder: dark rounded box with up to 4 mini icons
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        width: tile.iconSize; height: tile.iconSize
        radius: tile.iconSize * 0.22
        color: "#262626"
        border.color: "#5f7f45"
        border.width: tile.iconSize >= 40 ? 2 : 1
        visible: tile.folder
        Grid {
            anchors.centerIn: parent
            columns: 2
            spacing: tile.iconSize * 0.06
            Repeater {
                model: tile.folder ? tile.thumbs : []
                Image {
                    width: tile.iconSize * 0.38; height: tile.iconSize * 0.38
                    sourceSize.width: width; sourceSize.height: height
                    smooth: true
                    source: modelData
                }
            }
        }
    }
    Text {
        visible: tile.showName
        anchors { top: parent.top; topMargin: tile.iconSize + 6; horizontalCenter: parent.horizontalCenter }
        width: tile.width - 8
        horizontalAlignment: Text.AlignHCenter
        elide: Text.ElideRight
        text: tile.name
        color: "white"
        font.family: "Nokia Pure Text"
        font.pixelSize: 18
    }
}
