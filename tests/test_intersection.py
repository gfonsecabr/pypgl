"""Typed geometric results: optional -> None, variant -> concrete shape type."""

import pytest

import pypgl
from pypgl import Point, Segment


def test_disjoint_returns_none():
    a = pypgl.Segment(0, 0, 1, 0)
    b = pypgl.Segment(0, 1, 1, 1)
    assert a.intersection(b) is None


def test_crossing_returns_point():
    a = pypgl.Segment(0, 0, 2, 2)
    b = pypgl.Segment(0, 2, 2, 0)
    result = a.intersection(b)
    assert isinstance(result, pypgl.Point)
    assert result == pypgl.Point(1, 1)


def test_overlap_returns_segment():
    a = pypgl.Segment(0, 0, 4, 0)
    b = pypgl.Segment(1, 0, 3, 0)
    result = a.intersection(b)
    assert isinstance(result, pypgl.Segment)
    assert result == pypgl.Segment(1, 0, 3, 0)


def test_segment_point_intersection():
    s = pypgl.Segment(0, 0, 4, 4)
    on = pypgl.Point(2, 2)
    off = pypgl.Point(2, 3)
    assert s.intersection(on) == on
    assert s.intersection(off) is None


def test_value_semantics_in_containers():
    pts = {pypgl.Point(1, 1), pypgl.Point(1, 1), pypgl.Point(2, 2)}
    assert len(pts) == 2
    seg = pypgl.Segment(0, 0, 1, 1)
    assert seg in {pypgl.Segment(0, 0, 1, 1)}


# --- two-dimensional pairs --------------------------------------------------
#
# These used to be unbound: pgl only had the 0D/1D clipping, so a pair of area
# shapes had no intersection at all. Now every pair but a Disk's is defined, and
# what comes back says how connected the answer is guaranteed to be.

def test_two_convex_shapes_meet_in_one_convex_piece():
    triangle = pypgl.Triangle(Point(0, 0), Point(4, 0), Point(0, 4))
    square = pypgl.Rectangle(Point(0, 0), Point(2, 2))
    piece = triangle.intersection(square)
    assert isinstance(piece, pypgl.Convex)
    assert piece.area() == 4
    # Guaranteed connected, so it is an optional rather than a list: disjoint
    # convex shapes give None.
    assert triangle.intersection(pypgl.Rectangle(Point(9, 9), Point(10, 10))) is None


def test_a_convex_shape_meets_a_halfplane_in_a_convex_piece():
    triangle = pypgl.Triangle(Point(0, 0), Point(4, 0), Point(0, 4))
    upper = pypgl.Halfplane(Point(0, 1), Point(1, 1))
    assert isinstance(upper.intersection(triangle), pypgl.Convex)


def test_a_non_convex_pair_can_meet_in_pieces_of_every_dimension():
    # The literal point set keeps them all: an isolated contact point, a shared
    # stretch of boundary as a Polyline, and the area they both cover.
    bar = pypgl.Polygon([Point(0, 0), Point(12, 0), Point(12, 2), Point(0, 2)])
    comb = pypgl.Polygon(
        [
            Point(1, 1), Point(3, 1), Point(3, 5), Point(5, 5), Point(6, 2),
            Point(7, 5), Point(9, 5), Point(9, 2), Point(11, 2), Point(11, 6),
            Point(1, 6),
        ]
    )
    kinds = {type(piece).__name__ for piece in bar.intersection(comb)}
    assert kinds == {"Point", "Polyline", "Polygon"}


def test_a_region_operand_keeps_the_holes_in_the_answer():
    bar = pypgl.Polygon([Point(0, 0), Point(12, 0), Point(12, 2), Point(0, 2)])
    split = bar.difference(pypgl.Rectangle(Point(4, -1), Point(5, 3)))
    pieces = split.intersection(bar)
    assert all(
        isinstance(piece, (Point, pypgl.Polyline, pypgl.PolygonWithHoles))
        for piece in pieces
    )
    assert sum(
        piece.area() for piece in pieces if isinstance(piece, pypgl.PolygonWithHoles)
    ) == split.area()


