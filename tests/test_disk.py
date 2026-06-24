"""Disk: the closed circle stored exactly as three boundary points.

Covers the constructors, the exact measures (center / squaredRadius / bbox /
pointInside) versus the inherently-approximate floating ones (radius / area),
order-independent equality and hashing, the predicate matrix, squared distance,
and exact point intersection."""

from fractions import Fraction

import math

import pytest

import pypgl
from pypgl import Disk, Point, Rectangle, Triangle


# --- construction, exactness, accessors ----------------------------------

def test_disk_importable_and_in_all():
    assert hasattr(pypgl, "Disk")
    assert "Disk" in pypgl.__all__


def test_center_radius_constructor_is_exact():
    d = Disk(0, 0, 5)
    assert d.center() == Point(0, 0)
    assert d.squaredRadius() == 25
    assert isinstance(d.squaredRadius(), Fraction)
    assert d.bbox() == Rectangle(-5, -5, 5, 5)


def test_coordinate_constructor_accepts_fraction_and_strings():
    d = Disk(Fraction(1, 2), 0, Fraction(3, 2))
    assert d.center() == Point(Fraction(1, 2), 0)
    assert d.squaredRadius() == Fraction(9, 4)
    assert Disk("0", "0", "1/2").squaredRadius() == Fraction(1, 4)


def test_float_coordinates_are_rejected():
    with pytest.raises(TypeError):
        Disk(0.0, 0.0, 5.0)


def test_three_point_constructor_is_order_independent():
    d1 = Disk(Point(1, 0), Point(-1, 0), Point(0, 1))
    d2 = Disk(Point(0, 1), Point(1, 0), Point(-1, 0))
    assert d1 == d2
    assert hash(d1) == hash(d2)
    assert len({d1, d2}) == 1


def test_boundary_point_accessors_and_indexing():
    d = Disk(0, 0, 5)
    assert len(d) == 3
    assert (d.a(), d.b(), d.c()) == (d[0], d[1], d[2])
    assert list(d) == [d.a(), d.b(), d.c()]
    assert d[-1] == d[2]                 # cyclic indexing
    assert d.index(d.a()) == 0
    assert d.index(Point(100, 100)) is None


def test_degenerate_disk_from_collinear_points():
    assert Disk(Point(0, 0), Point(1, 0), Point(2, 0)).isDegenerate()
    assert not Disk(0, 0, 5).isDegenerate()


# --- approximate measures have no exact form -----------------------------

def test_radius_is_exact_when_built_from_center_and_radius():
    # Disks built from a center and radius keep an exact rational radius.
    for d in (Disk(0, 0, 5), Disk(Point(2, 3), 5), Disk(0, 0, Fraction(1, 2))):
        assert isinstance(d.radius(), Fraction)
    assert Disk(0, 0, 5).radius() == 5
    assert Disk(0, 0, Fraction(1, 2)).radius() == Fraction(1, 2)
    # Even three-point disks that coincide with the axis-aligned witness are exact.
    assert Disk(Point(-5, 0), Point(5, 0), Point(0, 5)).radius() == 5


def test_radius_is_float_when_irrational():
    # An arbitrary three-point disk has a square-root radius with no exact form.
    d = Disk(Point(0, 0), Point(4, 0), Point(0, 6))
    assert d.squaredRadius() == 13
    assert isinstance(d.radius(), float)
    assert d.radius() == pytest.approx(math.sqrt(13))


def test_area_is_always_float():
    d = Disk(0, 0, 5)
    assert isinstance(d.area(), float)
    assert d.area() == pytest.approx(math.pi * 25)


def test_diameter_is_an_exact_segment_for_center_radius_disks():
    d = Disk(0, 0, 10)
    diam = d.diameter()
    assert isinstance(diam, pypgl.Segment)
    assert diam == pypgl.Segment(Point(-10, 0), Point(10, 0))
    # A diameter is a chord: contained in the closed disk but not its interior.
    assert d.contains(diam)
    assert not d.interiorContains(diam)


def test_diameter_raises_when_radius_is_irrational():
    d = Disk(Point(0, 0), Point(4, 0), Point(0, 6))   # squaredRadius 13
    with pytest.raises(ValueError):
        d.diameter()


# --- predicates ----------------------------------------------------------

def test_point_containment_distinguishes_boundary_and_interior():
    d = Disk(0, 0, 5)
    assert Point(0, 0) in d                       # __contains__ -> contains
    assert d.contains(Point(5, 0))                # on the circle, boundary-inclusive
    assert d.boundaryContains(Point(5, 0))
    assert not d.interiorContains(Point(5, 0))
    assert d.interiorContains(Point(0, 0))
    assert Point(6, 0) not in d


def test_predicate_matrix_against_other_shapes():
    d = Disk(0, 0, 5)
    assert d.intersects(Rectangle(0, 0, 1, 1))
    assert d.contains(Triangle(Point(0, 0), Point(1, 0), Point(0, 1)))
    assert not d.intersects(Rectangle(100, 100, 101, 101))


def test_disk_versus_disk_predicates():
    assert Disk(0, 0, 5).contains(Disk(0, 0, 2))
    assert not Disk(0, 0, 5).interiorContains(Disk(0, 0, 5))
    assert Disk(0, 0, 1).intersects(Disk(2, 0, 1))      # touching counts
    assert not Disk(0, 0, 1).intersects(Disk(5, 0, 1))


# --- squared distance and intersection -----------------------------------

def test_squared_distance_is_float_and_zero_when_intersecting():
    assert Disk(0, 0, 1).squaredDistance(Disk(5, 0, 1)) == pytest.approx(9.0)
    assert Disk(0, 0, 5).squaredDistance(Point(0, 0)) == pytest.approx(0.0)


def test_intersection_with_point_is_exact_optional():
    d = Disk(0, 0, 5)
    assert d.intersection(Point(3, 4)) == Point(3, 4)   # on the circle
    assert d.intersection(Point(100, 100)) is None


# --- transforms ----------------------------------------------------------

def test_translation_and_rotation_return_new_disks():
    d = Disk(0, 0, 5)
    moved = d + Point(10, 10)
    assert moved.center() == Point(10, 10)
    assert moved.squaredRadius() == 25
    assert (d * 2).squaredRadius() == 100
    assert d.rotated90().squaredRadius() == 25          # radius preserved
