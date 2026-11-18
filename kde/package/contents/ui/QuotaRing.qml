import QtQuick

Canvas {
    id: ring
    property real remaining: -1
    readonly property color availableColor: "#2ecc71"
    readonly property color trackColor: "#808080"
    implicitWidth: 22
    implicitHeight: 22
    onRemainingChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        const radius = Math.max(0, Math.min(width, height) / 2 - 3);
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = trackColor;
        ctx.beginPath();
        ctx.arc(width / 2, height / 2, radius, 0, Math.PI * 2);
        ctx.stroke();
        if (remaining >= 0) {
            ctx.strokeStyle = availableColor;
            ctx.beginPath();
            ctx.arc(width / 2, height / 2, radius, -Math.PI / 2,
                    -Math.PI / 2 + Math.PI * 2 * Math.min(1, remaining / 100));
            ctx.stroke();
        }
    }
}
