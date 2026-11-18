import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Item {
    id: popup
    property var state: ({})
    signal refreshRequested()
    signal settingsRequested()
    signal logoutRequested()
    readonly property color green: "#2ecc71"
    readonly property color muted: Kirigami.Theme.disabledTextColor
    implicitWidth: 300
    implicitHeight: body.implicitHeight + 24
    Layout.minimumWidth: 280
    Layout.preferredWidth: 300
    Layout.maximumWidth: 320
    Layout.minimumHeight: implicitHeight
    Layout.preferredHeight: implicitHeight
    Layout.maximumHeight: implicitHeight
    property double now: Date.now()
    Timer { interval: 30000; running: popup.visible; repeat: true; onTriggered: popup.now = Date.now() }
    function renewal(value) {
        const stamp = Date.parse(value || "");
        if (!isFinite(stamp)) return "Renovação não informada";
        const minutes = Math.max(0, Math.ceil((stamp - now) / 60000));
        const duration = minutes >= 1440 ? Math.floor(minutes / 1440) + "d " + Math.floor(minutes % 1440 / 60) + "h" : Math.floor(minutes / 60) + "h " + minutes % 60 + "min";
        return minutes ? "Renova em " + duration + " · " + new Date(stamp).toLocaleString(Qt.locale("pt_BR"), "dd MMM, HH:mm") : "Aguardando renovação";
    }
    ColumnLayout {
        id: body
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
        spacing: 14
        RowLayout {
            Layout.fillWidth: true
            Label { text: "OmniRoute Cota"; font.bold: true; Layout.fillWidth: true }
            ToolButton {
                icon.name: "view-refresh"
                implicitWidth: 28; implicitHeight: 28
                onClicked: popup.refreshRequested()
                Accessible.name: "Atualizar cota"
                ToolTip.text: "Atualizar"; ToolTip.visible: hovered
            }
        }
        Repeater {
            model: popup.state.windows || []
            delegate: ColumnLayout {
                id: windowRow
                required property var modelData
                Layout.fillWidth: true
                spacing: 7
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: windowRow.modelData.label
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }
                    Label {
                        text: typeof windowRow.modelData.remainingPercent === "number" ? Math.round(windowRow.modelData.remainingPercent) + "% restante" : "Indisponível"
                        font.bold: true
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 5
                    radius: 2.5
                    color: Qt.rgba(0.5,0.5,0.5,0.25)
                    Rectangle {
                        width: parent.width * (typeof windowRow.modelData.remainingPercent === "number" ? Math.max(0,Math.min(100,windowRow.modelData.remainingPercent)) / 100 : 0)
                        height: parent.height; radius: 2.5; color: popup.green
                    }
                }
                Label {
                    text: popup.renewal(windowRow.modelData.resetAt)
                    color: popup.muted
                    font.pixelSize: 11
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
            }
        }
        Label {
            visible: typeof popup.state.bankedResetCredits === "number"
            text: "Resets disponíveis: " + (popup.state.bankedResetCredits ?? "")
            color: popup.green
            font.pixelSize: 12
            Layout.fillWidth: true
        }
        Label {
            visible: popup.state.status !== "ready" || !!popup.state.stale
            text: popup.state.stale ? "Dados desatualizados · " + (popup.state.message || "") : popup.state.message || "Entre para consultar sua cota."
            wrapMode: Text.Wrap
            Layout.fillWidth: true
            color: popup.muted
        }
        RowLayout {
            Layout.fillWidth: true
            ToolButton { text: "Configurações"; onClicked: popup.settingsRequested() }
            Item { Layout.fillWidth: true }
            ToolButton { text: "Sair"; onClicked: popup.logoutRequested() }
        }
    }
}
