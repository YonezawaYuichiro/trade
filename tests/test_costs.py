from decimal import Decimal

import pytest

from cleanroom.costs import floor_to_lot, round_trip_cost_floor


def test_cost_floor_is_two_ticks_over_price():
    assert round_trip_cost_floor(Decimal("1000"), Decimal("1")) == Decimal("0.002")
    assert round_trip_cost_floor(Decimal("2500"), Decimal("5")) == Decimal("0.004")


def test_cost_floor_rejects_float_and_nonpositive():
    with pytest.raises(TypeError):
        round_trip_cost_floor(1000.0, Decimal("1"))
    with pytest.raises(ValueError):
        round_trip_cost_floor(Decimal("1000"), Decimal("0"))
    with pytest.raises(ValueError):
        round_trip_cost_floor(Decimal("0"), Decimal("1"))


def test_quantity_is_whole_lots():
    assert floor_to_lot(250, 100) == 200
    assert floor_to_lot(99, 100) == 0
    with pytest.raises(ValueError):
        floor_to_lot(100, 0)
