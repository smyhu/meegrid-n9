import QtQuick 1.1
import com.nokia.meego 1.0

// row with an optional icon, a title and a switch
Item {
    id: row
    property alias title: t.text
    property string icon: ""
    property bool checked: false
    signal toggled(bool value)
    function reset() { sw.checked = row.checked }
    width: parent.width
    height: 80
    Image {
        id: img
        visible: row.icon != ""
        source: row.icon
        width: 48; height: 48
        smooth: true
        anchors.left: parent.left
        anchors.leftMargin: 16
        anchors.verticalCenter: parent.verticalCenter
    }
    Text {
        id: t
        anchors.left: row.icon != "" ? img.right : parent.left
        anchors.leftMargin: 16
        anchors.right: sw.left
        anchors.rightMargin: 8
        anchors.verticalCenter: parent.verticalCenter
        elide: Text.ElideRight
        font.family: "Nokia Pure Text"
        font.pixelSize: 26
        font.bold: true
        color: "white"
    }
    Switch {
        id: sw
        anchors.right: parent.right
        anchors.rightMargin: 16
        anchors.verticalCenter: parent.verticalCenter
        checked: row.checked
        onCheckedChanged: if (checked != row.checked) row.toggled(checked)
    }
}
