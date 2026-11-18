import QtQuick
import QtQuick.Controls
import "../kde/package/contents/ui"

ApplicationWindow {
    visible: true
    title: "OmniRoute Cota — prévia com dados sintéticos"
    width: 324
    height: preview.implicitHeight + 24
    color: "#202326"
    QuotaPopup {
        id: preview
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
        state: ({status: "ready", windows: [{label: "Semanal", remainingPercent: 91,
            resetAt: new Date(Date.now() + 6 * 86400000 + 18 * 3600000).toISOString()}], bankedResetCredits: 2})
        onRefreshRequested: feedback.text = "Atualizar acionado"
        onSettingsRequested: feedback.text = "Configurações acionado"
        onLogoutRequested: feedback.text = "Sair acionado"
    }
    Label { id: feedback; anchors.bottom: parent.bottom; text: "Prévia · dados sintéticos"; font.pixelSize: 10 }
}
