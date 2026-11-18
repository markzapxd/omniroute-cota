// SPDX-License-Identifier: GPL-3.0-or-later
// Adapted from izll/plasma-claude-usage, contents/ui/CompactView.qml.
// Copyright upstream contributors. OmniQuota adaptation: 2026.
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents

Item {
    id: compact
    property string percentage: "—"
    property real remaining: -1
    property bool stale: false
    signal activated()

    // Reserve the complete row width in Plasma's panel layout, as upstream does.
    Layout.minimumWidth: implicitWidth
    Layout.preferredWidth: implicitWidth
    Layout.maximumWidth: implicitWidth
    Layout.minimumHeight: 0
    Layout.preferredHeight: -1
    readonly property real ringSize: Math.max(8, Math.min(30, height - 2))
    implicitWidth: Math.ceil(ringSize + percentageLabel.implicitWidth + 12)
    implicitHeight: 16
    clip: true

    MouseArea {
        anchors.fill: parent
        onClicked: compact.activated()
        Accessible.name: "Cota restante " + compact.percentage
        Accessible.role: Accessible.Button
    }
    RowLayout {
        id: usageRow
        anchors.centerIn: parent
        spacing: 4
        QuotaRing {
            Layout.minimumWidth: compact.ringSize
            Layout.preferredWidth: compact.ringSize
            Layout.maximumWidth: compact.ringSize
            Layout.minimumHeight: compact.ringSize
            Layout.preferredHeight: compact.ringSize
            Layout.maximumHeight: compact.ringSize
            remaining: compact.remaining
            opacity: compact.stale ? 0.5 : 1
        }
        PlasmaComponents.Label {
            id: percentageLabel
            text: compact.percentage + (compact.stale ? " *" : "")
            font.pixelSize: Math.max(8, Math.min(11, compact.height - 6))
            Layout.preferredWidth: implicitWidth
            Layout.minimumWidth: implicitWidth
        }
    }
}
