import math_utils
import pytest

def test_add():
    assert math_utils.add(2, 2) == 4

def test_divide():
    assert math_utils.divide(10, 2) == 5.0

def test_divide_by_zero():
    with pytest.raises(ValueError):
        math_utils.divide(10, 0)
