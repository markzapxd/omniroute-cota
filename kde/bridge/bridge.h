#pragma once
#include <QObject>
#include <QVariantMap>
#include <QtQml/qqmlregistration.h>

class Bridge : public QObject {
    Q_OBJECT
    QML_ELEMENT
    Q_PROPERTY(QVariantMap state READ state NOTIFY stateChanged)
public:
    explicit Bridge(QObject *parent = nullptr);
    QVariantMap state() const;
    Q_INVOKABLE void refresh();
    Q_INVOKABLE void openSettings();
    Q_INVOKABLE void logout();
public slots:
    void update(const QString &raw);
signals:
    void stateChanged();
private:
    QVariantMap m_state;
    void failure();
    void invoke(const QString &method);
};
