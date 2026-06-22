"""Typed geometric results: optional -> None, variant -> concrete shape type."""

import pypgl


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
