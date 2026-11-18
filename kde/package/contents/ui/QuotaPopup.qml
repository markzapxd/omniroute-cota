import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    id: popup
    property var state: ({})
    signal refreshRequested()
    signal settingsRequested()
    signal logoutRequested()
    readonly property color green: "#2ecc71"
    readonly property color ink: Kirigami.Theme.textColor
    readonly property color muted: Kirigami.Theme.disabledTextColor
    color: Kirigami.Theme.backgroundColor
    radius: 16
    implicitWidth: 580
    implicitHeight: body.implicitHeight + 40
    Layout.minimumWidth: 420
    Layout.preferredWidth: 580
    Layout.minimumHeight: implicitHeight
    property double now: Date.now()
    Timer { interval: 30000; running: true; repeat: true; onTriggered: popup.now = Date.now() }
    function age() {
        const stamp = Date.parse(state.updatedAt || "");
        if (!isFinite(stamp)) return "Sem consulta";
        const seconds = Math.max(0, Math.floor((now - stamp) / 1000));
        return seconds < 60 ? "atualizado há " + seconds + "s" : "atualizado há " + Math.floor(seconds / 60) + "min";
    }
    function countdown(value) {
        const stamp = Date.parse(value || "");
        if (!isFinite(stamp)) return "Renovação indisponível";
        const minutes = Math.max(0, Math.ceil((stamp - now) / 60000));
        if (minutes === 0) return "Aguardando renovação";
        if (minutes >= 1440) return Math.floor(minutes / 1440) + "d " + Math.floor(minutes % 1440 / 60) + "h";
        return Math.floor(minutes / 60) + "h " + minutes % 60 + "m";
    }
    ColumnLayout {
        id: body
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
        spacing: 18
        RowLayout {
            Layout.fillWidth: true
            Label { text: "OmniRoute Cota"; font.bold: true; font.pixelSize: 16; Layout.fillWidth: true }
            Label { text: popup.age(); color: popup.muted; font.pixelSize: 11 }
            ToolButton { text: "↻"; onClicked: popup.refreshRequested(); ToolTip.text: "Atualizar cota"; ToolTip.visible: hovered }
        }
        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: popup.muted; opacity: 0.25 }
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 12
            rowSpacing: 12
            Repeater {
                model: popup.state.windows || []
                delegate: Rectangle {
                    id: card
                    required property var modelData
                    Layout.fillWidth: true
                    implicitWidth: 245
                    implicitHeight: cardBody.implicitHeight + 24
                    radius: 12
                    color: Qt.rgba(popup.ink.r, popup.ink.g, popup.ink.b, 0.07)
                    ColumnLayout {
                        id: cardBody
                        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
                        spacing: 9
                        Label { text: card.modelData.label.toUpperCase(); color: popup.muted; font.bold: true; font.pixelSize: 11; Layout.fillWidth: true; elide: Text.ElideRight }
                        Label { text: typeof card.modelData.remainingPercent === "number" ? Math.round(card.modelData.remainingPercent) + "%" : "—"; color: popup.green; font.bold: true; font.pixelSize: 28 }
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 8
                            radius: 4
                            color: Qt.rgba(popup.ink.r,popup.ink.g,popup.ink.b,0.16)
                            Rectangle { width: parent.width * (typeof card.modelData.remainingPercent === "number" ? Math.max(0, Math.min(100, card.modelData.remainingPercent)) / 100 : 0); height: parent.height; radius: 4; color: popup.green }
                        }
                        Label {
                            Layout.fillWidth: true
                            text: {
                                const date = new Date(card.modelData.resetAt || "");
                                return isFinite(date.getTime()) ? "Renova: " + date.toLocaleString(Qt.locale(), "dd/MM HH:mm") : "Sem horário de renovação";
                            }
                            color: popup.muted; font.pixelSize: 11; wrapMode: Text.Wrap
                        }
                        Label { text: popup.countdown(card.modelData.resetAt); color: popup.muted; font.bold: true; font.pixelSize: 17 }
                    }
                }
            }
        }
        Label { visible: !(popup.state.windows || []).length; text: "Entre para consultar sua cota."; Layout.fillWidth: true }
        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: popup.muted; opacity: 0.25 }
        RowLayout {
            Layout.fillWidth: true
            Rectangle { width: 8; height: 12; radius: 4; color: popup.state.status === "ready" && !popup.state.stale ? popup.green : popup.muted }
            Label {
                text: popup.state.status === "ready" && !popup.state.stale ? "Cota restante · consulta atualizada" : popup.state.message || "Serviço indisponível"
                font.pixelSize: 11; wrapMode: Text.Wrap; Layout.fillWidth: true
            }
            ToolButton { text: "⚙"; onClicked: popup.settingsRequested(); ToolTip.text: "Configurar / entrar"; ToolTip.visible: hovered }
            ToolButton { text: "Sair"; onClicked: popup.logoutRequested() }
        }
    }
}
