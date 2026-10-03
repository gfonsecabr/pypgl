"""Vertex-subset simplification, the optimal convex partition, and convex layers.

`simplified(squaredTolerance)` keeps a subsequence of the vertices within a
Hausdorff distance of sqrt(squaredTolerance), so it never constructs a
coordinate and stays exact; it is checked here against the definition, using
the Euclidean Hausdorff distance (itself new for the non-convex shapes) as the
independent measure.
"""

import math
import random
from fractions import Fraction

import pytest

import pypgl
from pypgl import (
    Convex,
    MonotoneChain,
    Point,
    Polygon,
    PolygonSet,
    PolygonWithHoles,
    Polyline,
)


def _is_subsequence(small, big):
    it = iter(big)
    return all(any(v == w for w in it) for v in small)


def _random_points(rng, n, size=20):
    return [Point(rng.randint(0, size), rng.randint(0, size)) for _ in range(n)]


# --- simplified / simplify ---------------------------------------------------


SIMPLIFIABLE = (Convex, MonotoneChain, Polyline, Polygon, PolygonWithHoles, PolygonSet)


@pytest.mark.parametrize("cls", SIMPLIFIABLE)
def test_every_vertex_sequence_shape_has_both_forms(cls):
    assert callable(cls.simplified)
    assert callable(cls.simplify)


def test_zero_tolerance_drops_only_vertices_that_change_nothing():
    p = Polygon([0, 0, 2, 0, 4, 0, 4, 1, 4, 4, 2, 5, 0, 4])
    q = p.simplified(0)
    assert q == Polygon([0, 0, 4, 0, 4, 4, 2, 5, 0, 4])
    assert q.samePointSet(p)


def test_a_larger_tolerance_removes_more():
    p = Polygon([0, 0, 2, 0, 4, 0, 4, 1, 4, 4, 2, 5, 0, 4])
    assert p.simplified(1) == Polygon([0, 0, 4, 0, 4, 4, 0, 4])
    # The tolerance is compared exactly: a zigzag of amplitude 1 survives a
    # squared tolerance of 1/4 and collapses at exactly 1.
    zigzag = Polyline([0, 0, 1, 1, 2, 0, 3, 1, 4, 0])
    assert zigzag.simplified(Fraction(1, 4)) == zigzag
    assert zigzag.simplified(1) == Polyline([0, 0, 4, 0])


def test_the_chains_keep_their_endpoints_and_a_loop_stays_closed():
    zigzag = [0, 0, 1, 1, 2, 0, 3, 1, 4, 0]
    assert MonotoneChain(zigzag).simplified(2) == MonotoneChain([0, 0, 4, 0])
    loop = Polyline([0, 0, 4, 0, 4, 4, 0, 4, 0, 0])
    assert loop.isClosed()
    assert loop.simplified(1) == loop
    assert loop.simplified(100).isClosed()


def test_a_convex_shape_thinner_than_the_tolerance_can_collapse():
    thin = Convex([0, 0, 4, 0, 4, 1, 0, 1])
    flat = thin.simplified(1)
    assert len(flat.vertices()) < 3
    assert flat.squaredHausdorffDistance(thin) <= 1


def test_a_region_keeps_every_ring():
    outer = Polygon([0, 0, 10, 0, 10, 10, 0, 10])
    hole = Polygon([4, 4, 5, 4, 6, 4, 6, 6, 4, 6])
    region = PolygonWithHoles(outer, [hole])
    assert region.simplified(0) == PolygonWithHoles(outer, [Polygon([4, 4, 6, 4, 6, 6, 4, 6])])
    # A tolerance wider than the hole still leaves it in place.
    big = region.simplified(100)
    assert big.holeCount() == 1
    assert big.isValid()
    assert PolygonSet([region]).simplified(100).componentCount() == 1


def test_simplify_is_the_in_place_form():
    p = Polygon([0, 0, 2, 0, 4, 0, 4, 1, 4, 4, 2, 5, 0, 4])
    expected = p.simplified(1)
    q = Polygon(p)
    assert q.simplify(1) is None
    assert q == expected
    assert p != expected  # the original is untouched


@pytest.mark.parametrize("cls", SIMPLIFIABLE)
def test_an_empty_shape_simplifies_to_itself(cls):
    assert cls().simplified(1) == cls()


def test_a_float_tolerance_is_refused():
    with pytest.raises(TypeError):
        Polygon([0, 0, 4, 0, 4, 4]).simplified(0.5)


def test_a_frozen_shape_refuses_simplify_but_answers_simplified():
    frozen = Polygon([0, 0, 2, 0, 4, 0, 4, 4]).frozen()
    with pytest.raises(TypeError, match="simplified"):
        frozen.simplify(1)
    assert frozen.simplified(0) == Polygon([0, 0, 4, 0, 4, 4])


