"""PolygonSet: a set of PolygonWithHoles components with pairwise disjoint
interiors, whose point set is their union.

This is the shape that closes the regularized boolean operations. Before it
existed they answered with a bare list, which could not be fed back in, compared,
hashed, drawn or measured; now every one of them answers with one of these. It
is also the only pypgl shape whose point set need not be connected, which is
what most of the tests below are really about.
"""

from fractions import Fraction

import pytest

from pypgl import (
    Canvas,
    Point,
    Polygon,
    PolygonSet,
    PolygonWithHoles,
    Rectangle,
    ShapeTree,
    Triangle,
)


def _square(side=10):
    return Polygon([Point(0, 0), Point(side, 0), Point(side, side), Point(0, side)])


def _split():
    """A square cut in two by a horizontal bar: two components, disjoint."""
    return _square().difference(Rectangle(Point(-1, 4), Point(11, 6)))


# --- construction -----------------------------------------------------------

def test_the_default_set_is_empty():
    empty = PolygonSet()
    assert empty.empty()
    assert empty.componentCount() == 0
    assert empty.area() == 0
    # An empty set is connected by convention, having nothing to come apart.
    assert empty.isConnected()


def test_a_single_component_covers_exactly_that_region():
    region = _square().asPolygonWithHoles()
    one = PolygonSet(region)
    assert one.componentCount() == 1
    assert one.area() == 100
    assert one.samePointSet(region)


def test_components_are_stored_in_canonical_order():
    a = Rectangle(Point(0, 0), Point(1, 1)).asPolygonWithHoles()
    b = Rectangle(Point(5, 5), Point(6, 6)).asPolygonWithHoles()
    assert PolygonSet([a, b]) == PolygonSet([b, a])


def test_zero_area_components_and_duplicates_are_dropped():
    region = _square().asPolygonWithHoles()
    flat = PolygonWithHoles(Polygon([Point(0, 0), Point(4, 0), Point(2, 0)]))
    assert PolygonSet([region, region, flat]).componentCount() == 1


# --- what a set is that no other shape is -----------------------------------

def test_a_set_need_not_be_connected():
    pieces = _split()
    assert pieces.componentCount() == 2
    assert not pieces.isConnected()
    # The components stay apart, which is the cheap exact case for every
    # predicate: they fold componentwise.
    assert not pieces.isPinched()


def test_components_are_not_nested():
    # An island stranded inside a hole of the answer is stored beside the region
    # holding it, never within it.
    frame = _square(20).difference(Rectangle(Point(5, 5), Point(15, 15)))
    pieces = frame.regularizedUnion(Rectangle(Point(8, 8), Point(12, 12)))
    assert pieces.componentCount() == 2
    assert pieces.component(0).holeCount() + pieces.component(1).holeCount() == 1


def test_touching_components_are_pinched_but_still_connected():
    a = Rectangle(Point(0, 0), Point(2, 2)).asPolygonWithHoles()
    b = Rectangle(Point(2, 2), Point(4, 4)).asPolygonWithHoles()
    pieces = PolygonSet([a, b])
    assert pieces.isPinched()
    assert pieces.isConnected()


# --- the algebra is closed --------------------------------------------------

@pytest.mark.parametrize(
    "operation",
    ["difference", "regularizedUnion", "symmetricDifference", "regularizedIntersection"],
)
def test_every_boolean_answers_with_a_set_that_feeds_back_in(operation):
    pieces = _split()
    other = Rectangle(Point(0, 0), Point(10, 3))
    result = getattr(pieces, operation)(other)
    assert isinstance(result, PolygonSet)
    # The point of being closed: the answer is an operand again.
    assert isinstance(getattr(result, operation)(pieces), PolygonSet)


def test_regularization_is_idempotent_in_the_type_system():
    # PolygonWithHoles.regularized() has to widen to a set; a set's stays a set.
    pieces = _split()
    assert pieces.isRegular()
    assert pieces.regularized() == pieces


# --- measures and geometry --------------------------------------------------

def test_area_is_the_sum_over_disjoint_components():
    assert _split().area() == 100 - 20


def test_the_bounding_box_spans_every_component():
    assert _split().bbox() == Rectangle(Point(0, 0), Point(10, 10))


def test_the_diameter_may_join_two_different_components():
    pieces = _split()
    assert pieces.diameter().squaredLength() == 200


def test_a_point_inside_is_inside_the_set():
    pieces = _split()
    assert pieces.pointInside() in pieces


def test_holes_are_counted_over_every_component():
    holed = _square().difference(Rectangle(Point(3, 3), Point(7, 7)))
    assert holed.holeCount() == 1
    assert holed.hasHoles()


# --- container sugar: vertices, flattened, like every other pypgl shape -----

def test_iteration_flattens_the_rings_of_every_component():
    pieces = _split()
    assert len(pieces) == pieces.vertexCount() == 8
    assert list(pieces) == pieces.vertices()
    assert pieces[0] == pieces.vertices()[0]
    # Indexing is cyclic, as on every other shape.
    assert pieces[-1] == pieces.vertices()[-1]


def test_membership_is_point_in_shape_not_component_membership():
    pieces = _split()
    assert Point(1, 1) in pieces
    assert Point(5, 5) not in pieces          # the removed bar
    assert pieces.contains(Point(1, 1))


# --- mutation ---------------------------------------------------------------

def test_components_can_be_added_and_erased():
    pieces = PolygonSet()
    region = Rectangle(Point(0, 0), Point(2, 2)).asPolygonWithHoles()
    pieces.addComponent(region)
    assert pieces.componentCount() == 1
    assert pieces.eraseComponent(region)
    assert pieces.empty()


def test_a_set_is_mutable_and_therefore_unhashable():
    with pytest.raises(TypeError):
        hash(_split())


def test_translation_moves_every_component():
    pieces = _split()
    moved = pieces + Point(3, 4)
    assert moved.bbox() == Rectangle(Point(3, 4), Point(13, 14))
    assert moved.area() == pieces.area()


# --- taking part in everything else -----------------------------------------

def test_a_set_is_a_storable_shapetree_element():
    tree = ShapeTree([_split(), Triangle(Point(50, 50), Point(51, 50), Point(50, 51))])
    assert tree.countIntersecting(Point(1, 1)) == 1


def test_a_set_draws_as_one_shape():
    assert "<svg" in Canvas().draw(_split()).toSVG()


def test_exactness_survives_the_whole_way():
    square = Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])
    pieces = square.difference(Triangle(Point(0, 0), Point(5, 3), Point(0, 3)))
    assert Point(4, Fraction(12, 5)) in pieces.vertices()
