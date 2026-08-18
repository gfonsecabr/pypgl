"""samePointSet: geometric equality, bound for all seventeen shapes against all
seventeen.

It answers what ``a.contains(b) and b.contains(a)`` answers, but directly and
usually faster. What makes it worth having separately from ``==`` is that ``==``
compares *representations* of one type: it cannot compare across types at all,
and even within one it can disagree -- a polygon carrying a redundant vertex in
the middle of an edge covers exactly the same points as one without it.
"""

import pytest

from pypgl import (
    Convex,
    Disk,
    Halfplane,
    HalfplaneIntersection,
    Line,
    MonotoneChain,
    OrientedSegment,
    Point,
    Polygon,
    PolygonSet,
    PolygonWithHoles,
    Polyline,
    Ray,
    Rectangle,
    Segment,
    Triangle,
)


def _square_shapes():
    """The same unit-square point set, said seven different ways."""
    corners = [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]
    return [
        Rectangle(Point(0, 0), Point(4, 4)),
        Convex(corners),
        Polygon(corners),
        Polygon(corners).asPolygonWithHoles(),
        Polygon(corners).asPolygonSet(),
        Rectangle(Point(0, 0), Point(4, 4)).asHalfplaneIntersection(),
        # A redundant vertex in the middle of an edge: the same point set, and
        # exactly the case `==` gets wrong.
        Polygon([Point(0, 0), Point(2, 0), Point(4, 0), Point(4, 4), Point(0, 4)]),
    ]


@pytest.mark.parametrize("a", _square_shapes())
@pytest.mark.parametrize("b", _square_shapes())
def test_the_same_point_set_across_every_representation(a, b):
    assert a.samePointSet(b)


def test_it_is_not_the_same_question_as_equality():
    plain = Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])
    redundant = Polygon(
        [Point(0, 0), Point(2, 0), Point(4, 0), Point(4, 4), Point(0, 4)]
    )
    assert plain.samePointSet(redundant)
    assert plain != redundant                       # different representations


def test_it_agrees_with_mutual_containment():
    a = Rectangle(Point(0, 0), Point(4, 4))
    for b in _square_shapes() + [Rectangle(Point(0, 0), Point(4, 5)), Point(1, 1)]:
        assert a.samePointSet(b) == (a.contains(b) and b.contains(a))


@pytest.mark.parametrize(
    "a, b",
    [
        (Point(1, 2), Point(1, 2)),
        (Segment(0, 0, 4, 0), OrientedSegment(Point(4, 0), Point(0, 0))),
        (Segment(0, 0, 4, 0), Polyline([Point(0, 0), Point(2, 0), Point(4, 0)])),
        (Segment(0, 0, 4, 0), MonotoneChain([Point(0, 0), Point(4, 0)])),
        (Line(Point(0, 0), Point(1, 0)), Line(Point(5, 0), Point(9, 0))),
        (Ray(Point(0, 0), Point(1, 0)), Ray(Point(0, 0), Point(7, 0))),
        (
            Halfplane(Point(0, 0), Point(1, 0)),
            Halfplane(Point(0, 0), Point(1, 0)).asHalfplaneIntersection(),
        ),
        (Triangle(Point(0, 0), Point(4, 0), Point(0, 4)),
         Convex([Point(0, 0), Point(4, 0), Point(0, 4)])),
        (Disk(Point(0, 0), 2), Disk(Point(0, 0), 2)),
    ],
)
def test_pairs_that_cover_the_same_points_say_so(a, b):
    assert a.samePointSet(b) and b.samePointSet(a)


@pytest.mark.parametrize(
    "a, b",
    [
        (Point(1, 2), Point(2, 1)),
        (Segment(0, 0, 4, 0), Segment(0, 0, 5, 0)),
        (Rectangle(Point(0, 0), Point(4, 4)), Triangle(Point(0, 0), Point(4, 0), Point(0, 4))),
        (Line(Point(0, 0), Point(1, 0)), Ray(Point(0, 0), Point(1, 0))),
        (Disk(Point(0, 0), 2), Disk(Point(0, 0), 3)),
    ],
)
def test_pairs_that_do_not_say_so(a, b):
    assert not a.samePointSet(b) and not b.samePointSet(a)


def test_a_set_of_one_component_is_that_component():
    region = Rectangle(Point(0, 0), Point(4, 4)).asPolygonWithHoles()
    assert PolygonSet(region).samePointSet(region)


def test_a_set_of_several_components_is_not_any_one_of_them():
    square = Polygon([Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)])
    split = square.difference(Rectangle(Point(-1, 4), Point(11, 6)))
    assert split.componentCount() == 2
    assert not split.samePointSet(split.component(0))
    assert split.samePointSet(PolygonSet(list(split.components())))


def test_the_empty_shapes_of_different_types_cover_the_same_nothing():
    assert Convex([]).samePointSet(Polygon([]))
    assert PolygonSet().samePointSet(PolygonWithHoles())
