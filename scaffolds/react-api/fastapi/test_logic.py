"""Known-answer and degenerate tests for logic.py. Run: python -m pytest -q"""
import pytest

from logic import summarize


def test_known_answer():
    # Worked by hand: 1+2+3+4+5 = 15, 15 / 5 = 3
    assert summarize([1, 2, 3, 4, 5]) == {"n": 5, "mean": 3.0, "min": 1.0, "max": 5.0}


def test_one_value():
    assert summarize([7]) == {"n": 1, "mean": 7.0, "min": 7.0, "max": 7.0}


def test_empty_is_an_error_not_a_number():
    with pytest.raises(ValueError):
        summarize([])


def test_text_is_an_error():
    with pytest.raises(ValueError):
        summarize([1, "two"])
