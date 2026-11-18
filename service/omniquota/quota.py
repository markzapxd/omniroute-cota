"""Normalize OmniRoute's named quotas; never infer missing utilization."""
import math


def number(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def normalize_usage(payload: dict) -> list[dict]:
    quotas = payload.get('quotas', {})
    if not isinstance(quotas, dict):
        return []
    result = []
    for label, quota in quotas.items():
        if not isinstance(quota, dict):
            continue
        value = quota.get('remainingPercentage')
        if value is None:
            remaining, total = quota.get('remaining'), quota.get('total')
            if number(remaining) and number(total) and total > 0:
                value = remaining / total * 100
        if (quota.get('fractionReported') is False or quota.get('unlimited') is True
                or not number(value) or not 0 <= value <= 100):
            value = None
        result.append({'label': str(label), 'remainingPercent': value,
                       'resetAt': quota.get('resetAt') if isinstance(quota.get('resetAt'), str) else None})
    return result


def panel_percent(windows: list[dict]):
    values = [w['remainingPercent'] for w in windows if w['remainingPercent'] is not None]
    return min(values) if values else None
