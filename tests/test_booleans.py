"""The regularized boolean set operations: difference, regularizedUnion,
symmetricDifference, and regularizedIntersection.

All four answer with a PolygonSet -- which is what makes them *closed*, a result
feeding straight back in -- and all four return the regularized result, the
closure of the operation applied to the operands' interiors. That is what these
tests mostly pin down, since it is where the answers differ from naive set
arithmetic: lower-dimensional leftovers are dropped, material with no area never
joins anything, and idempotence therefore holds only up to regularization.
"""

from fractions import Fraction

import pytest

from pypgl import (
    Convex,
    Point,
    Polygon,
    PolygonSet,
    PolygonWithHoles,
    Rectangle,
    Triangle,
)


def _square(side=10):
    return Polygon([Point(0, 0), Point(side, 0), Point(side, side), Point(0, side)])


def _total_area(pieces):
    return sum((piece.area() for piece in pieces.components()), Fraction(0))


# --- difference -------------------------------------------------------------

def test_removing_the_middle_leaves_a_hole():
    # This is the family PolygonWithHoles exists for: no other shape can say
    # that the result has a hole in it.
    pieces = _square().difference(Rectangle(Point(3, 3), Point(7, 7)))
    assert isinstance(pieces, PolygonSet)
    assert pieces.componentCount() == 1
    assert pieces.component(0).holeCount() == 1
    assert pieces.component(0).outer() == _square()
    assert pieces.component(0).hole(0) == Polygon(
        [Point(3, 3), Point(7, 3), Point(7, 7), Point(3, 7)]
    )
    assert pieces.area() == 100 - 16


def test_removing_a_bar_can_split_a_shape_in_two():
    pieces = _square().difference(Rectangle(Point(-1, 4), Point(11, 6)))
    assert pieces.componentCount() == 2
    assert pieces.area() == 100 - 20
    # Two components that never touch: the one shape in the library whose point
    # set need not be connected.
    assert not pieces.isConnected()


def test_difference_of_disjoint_shapes_is_the_receiver():
    pieces = _square().difference(Rectangle(Point(50, 50), Point(60, 60)))
    assert pieces.componentCount() == 1
    assert pieces.area() == 100


def test_difference_by_a_covering_shape_is_empty():
    assert _square().difference(Rectangle(Point(-1, -1), Point(11, 11))).empty()


def test_difference_is_not_symmetric():
    big = _square()
    small = Polygon([Point(3, 3), Point(7, 3), Point(7, 7), Point(3, 7)])
    assert big.difference(small).area() == 84
    # The other way round removes everything.
    assert small.difference(big).empty()


# --- union ------------------------------------------------------------------

def test_union_of_overlapping_shapes_merges_them():
    pieces = _square().regularizedUnion(Rectangle(Point(5, 5), Point(15, 15)))
    assert pieces.componentCount() == 1
    assert pieces.area() == 100 + 100 - 25


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
    pieces = u.regularizedUnion(cap)
    assert pieces.componentCount() == 1
    assert pieces.component(0).holeCount() == 1


def test_union_never_joins_across_a_single_point():
    # Regularization drops material with no area, so two shapes meeting at one
    # point come back as two pieces -- a region may not have a self-touching
    # outer ring.
    a = Polygon([Point(0, 0), Point(2, 0), Point(2, 2), Point(0, 2)])
    b = Rectangle(Point(2, 2), Point(4, 4))
    assert a.regularizedUnion(b).componentCount() == 2


def test_union_is_idempotent_only_up_to_regularization():
    r = _square().asPolygonWithHoles()
    assert r.regularizedUnion(r) == r.regularized() == PolygonSet(r)


# --- symmetric difference ---------------------------------------------------

def test_symmetric_difference_keeps_what_exactly_one_covers():
    a = Rectangle(Point(0, 0), Point(10, 10))
    b = Rectangle(Point(5, 5), Point(15, 15))
    pieces = a.asPolygonWithHoles().symmetricDifference(b)
    assert pieces.area() == (100 - 25) + (100 - 25)


def test_symmetric_difference_of_a_shape_with_itself_is_empty():
    r = _square().asPolygonWithHoles()
    assert r.symmetricDifference(r).empty()


# --- regularized intersection -----------------------------------------------

def test_region_intersection_keeps_holes():
    # The reason the regularized intersection needs a region or a set on one
    # side: a region's hole interiors are components of their own, so the usual
    # "a curve in A n B bounds a disk in each operand" argument does not apply.
    hole = Polygon([Point(4, 4), Point(8, 4), Point(8, 8), Point(4, 8)])
    annulus = PolygonWithHoles(_square(), [hole])
    pieces = annulus.regularizedIntersection(Rectangle(Point(-5, -5), Point(20, 20)))
    assert pieces == PolygonSet(annulus)


