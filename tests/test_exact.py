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


# --- the caster fast paths ---------------------------------------------------
#
# Both directions take a shortcut for the common coordinate: an int magnitude
# below 2**63 crosses as one machine integer instead of a decimal string, a
# Python int is read as a rational over denominator 1 without touching its
# `numerator`/`denominator` attributes, and terms already known to be coprime
# skip a normalizing gcd on each side. These pin the boundaries where the
# shortcuts hand over to the general path.


@pytest.mark.parametrize(
    "value",
    [
        0,
        1,
        -1,
        2**62,
        -(2**62),
        2**63 - 1,  # the largest magnitude the machine-integer path takes
        -(2**63 - 1),
        2**63,  # the first that falls through to the decimal-string path
        -(2**63),
        2**63 + 1,
        -(2**63 + 1),
        2**64,
        10**25,
        -(10**25),
    ],
)
def test_integer_coordinates_round_trip_across_the_int64_boundary(value):
    coordinate = pypgl.Point(value, 0).x()
    assert coordinate == Fraction(value)
    assert isinstance(coordinate, Fraction)
    # An integer coordinate is a Fraction over 1, not merely equal to one.
    assert coordinate.denominator == 1
    assert coordinate.numerator == value


@pytest.mark.parametrize(
    "value",
    [
        Fraction(1, 3),
        Fraction(-1, 3),
        Fraction(7, 2),
        Fraction(-(2**70), 3),
        Fraction(3, 2**70),
        Fraction(2**63, 2**63 + 1),
        Fraction(0, 5),
    ],
)
def test_fractional_coordinates_round_trip_in_lowest_terms(value):
    coordinate = pypgl.Point(value, 0).x()
    assert coordinate == value
    assert (coordinate.numerator, coordinate.denominator) == (
        value.numerator,
        value.denominator,
    )


def test_a_coordinate_hashes_and_compares_as_the_number_it_is():
    # The int, the Fraction and the coordinate are one value, so a set holds one.
    assert len({pypgl.Point(2, 3).x(), Fraction(2), 2}) == 1


def test_an_object_with_unreduced_terms_is_still_reduced():
    """Only an int or a Fraction is trusted to be in lowest terms already."""

    class Sloppy:
        numerator = 6
        denominator = 4

    coordinate = pypgl.Point(Sloppy(), 0).x()
    assert coordinate == Fraction(3, 2)
    assert (coordinate.numerator, coordinate.denominator) == (3, 2)
