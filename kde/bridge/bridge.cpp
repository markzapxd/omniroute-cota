#include "bridge.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QDBusConnection>
#include <QDBusMessage>
#include <QDBusPendingCallWatcher>
#include <QDBusPendingReply>

Bridge::Bridge(QObject *parent) : QObject(parent) {
    QDBusConnection::sessionBus().connect("io.github.omniquota.Service", "/io/github/omniquota/Service",
        "io.github.omniquota.Service", "StateChanged", this, SLOT(update(QString)));
    invoke("GetState");
}
QVariantMap Bridge::state() const { return m_state; }
void Bridge::refresh() { invoke("Refresh"); }
void Bridge::openSettings() { invoke("OpenSettings"); }
void Bridge::logout() { invoke("Logout"); }
void Bridge::update(const QString &raw) {
    const auto document = QJsonDocument::fromJson(raw.toUtf8());
    if (!document.isObject()) { failure(); return; }
    m_state = document.object().toVariantMap();
    emit stateChanged();
}
void Bridge::failure() {
    m_state.insert("status", "error");
    m_state.insert("message", "Operação falhou: serviço indisponível ou ocupado. Aguarde a consulta e tente novamente.");
    m_state.insert("stale", true);
    emit stateChanged();
}
void Bridge::invoke(const QString &method) {
    auto message = QDBusMessage::createMethodCall("io.github.omniquota.Service", "/io/github/omniquota/Service",
        "io.github.omniquota.Service", method);
    auto *watcher = new QDBusPendingCallWatcher(QDBusConnection::sessionBus().asyncCall(message, 60000), this);
    connect(watcher, &QDBusPendingCallWatcher::finished, this, [this, method](QDBusPendingCallWatcher *finished) {
        if (finished->isError()) failure();
        else if (method == "GetState") {
            QDBusPendingReply<QString> reply = *finished;
            if (reply.isError()) failure(); else update(reply.value());
        }
        finished->deleteLater();
    });
}
