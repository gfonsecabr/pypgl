"""Flat coordinate lists as constructor arguments.

The four variable-size shapes that pgl gives an `initializer_list<Number>`
constructor -- Convex, Polygon, MonotoneChain and Polyline -- take the same flat
list here, read in (x, y) pairs, so a literal shape needs no Point per vertex:

    Polygon([0, 0, 4, 0, 4, 4])   ==   Polygon([Point(0, 0), Point(4, 0), Point(4, 4)])

The coordinates go through the same caster as everywhere else, so int, Fraction
and "a/b" strings are accepted and float is rejected.
"""

from fractions import Fraction

import pytest

from pypgl import Convex, MonotoneChain, Point, Polygon, Polyline


COORDS = [0, 0, 8, 0, 8, 6, 0, 6]
POINTS = [Point(0, 0), Point(8, 0), Point(8, 6), Point(0, 6)]

SHAPES = [Convex, Polygon, MonotoneChain, Polyline]


@pytest.mark.parametrize("cls", SHAPES)
def test_coords_build_the_same_shape_as_points(cls):
    assert cls(COORDS) == cls(POINTS)


@pytest.mark.parametrize("cls", SHAPES)
def test_coords_are_read_in_xy_pairs(cls):
    assert list(cls(COORDS).vertices()) == list(cls(POINTS).vertices())


@pytest.mark.parametrize("cls", SHAPES)
def test_empty_coordinate_list_builds_the_empty_shape(cls):
    assert cls([]) == cls()


@pytest.mark.parametrize("cls", SHAPES)
def test_odd_coordinate_count_raises(cls):
    with pytest.raises(ValueError):
        cls([0, 0, 4])


@pytest.mark.parametrize("cls", SHAPES)
def test_float_coordinates_are_rejected(cls):
    with pytest.raises(TypeError):
        cls([0.5, 0, 4, 0, 4, 4])


@pytest.mark.parametrize("cls", SHAPES)
def test_coords_accept_every_exact_spelling(cls):
    mixed = cls([0, 0, Fraction(1, 2), "3/4", 4, 4])
    named = cls([Point(0, 0), Point(Fraction(1, 2), Fraction(3, 4)), Point(4, 4)])
    assert mixed == named


@pytest.mark.parametrize("cls", SHAPES)
def test_coords_is_a_keyword(cls):
    assert cls(coords=COORDS) == cls(POINTS)


@pytest.mark.parametrize("cls", SHAPES)
def test_coordinates_stay_exact(cls):
    big = 10**40
    shape = cls([0, 0, big, 1, "1/3", 2])
    assert Point(big, 1) in list(shape.vertices())
    assert Point(Fraction(1, 3), 2) in list(shape.vertices())


# --- `trusted`, on the three shapes whose C++ constructor has it -------------

@pytest.mark.parametrize("cls", [Convex, Polygon, MonotoneChain])
def test_trusted_stores_the_coordinates_verbatim(cls):
    # Canonical order for all three is CCW from the lexicographically smallest
    # vertex, which this list is not in: untrusted, it gets reordered.
    rotated = [8, 6, 0, 6, 0, 0, 8, 0]
    assert list(cls(rotated, trusted=True).vertices()) == [
        Point(8, 6), Point(0, 6), Point(0, 0), Point(8, 0)
    ]
    assert list(cls(rotated).vertices()) != list(cls(rotated, trusted=True).vertices())


def test_convex_points_constructor_also_takes_trusted():
    hull = [Point(0, 0), Point(8, 0), Point(8, 6), Point(0, 6)]
    assert Convex(hull, trusted=True) == Convex(hull)
    # Trusted skips the hull scan, so an interior point survives -- which is the
    # caller's promise to keep, exactly as in C++.
    with_interior = hull + [Point(4, 3)]
    assert len(Convex(with_interior, trusted=True)) == 5
    assert len(Convex(with_interior)) == 4


def test_polyline_has_no_trusted_parameter():
    # pgl's Polyline stores its vertices verbatim already, so there is nothing
    # to trust: its coordinate constructor takes the list alone.
    with pytest.raises(TypeError):
        Polyline([0, 0, 4, 4], trusted=True)


# --- the collapse a flat list makes possible ---------------------------------

def test_convex_hull_of_a_coordinate_list():
    hull = Convex([0, 0, 8, 0, 4, 3, 4, 6])
    assert Point(4, 3) not in list(hull.vertices())   # interior to the hull
    assert hull.area() == Convex([0, 0, 8, 0, 4, 6]).area()
