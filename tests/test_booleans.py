"""The regularized boolean set operations: difference, unionWith,
symmetricDifference, and the region-valued intersection.

All four answer in a *list* of PolygonWithHoles, and all four return the
regularized result -- the closure of the operation applied to the operands'
interiors. That is what these tests mostly pin down, since it is where the
answers differ from naive set arithmetic: lower-dimensional leftovers are
dropped, material with no area never joins anything, and idempotence therefore
holds only up to regularization.
"""

from fractions import Fraction

import pytest

from pypgl import (
    Convex,
    Point,
    Polygon,
    PolygonWithHoles,
    Rectangle,
    Triangle,
)


def _square(side=10):
    return Polygon([Point(0, 0), Point(side, 0), Point(side, side), Point(0, side)])


def _total_area(pieces):
    return sum((piece.area() for piece in pieces), Fraction(0))


# --- difference -------------------------------------------------------------

def test_removing_the_middle_leaves_a_hole():
    # This is the family PolygonWithHoles exists for: no other shape can say
    # that the result has a hole in it.
    pieces = _square().difference(Rectangle(Point(3, 3), Point(7, 7)))
    assert len(pieces) == 1
    assert pieces[0].holeCount() == 1
    assert pieces[0].outer() == _square()
    assert pieces[0].hole(0) == Polygon(
        [Point(3, 3), Point(7, 3), Point(7, 7), Point(3, 7)]
    )
    assert pieces[0].area() == 100 - 16


def test_removing_a_bar_can_split_a_shape_in_two():
    pieces = _square().difference(Rectangle(Point(-1, 4), Point(11, 6)))
    assert len(pieces) == 2
    assert _total_area(pieces) == 100 - 20


def test_difference_of_disjoint_shapes_is_the_receiver():
    pieces = _square().difference(Rectangle(Point(50, 50), Point(60, 60)))
    assert len(pieces) == 1
    assert pieces[0].area() == 100


def test_difference_by_a_covering_shape_is_empty():
    assert _square().difference(Rectangle(Point(-1, -1), Point(11, 11))) == []


def test_difference_is_not_symmetric():
    big = _square()
    small = Polygon([Point(3, 3), Point(7, 3), Point(7, 7), Point(3, 7)])
    assert _total_area(big.difference(small)) == 84
    # The other way round removes everything.
    assert small.difference(big) == []


# --- union ------------------------------------------------------------------

def test_union_of_overlapping_shapes_merges_them():
    pieces = _square().unionWith(Rectangle(Point(5, 5), Point(15, 15)))
    assert len(pieces) == 1
    assert pieces[0].area() == 100 + 100 - 25


def test_union_can_create_a_hole_from_nothing():
    # A U-shape united with the bar that caps it encloses a hole neither
    # operand has.
    u = Polygon(
        [
            Point(0, 0), Point(6, 0), Point(6, 6), Point(4, 6),
            Point(4, 2), Point(2, 2), Point(2, 6), Point(0, 6),
        ]
    )
    cap = Rectangle(Point(0, 6), Point(6, 8))
    pieces = u.unionWith(cap)
    assert len(pieces) == 1
    assert pieces[0].holeCount() == 1


def test_union_never_joins_across_a_single_point():
    # Regularization drops material with no area, so two shapes meeting at one
    # point come back as two pieces -- a region may not have a self-touching
    # outer ring.
    a = Polygon([Point(0, 0), Point(2, 0), Point(2, 2), Point(0, 2)])
    b = Rectangle(Point(2, 2), Point(4, 4))
    assert len(a.unionWith(b)) == 2


def test_union_is_idempotent_only_up_to_regularization():
    r = _square().asPolygonWithHoles()
    assert r.unionWith(r) == r.regularized() == [r]


# --- symmetric difference ---------------------------------------------------

def test_symmetric_difference_keeps_what_exactly_one_covers():
    a = Rectangle(Point(0, 0), Point(10, 10))
    b = Rectangle(Point(5, 5), Point(15, 15))
    pieces = a.asPolygonWithHoles().symmetricDifference(b)
    assert _total_area(pieces) == (100 - 25) + (100 - 25)


def test_symmetric_difference_of_a_shape_with_itself_is_empty():
    r = _square().asPolygonWithHoles()
    assert r.symmetricDifference(r) == []


# --- intersection -----------------------------------------------------------