def test_a_chain_meets_a_polygon_in_a_list_of_pieces():
    chain = pypgl.MonotoneChain([Point(-1, 1), Point(5, 1)])
    square = pypgl.Polygon([Point(0, 0), Point(4, 0), Point(4, 2), Point(0, 2)])
    pieces = chain.intersection(square)
    assert [type(p).__name__ for p in pieces] == ["Segment"]
    assert pieces[0] == Segment(0, 1, 4, 1)


def test_a_disk_still_only_meets_a_point():
    disk = pypgl.Disk(Point(0, 0), 5)
    assert disk.intersection(Point(1, 1)) == Point(1, 1)
    assert disk.intersection(Point(9, 9)) is None
    with pytest.raises(TypeError):
        disk.intersection(pypgl.Rectangle(Point(0, 0), Point(1, 1)))


# --- a zero-length operand is a point, not a direction ----------------------
#
# Every orientation test against a zero-length segment vanishes, which reads as
# collinear and let the 1D overlap answer with an endpoint lying on neither
# shape. Both families now ask the point directly.

def test_a_degenerate_segment_intersects_only_where_its_point_lies():
    diagonal = pypgl.Segment(Point(0, 0), Point(10, 10))
    # Off the supporting line but inside its bounding box, so no cheap
    # rejection settles it: the answer has to come from the point itself.
    for off in (Point(10, 0), Point(0, 10), Point(3, 7)):
        degenerate = pypgl.Segment(off, off)
        assert diagonal.intersection(degenerate) is None
        assert degenerate.intersection(diagonal) is None
        assert degenerate.intersection(degenerate) == off
    for on in (Point(5, 5), Point(2, 2)):
        degenerate = pypgl.Segment(on, on)
        assert diagonal.intersection(degenerate) == on
        assert degenerate.intersection(diagonal) == on


def test_a_convex_shape_intersects_a_degenerate_segment_it_contains():
    # A zero-length segment has no supporting line to clip the hull against,
    # so the convex shapes answer for the point it is.
    square = pypgl.Convex([Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)])
    inside = pypgl.Segment(Point(5, 5), Point(5, 5))
    assert square.intersection(inside) == Point(5, 5)
    on_edge = pypgl.Segment(Point(0, 5), Point(0, 5))
    assert square.intersection(on_edge) == Point(0, 5)
    outside = pypgl.Segment(Point(50, 5), Point(50, 5))
    assert square.intersection(outside) is None


# --- The grid is square now -------------------------------------------------
#
# Every one of the sixteen non-Disk shapes intersects all sixteen, in either
# order. Two gaps closed upstream to make that true: a PolygonSet against the
# lower-dimensional shapes, and a chain against a HalfplaneIntersection.


ALL_SHAPES = [
    "Point", "Segment", "OrientedSegment", "Line", "OrientedLine", "Ray", "Halfplane",
    "Triangle", "Rectangle", "Convex", "MonotoneChain", "Polyline", "Polygon",
    "PolygonWithHoles", "HalfplaneIntersection", "PolygonSet",
]


