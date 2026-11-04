from decimal import Decimal, ROUND_HALF_UP


def decimal(value):
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError("A finite numeric value is required")
    return number


def money(value):
    return decimal(value).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def dollars(cents):
    return format(money(Decimal(cents) / 100), ".2f")


def fmt(value):
    return format(money(value), ".2f")
