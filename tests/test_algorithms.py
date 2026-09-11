"""Free algorithms documented by Pangolin's algorithms reference."""

import math
from fractions import Fraction

import pytest

import pypgl
from pypgl import Point, Segment


def test_algorithms_are_public():
    names = {
        "findIntersections", "findCrossings", "bruteForceIntersections",
        "bruteForceCrossings", "detectIntersections", "detectCrossings",
        "convexHull", "convexHullExtended",
        "sortPoints", "sortDistinctPoints", "sortAround", "hilbertSort",
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


def test_segment_sweep_handles_repeated_segments():
    # The Bentley-Ottmann sweep used to collapse two equal segments into one
    # status node, whose second RIGHT event then found nothing -- a silently
    # skipped event in a release build, and heap corruption in practice. Equal
    # segments are now swept once and the rest reported as meeting that one.
    a = Segment(0, 0, 4, 0)
    crossing = Segment(2, -1, 2, 1)
    segments = [a, a, crossing]

    assert pypgl.findIntersections(segments) == [[a, a], [a, crossing]]
    assert pypgl.detectIntersections(segments)
    assert pypgl.findCrossings(segments) == [[a, crossing]]
    assert pypgl.detectCrossings(segments)

    # The brute-force pair enumeration counts each pair of positions, so a
    # repeated segment gives it the same pair more than once; the sweep names
    # each pair of distinct segments once. The two agree as sets.
    def as_set(pairs):
        return {frozenset(map(repr, pair)) for pair in pairs}

    assert as_set(pypgl.findIntersections(segments)) == \
        as_set(pypgl.bruteForceIntersections(segments))
    assert as_set(pypgl.findCrossings(segments)) == \
        as_set(pypgl.bruteForceCrossings(segments))


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


def test_sort_points_orders_lexicographically():
    points = [Point(2, 0), Point(0, 2), Point(0, 0), Point(2, 2)]
    assert pypgl.sortPoints(points) is None
    assert points == [Point(0, 0), Point(0, 2), Point(2, 0), Point(2, 2)]


def test_sort_distinct_points_shortens_the_list_in_place():
    points = [Point(2, 2), Point(0, 0), Point(2, 2), Point(0, 0), Point(1, 1)]
    original = points
    assert pypgl.sortDistinctPoints(points) is None
    # The same list object, not a replacement: the duplicates are erased from it.
    assert points is original
    assert points == [Point(0, 0), Point(1, 1), Point(2, 2)]

    # Exact coordinates are ordered by value, not by how they were written.
    points = [Point("3/2", 0), Point(Fraction(3, 2), 0), Point(1, 0)]
    pypgl.sortDistinctPoints(points)
    assert points == [Point(1, 0), Point(Fraction(3, 2), 0)]

    for degenerate in ([], [Point(4, 4)], [Point(4, 4)] * 5):
        points = list(degenerate)
        pypgl.sortDistinctPoints(points)
        assert points == sorted(set(degenerate))


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
    with pytest.raises(TypeError):
        pypgl.sortPoints((Point(0, 0), Point(1, 1)))
    with pytest.raises(TypeError):
        pypgl.sortDistinctPoints((Point(0, 0), Point(1, 1)))


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


# --- minimum width ----------------------------------------------------------

def test_the_minimum_width_of_a_square_is_its_side():
    square = pypgl.Convex([0, 0, 4, 0, 4, 4, 0, 4])
    assert square.squaredMinimumWidth() == 16
    assert square.minimumWidth() == pytest.approx(4.0)


def test_the_narrowest_slab_is_the_other_half_of_the_calipers_pair():
    # Both supporting lines are exact -- one flush with an edge, one through
    # the farthest vertex -- so the slab is exact even though its width is not.
    strip = pypgl.Convex([Point(0, 0), Point(4, 2), Point(3, 4), Point(-1, 2)])
    slab = strip.smallestEnclosingSlab()
    assert isinstance(slab, pypgl.HalfplaneIntersection)
    assert slab.contains(strip)
    assert len(slab) == 2                          # two parallel half-planes
    assert strip.squaredMinimumWidth() == 5        # exact; the width is sqrt(5)
    assert strip.minimumWidth() == pytest.approx(math.sqrt(5))


def test_the_width_can_beat_every_side_of_the_bounding_box():
    # The minimum is attained flush with an edge, at whatever angle that is:
    # this parallelogram is thinner than either side of its 5 x 4 bbox.
    strip = pypgl.Convex([Point(0, 0), Point(4, 2), Point(3, 4), Point(-1, 2)])
    box = strip.bbox()
    assert strip.squaredMinimumWidth() < min(box.width(), box.height()) ** 2


def test_the_squared_width_is_the_exact_form_to_compare_with():
    triangle = pypgl.Convex([Point(0, 0), Point(4, 0), Point(2, 3)])
    assert triangle.squaredMinimumWidth() == 9      # 2 * area / longest edge
    assert isinstance(triangle.squaredMinimumWidth(), Fraction)
    assert isinstance(triangle.minimumWidth(), float)
    # Fitting through a gap of width w is decided exactly, with no square root.
    assert triangle.squaredMinimumWidth() <= Fraction(3) ** 2
    assert not triangle.squaredMinimumWidth() <= Fraction(29, 10) ** 2


def test_a_hull_of_fewer_than_three_vertices_has_no_width_to_minimize():
    for hull in (pypgl.Convex(), pypgl.Convex([Point(1, 1)]),
                 pypgl.Convex([Point(0, 0), Point(5, 5)])):
        assert hull.squaredMinimumWidth() == 0
        assert hull.minimumWidth() == 0.0
        # The degenerate slab of width zero is the hull's own region.
        assert hull.smallestEnclosingSlab() == hull.asHalfplaneIntersection()


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
