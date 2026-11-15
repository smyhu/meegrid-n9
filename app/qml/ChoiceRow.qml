import QtQuick 1.1

// row with a title and the chosen value; tap opens a selection dialog
Item {
    id: row
    property alias title: t.text
    property alias value: v.text
    signal clicked
    width: parent.width
    height: 88
    Rectangle { anchors.fill: parent; color: "#1A1A1A"; visible: mouse.pressed }
    Column {
        anchors.left: parent.left
        anchors.leftMargin: 16
        anchors.verticalCenter: parent.verticalCenter
        Text { id: t; font.family: "Nokia Pure Text"; font.pixelSize: 26; font.bold: true; color: "white" }
        Text { id: v; font.family: "Nokia Pure Text"; font.pixelSize: 22; color: "#cfeca0" }
    }
    MouseArea { id: mouse; anchors.fill: parent; onClicked: row.clicked() }
}
