import pytest
from nour_transfers.rules import can_transfer, days_of_cover, priority

def test_cover_is_true_division():
    assert days_of_cover(10, 4) == 2.5
    assert days_of_cover(1, 2) == 0.5
def test_cover_none_when_no_sales():
    assert days_of_cover(10, 0) is None
    assert days_of_cover(0, 0) is None
def test_cover_zero_stock_with_sales_is_zero():
    assert days_of_cover(0, 5) == 0.0
def test_cover_negative_inputs_raise():
    with pytest.raises(ValueError):
        days_of_cover(-1, 2)
    with pytest.raises(ValueError):
        days_of_cover(5, -2)

def test_priority_none_cover_is_normal():
    assert priority(True, None) == "normal"
    assert priority(False, None) == "normal"
def test_priority_chronic_under_3_is_urgent():
    assert priority(True, 0.0) == "urgent"
    assert priority(True, 2.99) == "urgent"
def test_priority_chronic_exactly_3_is_high():
    assert priority(True, 3) == "high"
    assert priority(True, 3.0) == "high"
def test_priority_non_chronic_low_cover_is_never_urgent():
    assert priority(False, 0.5) == "high"
    assert priority(False, 2.99) == "high"
    assert priority(False, 3) == "high"
def test_priority_high_boundary_at_7():
    assert priority(True, 6.99) == "high"
    assert priority(False, 6.99) == "high"
    assert priority(True, 7) == "normal"
    assert priority(False, 7) == "normal"
    assert priority(True, 100) == "normal"


def test_can_transfer_exactly_reaching_reserve_is_allowed():
    assert can_transfer(20, 5, 15) is True
def test_can_transfer_one_below_reserve_is_refused():
    assert can_transfer(20, 6, 15) is False
def test_can_transfer_zero_or_negative_quantity_refused():
    assert can_transfer(20, 0, 0) is False
    assert can_transfer(20, -1, 0) is False
def test_can_transfer_minimum_quantity_and_empty_stock():
    assert can_transfer(20, 1, 0) is True
    assert can_transfer(10, 10, 0) is True
    assert can_transfer(0, 1, 0) is False
def test_can_transfer_returns_real_bool():
    assert type(can_transfer(20, 5, 15)) is bool
    assert type(can_transfer(20, 6, 15)) is bool