def test_region_intersection_keeps_holes():
    # The reason the region-valued intersection exists: a region's hole
    # interiors are components of their own, so the usual "a curve in A n B
    # bounds a disk in each operand" argument does not apply to it.
    hole = Polygon([Point(4, 4), Point(8, 4), Point(8, 8), Point(4, 8)])
    annulus = PolygonWithHoles(_square(), [hole])
    pieces = annulus.intersection(Rectangle(Point(-5, -5), Point(20, 20)))
    assert pieces == [annulus]


def test_polygon_intersection_with_a_region_returns_regions():
    # Which of the two `intersection` methods answers is decided by the
    # operands, not the receiver: a region operand pulls in the region-valued
    # one whichever side it is written on.
    hole = Polygon([Point(4, 4), Point(8, 4), Point(8, 8), Point(4, 8)])
    annulus = PolygonWithHoles(_square(), [hole])
    pieces = _square().intersection(annulus)
    assert isinstance(pieces, list)
    assert pieces == [annulus]


def test_polygon_intersection_without_a_region_stays_component_valued():
    # No region operand, so this is the general intersection, which returns
    # polygon components rather than regions.
    result = _square().intersection(Rectangle(Point(5, 5), Point(15, 15)))
    assert not isinstance(result, list) or not any(
        isinstance(piece, PolygonWithHoles) for piece in result
    )


def test_intersection_of_disjoint_regions_is_empty():
    a = _square().asPolygonWithHoles()
    b = Rectangle(Point(50, 50), Point(60, 60)).asPolygonWithHoles()
    assert a.intersection(b) == []


# --- the symmetric three forward, so either spelling works ------------------

@pytest.mark.parametrize(
    "other",
    [
        Convex([Point(5, 5), Point(15, 5), Point(15, 15), Point(5, 15)]),
        Triangle(Point(5, 5), Point(15, 5), Point(5, 15)),
        Rectangle(Point(5, 5), Point(15, 15)),
    ],
)
@pytest.mark.parametrize("op", ["unionWith", "symmetricDifference"])
def test_symmetric_operations_forward_either_way(other, op):
    polygon = _square()
    assert getattr(polygon, op)(other) == getattr(other, op)(polygon)


def test_intersection_forwards_from_an_area_shape_to_a_region():
    region = _square().asPolygonWithHoles()
    rectangle = Rectangle(Point(5, 5), Point(15, 15))
    assert rectangle.intersection(region) == region.intersection(rectangle)


@pytest.mark.parametrize(
    "receiver",
    [
        Rectangle(Point(0, 0), Point(1, 1)),
        Triangle(Point(0, 0), Point(1, 0), Point(0, 1)),
        Convex([Point(0, 0), Point(1, 0), Point(0, 1)]),
    ],
)
def test_difference_does_not_forward(receiver):
    # difference is not symmetric, so unlike the other three it stays on the two
    # receivers that can represent the answer -- Polygon and PolygonWithHoles.
    # The area shapes have no `difference` at all, not merely a narrower one.
    assert not hasattr(receiver, "difference")


# --- results are flat, not nested -------------------------------------------

def test_an_island_inside_a_hole_is_its_own_piece():
    # pgl has no PolygonSet, so the pieces are never nested: an island stranded
    # inside a hole of the result comes back separately.
    frame = _square(20).difference(Rectangle(Point(5, 5), Point(15, 15)))
    assert len(frame) == 1
    island = Rectangle(Point(8, 8), Point(12, 12))
    pieces = frame[0].unionWith(island)
    assert len(pieces) == 2
    assert _total_area(pieces) == (400 - 100) + 16


# --- exactness --------------------------------------------------------------

def test_rectilinear_input_gives_exact_integer_output():
    # The arrangement is always built over exact rationals, so an integral
    # result is exact whenever the crossings are.
    pieces = _square().difference(Rectangle(Point(3, 3), Point(7, 7)))
    for vertex in pieces[0].vertices():
        assert vertex.x().denominator == 1
        assert vertex.y().denominator == 1


def test_diagonal_crossings_stay_exact_fractions():
    # The cut's edge (0,0)--(5,3) leaves the square through x == 4 at y == 12/5,
    # so the result has a vertex off the integer lattice. The arrangement is
    # built over exact rationals, so that vertex is exact rather than rounded.
    square = Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])
    pieces = square.difference(Triangle(Point(0, 0), Point(5, 3), Point(0, 3)))
    corners = [v for piece in pieces for v in piece.vertices()]
    assert Point(4, Fraction(12, 5)) in corners
    assert _total_area(pieces) == Fraction(24, 5) + 4
