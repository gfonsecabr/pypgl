"""A distance to an empty shape is refused, not undefined.

The nearest-point distance is an infimum over an operand's points, and the empty
set has none, so a non-empty operand is a precondition of every distance method.
pgl states it as an assert, which the release build compiles out; before pypgl
checked it, an empty `Convex`, `Polygon`, chain or `HalfplaneIntersection` took
the interpreter down (it seeds its minimum from a first vertex or edge it does
not have), the other empty shapes answered 0, and `closestPoints` /
`closestSegments` invented witness points such as (0, 0) on neither shape.

The Hausdorff family's copy of this rule is pinned in test_hausdorff.py.
"""

import pytest

from pypgl import (
    Convex,
    Disk,
    Halfplane,
    HalfplaneIntersection,
    Line,
    MonotoneChain,
    OrientedLine,
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

METHODS = ["squaredDistance", "distanceL1", "distanceLInf", "closestPoints", "closestSegments"]


def empty_shapes():
    return {
        "Rectangle": Rectangle(),
        "Convex": Convex(),
        "MonotoneChain": MonotoneChain(),
        "Polyline": Polyline(),
        "Polygon": Polygon(),
        "PolygonWithHoles": PolygonWithHoles(),
        "PolygonSet": PolygonSet(),
        "HalfplaneIntersection": HalfplaneIntersection(
            [Halfplane(Point(0, 0), Point(1, 0)), Halfplane(Point(0, -1), Point(-1, -1))]
        ),
    }


def nonempty_shapes():
    a, b, c = Point(5, 5), Point(6, 7), Point(9, 5)
    return [
        a,
        Segment(a, b),
        OrientedSegment(a, b),
        Line(a, b),
        OrientedLine(a, b),
        Ray(a, b),
        Halfplane(a, b),
        Triangle(a, b, c),
        Rectangle(a, b),
        Convex([a, b, c]),
        MonotoneChain([a, b]),
        Polyline([a, b]),
        Polygon([a, b, c]),
        Polygon([a, b, c]).asPolygonWithHoles(),
        Polygon([a, b, c]).asPolygonSet(),
        Convex([a, b, c]).asHalfplaneIntersection(),
        Disk(a, 1),
    ]


def call(receiver, method, argument):
    """The call's outcome: "refused", "unbound", or the answer it gave."""
    if not hasattr(receiver, method):
        return "unbound"
    try:
        result = getattr(receiver, method)(argument)
    except ValueError as exc:
        assert "empty" in str(exc)
        return "refused"
    except TypeError:
        return "unbound"
    return result


@pytest.mark.parametrize("name", sorted(empty_shapes()))
@pytest.mark.parametrize("method", METHODS)
def test_an_empty_operand_is_refused_on_either_side(name, method):
    empty = empty_shapes()[name]
    assert empty.empty()
    refused = 0
    others = nonempty_shapes() + list(empty_shapes().values())
    for other in others:
        for receiver, argument in ((empty, other), (other, empty)):
            outcome = call(receiver, method, argument)
            assert outcome in ("refused", "unbound"), (
                f"{receiver!r}.{method}({argument!r}) answered {outcome!r}"
            )
            refused += outcome == "refused"
    # Every empty kind is in some grid of every family -- bar an unbounded-capable
    # HalfplaneIntersection, which has no closestSegments at all -- so the loop
    # has to have reached the guard, or a TypeError everywhere would pass.
    if (name, method) != ("HalfplaneIntersection", "closestSegments"):
        assert refused > 0


def test_a_degenerate_shape_is_still_measured():
    # empty() is about the point set, not dimension: a zero-area rectangle and a
    # one-vertex Convex hold a point each and are measured normally.
    flat = Rectangle(Point(2, 3), Point(2, 3))
    single = Convex([Point(2, 3)])
    assert flat.squaredDistance(Point(2, 5)) == 4
    assert single.distanceL1(Point(4, 4)) == 3
    assert single.closestPoints(Point(2, 5)) == [Point(2, 3), Point(2, 5)]
