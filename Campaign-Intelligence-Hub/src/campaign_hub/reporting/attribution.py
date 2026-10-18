"""Explicit channel rules, shared by synthetic outcomes and benchmarking."""
from datetime import date, datetime, timedelta

CHANNEL_RULES={
    'direct_mail':{'window_days':60,'anchor':'mail_drop_date','exposure_unit':'mailed_households'},
    'display':{'window_days':30,'anchor':'exposure_date','exposure_unit':'exposed_users'},
}


def as_date(value):
    if isinstance(value,datetime):
        return value.date()
    return value if isinstance(value,date) else date.fromisoformat(value)


def attributable(channel,anchor_date,conversion_date):
    if channel not in CHANNEL_RULES:
        raise ValueError(f'Unsupported channel: {channel}')
    delta=(as_date(conversion_date)-as_date(anchor_date)).days
    return 0<=delta<=CHANNEL_RULES[channel]['window_days']


def matured(channel,anchor_date,as_of):
    return as_date(as_of)>=as_date(anchor_date)+timedelta(days=CHANNEL_RULES[channel]['window_days'])
