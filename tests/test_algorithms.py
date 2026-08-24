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
        "smallestEnclosingDisk", "closestPair", "regularizedUnionOf",
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


# --- smallest enclosing disk ------------------------------------------------

def test_smallest_enclosing_disk_of_a_square_is_its_circumcircle():
    corners = [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]
    disk = pypgl.smallestEnclosingDisk(corners)
    assert all(corner in disk for corner in corners)
    assert disk.center() == Point(2, 2)
    assert disk.squaredRadius() == 8


def test_interior_points_do_not_enlarge_the_disk():
    corners = [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]
    assert pypgl.smallestEnclosingDisk(corners + [Point(2, 2), Point(1, 3)]) == (
        pypgl.smallestEnclosingDisk(corners)
    )


def test_two_points_give_the_disk_on_their_diameter():
    disk = pypgl.smallestEnclosingDisk([Point(0, 0), Point(4, 0)])
    assert disk.center() == Point(2, 0)
    assert disk.radius() == 2                       # exact: pypgl halves exactly


def test_the_smallest_enclosing_disk_of_nothing_is_an_error():
    with pytest.raises(ValueError):
        pypgl.smallestEnclosingDisk([])


def test_a_convex_hull_encloses_itself_the_same_way():
    # The method form, which reads a boundary that is already convex and so
    # lives on Convex alone. Same answer as the free function over the points.
    corners = [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]
    hull = pypgl.Convex(corners)
    assert hull.smallestEnclosingDisk() == pypgl.smallestEnclosingDisk(corners)


def test_the_enclosing_disk_is_the_same_however_the_points_are_ordered():
    # The randomized incremental algorithm settled on a deterministic order
    # upstream, so a shuffled input gives back the identical disk.
    corners = [Point(0, 2), Point(4, 12), Point(10, 4), Point(16, 14), Point(8, -4)]
    first = pypgl.smallestEnclosingDisk(corners)
    assert pypgl.smallestEnclosingDisk(list(reversed(corners))) == first
    assert pypgl.smallestEnclosingDisk(corners[2:] + corners[:2]) == first


# --- smallest enclosing rectangle -------------------------------------------

def test_the_smallest_enclosing_rectangle_of_a_square_is_that_square():
    square = pypgl.Convex([0, 0, 4, 0, 4, 4, 0, 4])
    rect = square.smallestEnclosingRectangle()
    assert isinstance(rect, pypgl.HalfplaneIntersection)
    assert rect.samePointSet(square)


def test_the_enclosing_rectangle_may_be_tilted():
    # It minimizes *area* at whatever angle that takes, which is why it comes
    # back as four half-planes rather than as an axis-aligned Rectangle. A
    # diamond's tightest box is the tilted one, half the area of its bbox.
    diamond = pypgl.Convex([0, 4, 4, 0, 8, 4, 4, 8])
    rect = diamond.smallestEnclosingRectangle()
    assert rect.contains(diamond)
    assert rect.area() == 32                      # the bbox is 8 x 8
    assert rect.area() < diamond.bbox().area()


def test_the_enclosing_rectangle_stays_exact_on_a_slanted_hull():
    # Its corners are generally fractional even for integer input, and the
    # exact rational coordinates carry them without rounding.
    hull = pypgl.Convex([0, 0, 5, 1, 4, 5, 1, 4])
    rect = hull.smallestEnclosingRectangle()
    assert rect.contains(hull)
    for vertex in hull.vertices():
        assert vertex in rect


# --- closest pair -----------------------------------------------------------

def test_closest_pair_finds_the_two_nearest_points():
    points = [Point(0, 0), Point(10, 0), Point(11, 1), Point(0, 20)]
    pair = pypgl.closestPair(points)
    assert isinstance(pair, Segment)
    assert pair.squaredLength() == 2                # (10,0)--(11,1)
    assert set(pair.vertices()) == {Point(10, 0), Point(11, 1)}


def test_closest_pair_agrees_with_the_brute_force_answer():
    points = [Point(x, (x * x) % 7) for x in range(12)]
    best = min(
        (a.squaredDistance(b) for i, a in enumerate(points) for b in points[i + 1:]),
    )
    assert pypgl.closestPair(points).squaredLength() == best


def test_closest_pair_needs_two_points():
    with pytest.raises(ValueError):
        pypgl.closestPair([Point(0, 0)])


# --- regularized union of many shapes at once -------------------------------

def test_uniting_many_shapes_settles_them_in_one_arrangement():
    strips = [
        pypgl.Polygon([Point(i, 0), Point(i + 2, 0), Point(i + 2, 2), Point(i, 2)])
        for i in range(0, 6, 1)
    ]
    united = pypgl.regularizedUnionOf(strips)
    assert isinstance(united, pypgl.PolygonSet)
    assert united.componentCount() == 1
    assert united.area() == 7 * 2                   # x from 0 to 7


def test_uniting_disjoint_shapes_keeps_them_apart():
    apart = [
        pypgl.Convex([Point(0, 0), Point(1, 0), Point(0, 1)]),
        pypgl.Convex([Point(9, 9), Point(10, 9), Point(9, 10)]),
    ]
    united = pypgl.regularizedUnionOf(apart)
    assert united.componentCount() == 2
    assert not united.isConnected()


def test_the_simple_boundaries_flag_takes_the_faster_path_to_the_same_answer():
    shapes = [
        pypgl.Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]),
        pypgl.Polygon([Point(2, 2), Point(6, 2), Point(6, 6), Point(2, 6)]),
    ]
    assert pypgl.regularizedUnionOf(shapes, True) == pypgl.regularizedUnionOf(shapes)


def test_uniting_regions_keeps_the_holes_that_survive():
    square = pypgl.Polygon([Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)])
    annulus = square.difference(pypgl.Rectangle(Point(3, 3), Point(7, 7)))
    united = pypgl.regularizedUnionOf(list(annulus.components()))
    assert united.holeCount() == 1


def test_uniting_a_range_of_triangles():
    halves = [
        pypgl.Triangle(Point(0, 0), Point(2, 0), Point(2, 2)),
        pypgl.Triangle(Point(0, 0), Point(2, 2), Point(0, 2)),
    ]
    united = pypgl.regularizedUnionOf(halves)
    assert united.componentCount() == 1
    assert united.area() == 4
    # A triangle never has two of its own edges overlapping, so the flag is free.
    assert pypgl.regularizedUnionOf(halves, True) == united


def test_uniting_a_range_of_rectangles():
    overlapping = [
        pypgl.Rectangle(Point(0, 0), Point(2, 1)),
        pypgl.Rectangle(Point(1, 0), Point(3, 1)),
    ]
    united = pypgl.regularizedUnionOf(overlapping)
    assert united.componentCount() == 1
    assert united.area() == 3
    assert pypgl.regularizedUnionOf(overlapping, True) == united


def test_uniting_a_range_of_polygon_sets_flattens_their_components():
    apart = pypgl.regularizedUnionOf([
        pypgl.Rectangle(Point(0, 0), Point(1, 1)),
        pypgl.Rectangle(Point(4, 0), Point(5, 1)),
    ])
    assert apart.componentCount() == 2
    bridge = pypgl.Rectangle(Point(1, 0), Point(4, 1)).asPolygonSet()
    united = pypgl.regularizedUnionOf([apart, bridge])
    assert united.componentCount() == 1              # the bridge joins the two
    assert united.area() == 5
