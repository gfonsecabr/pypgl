"""Exactness contract: arbitrary-precision round-trips, Fraction/str in & out,
float rejected."""

from fractions import Fraction

import pytest

import pypgl


def test_bigint_roundtrip():
    big = 10**50
    p = pypgl.Point(big, -big)
    assert p.x() == Fraction(big)
    assert p.y() == Fraction(-big)
    # The coordinate comes back as an exact Fraction, never a float.
    assert isinstance(p.x(), Fraction)


def test_fraction_in_out():
    p = pypgl.Point(Fraction(3, 2), Fraction(-7, 4))
    assert p.x() == Fraction(3, 2)
    assert p.y() == Fraction(-7, 4)


def test_string_coordinates():
    p = pypgl.Point("5/2", "-3")
    assert p.x() == Fraction(5, 2)
    assert p.y() == Fraction(-3)


def test_mixed_coordinate_forms():
    p = pypgl.Point(3, "5/2")
    assert p.x() == Fraction(3)
    assert p.y() == Fraction(5, 2)


def test_exact_intersection_is_rational():
    # Two crossing segments whose intersection is not integral.
    a = pypgl.Segment(0, 0, 2, 1)
    b = pypgl.Segment(0, 1, 2, 0)
    hit = a.intersection(b)
    assert isinstance(hit, pypgl.Point)
    assert hit == pypgl.Point(1, Fraction(1, 2))


@pytest.mark.parametrize("bad", [1.5, 2.0, float("inf")])
def test_float_is_rejected(bad):
    with pytest.raises(TypeError):
        pypgl.Point(bad, 0)
