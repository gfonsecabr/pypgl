"""The uniform predicate surface and the ``in`` sugar."""

import pypgl


def test_point_contains_point():
    p = pypgl.Point(1, 2)
    assert p.contains(pypgl.Point(1, 2))
    assert not p.contains(pypgl.Point(1, 3))


def test_segment_contains_point():
    s = pypgl.Segment(0, 0, 4, 4)
    assert s.contains(pypgl.Point(2, 2))
    assert not s.contains(pypgl.Point(2, 3))


def test_in_operator_point_in_shape():
    s = pypgl.Segment(0, 0, 4, 4)
    assert pypgl.Point(2, 2) in s
    assert pypgl.Point(2, 3) not in s
    assert pypgl.Point(1, 1) in pypgl.Point(1, 1)


def test_boundary_vs_interior_contains():
    s = pypgl.Segment(0, 0, 4, 0)
    endpoint = pypgl.Point(0, 0)
    middle = pypgl.Point(2, 0)
    assert s.boundaryContains(endpoint)
    assert not s.interiorContains(endpoint)
    assert s.interiorContains(middle)


def test_intersects_and_crosses():
    a = pypgl.Segment(0, 0, 4, 0)
    b = pypgl.Segment(2, -2, 2, 2)
    assert a.intersects(b)
    assert a.crosses(b)
    parallel = pypgl.Segment(0, 1, 4, 1)
    assert not a.intersects(parallel)