def test_the_regularized_intersection_forwards_either_way():
    # Which operand it is written on does not matter, only that one of them can
    # hold the answer.
    hole = Polygon([Point(4, 4), Point(8, 4), Point(8, 8), Point(4, 8)])
    annulus = PolygonWithHoles(_square(), [hole])
    assert _square().regularizedIntersection(annulus) == annulus.regularizedIntersection(
        _square()
    )


def test_a_pair_of_convex_shapes_has_no_regularized_intersection():
    # The one gap in the four grids: neither operand can hold an answer with a
    # hole, so the operation is not bound for the pair at all. The literal
    # `intersection` is defined for it as it stands, and asPolygonWithHoles()
    # on either operand reaches the regularized one.
    rect = Rectangle(Point(0, 0), Point(4, 4))
    tri = Triangle(Point(0, 0), Point(6, 0), Point(0, 6))
    with pytest.raises(TypeError):
        rect.regularizedIntersection(tri)
    assert rect.asPolygonWithHoles().regularizedIntersection(tri).area() == 14
    assert rect.intersection(tri) is not None


def test_the_literal_intersection_keeps_every_dimension():
    # Not the same operation: `intersection` is the point set, so it keeps the
    # lower-dimensional pieces the regularized one drops.
    result = _square().intersection(Rectangle(Point(5, 5), Point(15, 15)))
    assert not any(isinstance(piece, PolygonWithHoles) for piece in result)


def test_intersection_of_disjoint_regions_is_empty():
    a = _square().asPolygonWithHoles()
    b = Rectangle(Point(50, 50), Point(60, 60)).asPolygonWithHoles()
    assert a.regularizedIntersection(b).empty()


# --- the symmetric three forward, so either spelling works ------------------

@pytest.mark.parametrize(
    "other",
    [
        Convex([Point(5, 5), Point(15, 5), Point(15, 15), Point(5, 15)]),
        Triangle(Point(5, 5), Point(15, 5), Point(5, 15)),
        Rectangle(Point(5, 5), Point(15, 15)),
    ],
)
@pytest.mark.parametrize("op", ["regularizedUnion", "symmetricDifference"])
def test_symmetric_operations_forward_either_way(other, op):
    polygon = _square()
    assert getattr(polygon, op)(other) == getattr(other, op)(polygon)


@pytest.mark.parametrize(
    "receiver",
    [
        Rectangle(Point(0, 0), Point(4, 4)),
        Triangle(Point(0, 0), Point(4, 0), Point(0, 4)),
        Convex([Point(0, 0), Point(4, 0), Point(0, 4)]),
    ],
)
def test_every_bounded_region_type_can_be_the_receiver(receiver):
    # All six -- Triangle, Rectangle, Convex, Polygon, PolygonWithHoles,
    # PolygonSet -- take all three symmetric operations and the difference.
    # (Upstream widened this: the convex shapes used to be able to forward the
    # symmetric ones only.)
    assert receiver.difference(Rectangle(Point(1, 1), Point(2, 2))).area() == (
        receiver.area() - 1
    )


def test_a_difference_may_remove_an_unbounded_shape():
    # A \\ B stays bounded however big B is, so unlike the symmetric three, the
    # difference also accepts a Halfplane or a HalfplaneIntersection -- as its
    # argument only, never as its receiver.
    from pypgl import Halfplane

    left = _square().difference(Halfplane(Point(5, 0), Point(5, 1)))
    assert left.area() == 50


# --- results are flat, not nested -------------------------------------------

def test_an_island_inside_a_hole_is_its_own_component():
    # A PolygonSet's components are deliberately not nested: an island stranded
    # inside a hole of the result is stored beside the region holding it.
    frame = _square(20).difference(Rectangle(Point(5, 5), Point(15, 15)))
    assert frame.componentCount() == 1
    island = Rectangle(Point(8, 8), Point(12, 12))
    pieces = frame.regularizedUnion(island)
    assert pieces.componentCount() == 2
    assert pieces.area() == (400 - 100) + 16


# --- exactness --------------------------------------------------------------

def test_rectilinear_input_gives_exact_integer_output():
    # The arrangement is always built over exact rationals, so an integral
    # result is exact whenever the crossings are.
    pieces = _square().difference(Rectangle(Point(3, 3), Point(7, 7)))
    for vertex in pieces.vertices():
        assert vertex.x().denominator == 1
        assert vertex.y().denominator == 1


def test_diagonal_crossings_stay_exact_fractions():
    # The cut's edge (0,0)--(5,3) leaves the square through x == 4 at y == 12/5,
    # so the result has a vertex off the integer lattice. The arrangement is
    # built over exact rationals, so that vertex is exact rather than rounded.
    square = Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])
    pieces = square.difference(Triangle(Point(0, 0), Point(5, 3), Point(0, 3)))
    assert Point(4, Fraction(12, 5)) in pieces.vertices()
    assert pieces.area() == Fraction(24, 5) + 4
