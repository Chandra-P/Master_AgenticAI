from decimal import Decimal


def compare(target, actual, direction, compatible=True):
    if not compatible:
        return {'status':'incompatible','absolute_variance':None,'percentage_variance':None}
    if target is None or actual is None:
        return {'status':'unavailable','absolute_variance':None,'percentage_variance':None}
    target, actual=Decimal(str(target)),Decimal(str(actual))
    delta=actual-target
    return {'status':'met' if (actual>=target if direction=='higher' else actual<=target) else 'not met',
            'absolute_variance':float(delta),'percentage_variance':float(delta/target*100) if target else None}
