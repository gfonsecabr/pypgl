"""Free algorithms documented by Pangolin's algorithms reference."""

import pytest

import pypgl
from pypgl import Point, Segment


def test_algorithms_are_public():
    names = {
        "findIntersections", "findCrossings", "bruteForceIntersections",
        "bruteForceCrossings", "detectIntersections", "detectCrossings",
        "convexHull", "convexHullExtended", "sortAround", "hilbertSort",
        "polyominoes", "polyominoesUpTo",
    }
    assert names <= set(pypgl.__all__)
    assert all(callable(getattr(pypgl, name)) for name in names)


def test_segment_intersection_algorithms():
    diagonal = Segment(0, 0, 2, 2)
    crossing = Segment(0, 2, 2, 0)
    touching = Segment(2, 2, 3, 2)
    segments = [diagonal, crossing, touching]
    expected_crossings = [[diagonal, crossing]]
    expected_intersections = expected_crossings + [[diagonal, touching]]

    assert pypgl.findIntersections(segments) == expected_intersections
    assert pypgl.bruteForceIntersections(segments) == expected_intersections
    assert pypgl.findCrossings(segments) == expected_crossings
    assert pypgl.bruteForceCrossings(segments) == expected_crossings
    assert pypgl.detectIntersections(segments)
    assert pypgl.detectCrossings(segments)
    assert not pypgl.detectIntersections([diagonal])
    assert not pypgl.detectCrossings([diagonal, touching])


def test_convex_hulls():
    points = [
        Point(0, 0), Point(1, 0), Point(2, 0), Point(2, 2), Point(0, 2),
        Point(1, 1), Point(0, 0),
    ]
    assert pypgl.convexHull(points) == [
        Point(0, 0), Point(2, 0), Point(2, 2), Point(0, 2),
    ]
    assert pypgl.convexHullExtended(points) == [
        Point(0, 0), Point(1, 0), Point(2, 0), Point(2, 2), Point(0, 2),
    ]


def test_sorting_algorithms_reorder_the_input_list():
    points = [Point(0, 2), Point(2, 0), Point(0, 0), Point(2, 2)]

    assert pypgl.sortAround(points, Point(1, 1)) is None
    assert points == [Point(0, 0), Point(2, 0), Point(2, 2), Point(0, 2)]

    assert pypgl.hilbertSort(points) is None
    assert sorted(points) == [Point(0, 0), Point(0, 2), Point(2, 0), Point(2, 2)]


def test_sorting_algorithms_require_a_mutable_list():
    with pytest.raises(TypeError):
        pypgl.sortAround((Point(0, 0), Point(1, 1)), Point(0, 0))
    with pytest.raises(TypeError):
        pypgl.hilbertSort((Point(0, 0), Point(1, 1)))


def test_polyominoes():
    assert pypgl.polyominoes(0) == []
    assert len(pypgl.polyominoes(1)) == 1
    assert len(pypgl.polyominoes(4)) == 5
    assert len(pypgl.polyominoes(2, 3)) == 3
    assert len(pypgl.polyominoesUpTo(3)) == 4
    assert all(isinstance(polyomino, pypgl.Polygon) for polyomino in pypgl.polyominoes(3))
