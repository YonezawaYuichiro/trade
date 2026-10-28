"""往復コストの下限と単元。呼値と単元は公式の表から渡す。ここに数値を書かない。"""
from decimal import Decimal


def round_trip_cost_floor(price: Decimal, tick: Decimal) -> Decimal:
    """往復で呼値2つ分を値段で割ったもの（規則12）。tick はその約定日に有効な呼値。"""
    if not isinstance(price, Decimal) or not isinstance(tick, Decimal):
        raise TypeError("price と tick は Decimal で渡す")
    if price <= 0 or tick <= 0:
        raise ValueError("price と tick は正")
    return 2 * tick / price


def floor_to_lot(quantity: int, lot: int) -> int:
    """単元の整数倍に切り下げる（規則13）。端株にしない。"""
    if lot <= 0 or quantity < 0:
        raise ValueError("lot は正、quantity は0以上")
    return quantity // lot * lot