def _one_of_each():
    square = pypgl.Polygon([0, 0, 10, 0, 10, 10, 0, 10])
    return {
        "Point": Point(5, 5),
        "Segment": Segment(Point(-5, 5), Point(15, 5)),
        "OrientedSegment": pypgl.OrientedSegment(Point(-5, 4), Point(15, 4)),
        "Line": pypgl.Line(Point(0, 6), Point(1, 6)),
        "OrientedLine": pypgl.OrientedLine(Point(0, 7), Point(1, 7)),
        "Ray": pypgl.Ray(Point(-5, 3), Point(0, 3)),
        "Halfplane": pypgl.Halfplane(Point(0, 0), Point(1, 0)),
        "Triangle": pypgl.Triangle(Point(1, 1), Point(9, 1), Point(1, 9)),
        "Rectangle": pypgl.Rectangle(Point(2, 2), Point(8, 8)),
        "Convex": pypgl.Convex([Point(1, 1), Point(9, 1), Point(9, 9), Point(1, 9)]),
        "MonotoneChain": pypgl.MonotoneChain([Point(-5, 2), Point(5, 8), Point(15, 2)]),
        "Polyline": pypgl.Polyline([Point(-5, 8), Point(5, 2), Point(15, 8)]),
        "Polygon": square,
        "PolygonWithHoles": square.asPolygonWithHoles(),
        "HalfplaneIntersection": pypgl.Rectangle(
            Point(1, 1), Point(9, 9)
        ).asHalfplaneIntersection(),
        "PolygonSet": square.asPolygonSet(),
    }


@pytest.mark.parametrize("left", ALL_SHAPES)
def test_every_non_disk_pair_intersects_in_both_orders(left):
    shapes = _one_of_each()
    a = shapes[left]
    for right in ALL_SHAPES:
        b = shapes[right]
        # Neither direction may raise; what comes back is a shape, a list of
        # them, or None when the pair is disjoint.
        a.intersection(b)
        b.intersection(a)


def test_a_polygon_set_now_meets_the_lower_dimensional_shapes():
    square = pypgl.Polygon([0, 0, 10, 0, 10, 10, 0, 10]).asPolygonSet()
    crossing = Segment(Point(-5, 5), Point(15, 5))
    assert square.intersection(crossing) == [Segment(Point(0, 5), Point(10, 5))]
    assert crossing.intersection(square) == square.intersection(crossing)
    # A Point operand is the one pair whose answer is a single optional piece.
    assert square.intersection(Point(5, 5)) == Point(5, 5)
    assert Point(5, 5).intersection(square) == Point(5, 5)
    assert square.intersection(Point(50, 5)) is None
    for unbounded in (
        pypgl.Line(Point(0, 5), Point(1, 5)),
        pypgl.OrientedLine(Point(0, 5), Point(1, 5)),
        pypgl.Ray(Point(-5, 5), Point(0, 5)),
    ):
        assert square.intersection(unbounded) == [Segment(Point(0, 5), Point(10, 5))]


def test_a_polygon_set_reports_a_piece_per_component():
    apart = pypgl.PolygonSet(
        [
            pypgl.Polygon([0, 0, 2, 0, 2, 2, 0, 2]).asPolygonWithHoles(),
            pypgl.Polygon([5, 0, 7, 0, 7, 2, 5, 2]).asPolygonWithHoles(),
        ]
    )
    across = pypgl.Line(Point(0, 1), Point(1, 1))
    pieces = apart.intersection(across)
    assert sorted(repr(p) for p in pieces) == sorted(
        repr(p)
        for p in [Segment(Point(0, 1), Point(2, 1)), Segment(Point(5, 1), Point(7, 1))]
    )


def test_a_chain_now_meets_a_halfplane_intersection():
    strip = pypgl.Rectangle(Point(0, 0), Point(10, 10)).asHalfplaneIntersection()
    for chain in (
        pypgl.MonotoneChain([Point(-5, 5), Point(15, 5)]),
        pypgl.Polyline([Point(-5, 5), Point(15, 5)]),
    ):
        clipped = chain.intersection(strip)
        assert clipped == [Segment(Point(0, 5), Point(10, 5))]
        assert strip.intersection(chain) == clipped
    # An unbounded region clips a chain just as well -- the chain is bounded, so
    # the answer is.
    half = pypgl.HalfplaneIntersection([pypgl.Halfplane(Point(0, 0), Point(1, 0))])
    zigzag = pypgl.Polyline([Point(0, -2), Point(2, 2), Point(4, -2)])
    pieces = zigzag.intersection(half)
    assert pieces and all(isinstance(p, (Point, Segment)) for p in pieces)