@pytest.mark.parametrize("make", [Polyline, MonotoneChain])
def test_random_chains_against_the_definition(make):
    rng = random.Random(7)
    for _ in range(150):
        chain = make(_random_points(rng, rng.randint(2, 12)))
        tolerance = Fraction(rng.randint(0, 40), rng.randint(1, 4))
        simple = chain.simplified(tolerance)
        assert _is_subsequence(simple.vertices(), chain.vertices())
        assert simple.vertices()[0] == chain.vertices()[0]
        assert simple.vertices()[-1] == chain.vertices()[-1]
        assert chain.squaredHausdorffDistance(simple) <= float(tolerance) * (1 + 1e-12)


def test_random_polygons_stay_simple_and_within_the_tolerance():
    rng = random.Random(11)
    center = Point(10, 10)
    checked = 0
    for _ in range(400):
        points = _random_points(rng, rng.randint(4, 14))
        if not Convex(points).interiorContains(center):
            continue
        pypgl.sortAround(points, center)
        polygon = Polygon(points)
        if not polygon.isSimple() or polygon.isDegenerate():
            continue
        checked += 1
        tolerance = Fraction(rng.randint(0, 30))
        simple = polygon.simplified(tolerance)
        assert simple.vertices()[0] == polygon.vertices()[0]
        assert set(map(repr, simple.vertices())) <= set(map(repr, polygon.vertices()))
        assert simple.isSimple()
        assert polygon.squaredHausdorffDistance(simple) <= float(tolerance) * (1 + 1e-12)
    assert checked > 100


# --- optimalConvexPartition ---------------------------------------------------


def test_the_optimal_partition_can_beat_the_heuristic_one():
    p = Polygon([0, 8, 6, 5, 8, 3, 8, 4, 8, 7, 11, 10])
    assert len(p.convexPartition()) == 3
    pieces = p.optimalConvexPartition()
    assert len(pieces) == 2
    assert all(isinstance(q, Convex) for q in pieces)
    assert sum(q.area() for q in pieces) == p.area()
    assert pypgl.regularizedUnionOf(pieces).samePointSet(p)


def test_a_comb_meets_the_reflex_lower_bound():
    # Every reflex vertex needs a diagonal, and a diagonal resolves at most two,
    # so r reflex vertices need at least ceil(r / 2) + 1 pieces.
    comb = Polygon([0, 0, 10, 0, 10, 4, 9, 4, 9, 1, 8, 1, 8, 4, 7, 4, 7, 1, 6, 1, 6, 4,
                    5, 4, 5, 1, 4, 1, 4, 4, 3, 4, 3, 1, 2, 1, 2, 4, 1, 4, 1, 1, 0, 1])
    reflex = 9
    assert len(comb.optimalConvexPartition()) == math.ceil(reflex / 2) + 1


def test_a_convex_polygon_is_one_piece():
    square = Polygon([0, 0, 1, 0, 1, 1, 0, 1])
    assert square.optimalConvexPartition() == [Convex([0, 0, 1, 0, 1, 1, 0, 1])]


def test_random_polygons_partition_no_worse_than_the_heuristic():
    rng = random.Random(3)
    center = Point(6, 6)
    checked = 0
    for _ in range(600):
        points = list({(rng.randint(0, 12), rng.randint(0, 12)) for _ in range(rng.randint(6, 12))})
        points = [Point(x, y) for x, y in points]
        if len(points) < 4 or not Convex(points).interiorContains(center):
            continue
        pypgl.sortAround(points, center)
        polygon = Polygon(points)
        if not polygon.isSimple() or polygon.isDegenerate():
            continue
        checked += 1
        pieces = polygon.optimalConvexPartition()
        assert len(pieces) <= len(polygon.convexPartition())
        assert sum(q.area() for q in pieces) == polygon.area()
        corners = set(map(repr, polygon.vertices()))
        assert all(set(map(repr, q.vertices())) <= corners for q in pieces)
    assert checked > 200


# --- convexLayers --------------------------------------------------------------


def _peel(points):
    """The definition: repeatedly take the extended hull of what is left."""
    left = {repr(p): p for p in points}
    layers = []
    while left:
        layer = pypgl.convexHullExtended(list(left.values()))
        layers.append(layer)
        for p in layer:
            del left[repr(p)]
    return layers


def test_a_grid_peels_into_nested_squares():
    grid = [Point(x, y) for x in range(5) for y in range(5)]
    layers = pypgl.convexLayers(grid)
    assert [len(layer) for layer in layers] == [16, 8, 1]
    assert layers[0][0] == Point(0, 0)  # counterclockwise from the smallest
    assert layers[0][1] == Point(1, 0)
    assert layers[2] == [Point(2, 2)]


def test_convex_layers_edge_cases():
    assert pypgl.convexLayers([]) == []
    assert pypgl.convexLayers([Point(1, 1), Point(1, 1)]) == [[Point(1, 1)]]
    collinear = [Point(2, 2), Point(0, 0), Point(1, 1)]
    assert pypgl.convexLayers(collinear) == [[Point(0, 0), Point(1, 1), Point(2, 2)]]


def test_convex_layers_against_repeated_hulls():
    rng = random.Random(5)
    for _ in range(100):
        points = _random_points(rng, rng.randint(1, 40), size=10)
        assert pypgl.convexLayers(points) == _peel(points)
