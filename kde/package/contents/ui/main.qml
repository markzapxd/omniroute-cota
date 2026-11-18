import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../bridge/OmniQuota"

PlasmoidItem {
    id: root
    readonly property real panelContentWidth: compactRepresentationItem ? compactRepresentationItem.implicitWidth : 64
    Layout.minimumWidth: panelContentWidth
    Layout.preferredWidth: panelContentWidth
    Layout.maximumWidth: panelContentWidth
    Layout.minimumHeight: 0
    Bridge { id: backend }
    readonly property var state: backend.state
    readonly property string percent: typeof state.remainingPercent === "number" ? Math.round(state.remainingPercent) + "%" : "—"
    toolTipMainText: "OmniRoute Cota · " + percent + " restante"
    toolTipSubText: state.message || "Configurar / entrar"
    compactRepresentation: CompactView {
        percentage: root.percent
        remaining: typeof root.state.remainingPercent === "number" ? root.state.remainingPercent : -1
        stale: !!root.state.stale
        onActivated: root.expanded = !root.expanded
    }
    fullRepresentation: QuotaPopup {
        state: root.state
        onRefreshRequested: backend.refresh()
        onSettingsRequested: backend.openSettings()
        onLogoutRequested: backend.logout()
    }
}
