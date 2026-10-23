"""`Polygon.minimumWeightTriangulation`, against an exhaustive reference.

The reference enumerates every triangulation of a small polygon by its own
vertices -- the classic recursion over the triangle on edge (i, j), whose apex k
must see both i and j along a side or a clear diagonal -- and takes the least
total diagonal weight. Clear diagonals are decided by
`Polygon.interiorContainsInterior`, which shares no code with the triangular
expansion the library runs. The polygons are random star-shaped rings on a small
grid, so collinear vertices and diagonals grazing a vertex are common.
"""

import math
import random
from fractions import Fraction
from functools import lru_cache

import pytest

import pypgl
from pypgl import Point, Polygon, Segment


def _random_polygon(rng, n, span=6):
    """A simple star-shaped polygon with positive area, or None."""
    points = list({Point(rng.randint(0, span), rng.randint(0, span)) for _ in range(n)})
    if len(points) < 3:
        return None
    # The vertices' centroid lies strictly inside their hull unless they are
    # collinear, which is what makes the angular order a simple ring.
    center = Point(Fraction(sum(p.x() for p in points), len(points)),
                   Fraction(sum(p.y() for p in points), len(points)))
    if center in points:
        return None
    pypgl.sortAround(points, center)
    polygon = Polygon(points)
    if polygon.isDegenerate() or not polygon.isSimple():
        return None
    return polygon


def _clear(polygon, ring, i, j):
    n = len(ring)
    if (j - i) % n in (1, n - 1):
        return True  # a side
    return polygon.interiorContainsInterior(Segment(ring[i], ring[j]))


def _reference_minimum(polygon, weight):
    ring = list(polygon.vertices())
    n = len(ring)

    @lru_cache(maxsize=None)
    def best(i, j):
        # Least weight of the diagonals strictly inside the sub-polygon i..j,
        # or None when it has no triangulation.
        if j - i < 2:
            return 0
        result = None
        for k in range(i + 1, j):
            if not (_clear(polygon, ring, i, k) and _clear(polygon, ring, k, j)):
                continue
            left, right = best(i, k), best(k, j)
            if left is None or right is None:
                continue
            cost = left + right
            if k - i > 1:
                cost += weight(ring[i], ring[k])
            if j - k > 1:
                cost += weight(ring[k], ring[j])
            if result is None or cost < result:
                result = cost
        return result

    return best(0, n - 1)


def _diagonal_weight(polygon, triangulation, weight):
    ring = list(polygon.vertices())
    sides = {frozenset((ring[i], ring[(i + 1) % len(ring)])) for i in range(len(ring))}
    total = 0
    for e in triangulation.edges():
        if frozenset((e.min(), e.max())) not in sides:
            total += weight(e.min(), e.max())
    return total


def _check_tiles(polygon, triangulation):
    triangles = triangulation.triangles()
    assert len(triangles) == len(polygon) - 2
    assert sum(t.area() for t in triangles) == polygon.area()
    corners = {v for t in triangles for v in t.vertices()}
    assert corners == set(polygon.vertices())
    assert all(polygon.contains(t) for t in triangles)


def _squared(p, q):
    return p.squaredDistance(q)


def _manhattan(p, q):  # an int weight with many ties
    return int(abs(p.x() - q.x()) + abs(p.y() - q.y()))


@pytest.mark.parametrize("weight", [_squared, _manhattan])
def test_an_exact_weight_gives_the_exact_minimum(weight):
    rng = random.Random(33)
    checked = convex = 0
    while checked < 150:
        polygon = _random_polygon(rng, rng.randint(4, 10))
        if polygon is None:
            continue
        triangulation = polygon.minimumWeightTriangulation(weight)
        _check_tiles(polygon, triangulation)
        assert _diagonal_weight(polygon, triangulation, weight) == \
            _reference_minimum(polygon, weight)
        checked += 1
        convex += polygon.isConvex()
    # Both code paths ran: the dense table for a convex ring and the
    # expansion over clear diagonals otherwise.
    assert 0 < convex < checked


def test_the_default_weight_is_the_euclidean_length():
    rng = random.Random(7)
    checked = 0
    while checked < 60:
        polygon = _random_polygon(rng, rng.randint(4, 9))
        if polygon is None:
            continue
        triangulation = polygon.minimumWeightTriangulation()
        _check_tiles(polygon, triangulation)
        length = lambda p, q: math.dist((p.x(), p.y()), (q.x(), q.y()))
        assert _diagonal_weight(polygon, triangulation, length) == \
            pytest.approx(_reference_minimum(polygon, length))
        checked += 1


def test_the_weight_decides_and_need_not_be_a_metric():
    # A convex pentagon has five triangulations, one per fan apex. A weight
    # that is cheap only at one vertex picks that fan, even with negative
    # values.
    pentagon = Polygon([0, 0, 4, 0, 5, 3, 2, 5, -1, 3])
    for apex in pentagon.vertices():
        weight = lambda p, q: -10 if apex in (p, q) else 1
        triangulation = pentagon.minimumWeightTriangulation(weight)
        assert all(apex in t.vertices() for t in triangulation.triangles())


def test_the_weight_is_called_once_per_clear_diagonal():
    polygon = Polygon([0, 0, 6, 0, 6, 6, 3, 2, 0, 6])  # one reflex vertex
    ring = list(polygon.vertices())
    clear = {frozenset((ring[i], ring[j]))
             for i in range(len(ring)) for j in range(i + 2, len(ring))
             if (i, j) != (0, len(ring) - 1) and _clear(polygon, ring, i, j)}
    calls = []
    polygon.minimumWeightTriangulation(lambda p, q: calls.append(frozenset((p, q))) or 1)
    assert len(calls) == len(set(calls))
    assert set(calls) == clear


def test_the_result_is_unconstrained():
    polygon = Polygon([0, 0, 6, 0, 6, 6, 3, 2, 0, 6])
    triangulation = polygon.minimumWeightTriangulation()
    assert not any(triangulation.isConstrained(e) for e in triangulation.edges())


def test_a_python_error_in_the_weight_propagates():
    pentagon = Polygon([0, 0, 4, 0, 5, 3, 2, 5, -1, 3])
    with pytest.raises(ZeroDivisionError):
        pentagon.minimumWeightTriangulation(lambda p, q: 1 / 0)
    with pytest.raises(TypeError):
        pentagon.minimumWeightTriangulation(lambda p, q: "heavy")


@pytest.mark.parametrize("polygon", [
    Polygon(),
    Polygon([0, 0, 1, 1]),
    Polygon([0, 0, 1, 1, 2, 2]),  # no area
])
def test_a_polygon_without_area_gives_an_empty_triangulation(polygon):
    assert polygon.minimumWeightTriangulation().triangles() == []
    assert polygon.minimumWeightTriangulation(_squared).triangles() == []


def test_a_triangle_is_its_own_triangulation():
    polygon = Polygon([0, 0, 4, 0, 0, 3])
    assert polygon.minimumWeightTriangulation(_squared).triangles() == \
        [pypgl.Triangle(Point(0, 0), Point(4, 0), Point(0, 3))]
