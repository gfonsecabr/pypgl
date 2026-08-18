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
