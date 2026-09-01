"""``latticePoints()``: the integer points a bounded shape contains.

The boundary counts as ``contains`` counts it, so a point on an edge is a point
of the shape, and every point is reported once. Twelve shapes have it -- every
bounded one except ``Point``, plus ``HalfplaneIntersection``, which raises when
it is unbounded; the four unbounded shapes cover infinitely many and do not.

The coordinates come back as an ordinary exact ``Point``, so the answer is never
capped by a machine integer: a short segment sitting at x = 10**20 has three
lattice points and names them.
"""

from fractions import Fraction

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


def region_with_hole():
    region = PolygonWithHoles(Polygon([0, 0, 8, 0, 8, 8, 0, 8]))
    region.addHole(Polygon([2, 2, 6, 2, 6, 6, 2, 6]))
    return region


# One of every kind of receiver: the two segments, the two chains, the three
# fixed convex shapes, the disk, the two polygons, the region, the set and the
# half-plane intersection.
SHAPES = {
    "Segment": Segment(Point(0, 0), Point(6, 4)),
    "OrientedSegment": OrientedSegment(Point(6, 4), Point(0, 0)),
    "Rectangle": Rectangle(Point(0, 0), Point(3, 2)),
    "Triangle": Triangle(Point(0, 0), Point(4, 0), Point(0, 4)),
    "Convex": Convex([0, 0, 4, 0, 4, 3, 0, 3]),
    "Polygon": Polygon([0, 0, 4, 0, 4, 4, 2, 2, 0, 4]),
    "Disk": Disk(Point(0, 0), 5),
    "MonotoneChain": MonotoneChain([0, 0, 3, 3, 6, 1]),
    "Polyline": Polyline([0, 0, 3, 3, 6, 1]),
    "PolygonWithHoles": region_with_hole(),
    "PolygonSet": PolygonSet(region_with_hole()),
    "HalfplaneIntersection": HalfplaneIntersection(
        Triangle(Point(0, 0), Point(5, 0), Point(0, 5))
    ),
}


@pytest.mark.parametrize("name", sorted(SHAPES))
def test_every_reported_point_is_a_point_of_the_shape(name):
    shape = SHAPES[name]
    points = shape.latticePoints()
    assert points
    assert all(shape.contains(point) for point in points)


@pytest.mark.parametrize("name", sorted(SHAPES))
def test_nothing_the_shape_contains_is_missed(name):
    """Against the brute-force answer over the bounding box."""
    shape = SHAPES[name]
    box = shape.bbox()
    brute = [
        Point(x, y)
        for x in range(int(box.min().x()), int(box.max().x()) + 1)
        for y in range(int(box.min().y()), int(box.max().y()) + 1)
        if shape.contains(Point(x, y))
    ]
    assert sorted(shape.latticePoints(), key=lambda p: (p.x(), p.y())) == sorted(
        brute, key=lambda p: (p.x(), p.y())
    )


@pytest.mark.parametrize("name", sorted(SHAPES))
def test_each_point_is_reported_once(name):
    points = SHAPES[name].latticePoints()
    assert len(set(points)) == len(points)


# --- ordering ---------------------------------------------------------------


def test_most_shapes_answer_in_increasing_order():
    for name, shape in SHAPES.items():
        if name == "OrientedSegment" or name == "Polyline":
            continue
        points = shape.latticePoints()
        assert points == sorted(points), name


def test_an_oriented_segment_lists_from_source_to_target():
    forward = OrientedSegment(Point(0, 0), Point(6, 4))
    backward = OrientedSegment(Point(6, 4), Point(0, 0))
    assert forward.latticePoints() == [Point(0, 0), Point(3, 2), Point(6, 4)]
    assert backward.latticePoints() == list(reversed(forward.latticePoints()))
    # The same points either way -- only the order is the orientation's.
    assert forward.latticePoints() == Segment(Point(0, 0), Point(6, 4)).latticePoints()


def test_a_polyline_walks_its_edges_and_reports_a_retraced_point_once():
    # Out to (4, 0) and back over the same stretch: every point is reached
    # first on the way out, so the return leg adds nothing.
    there_and_back = Polyline([0, 0, 4, 0, 1, 0])
    assert there_and_back.latticePoints() == [
        Point(0, 0),
        Point(1, 0),
        Point(2, 0),
        Point(3, 0),
        Point(4, 0),
    ]


def test_a_chain_reports_a_shared_vertex_once():
    chain = MonotoneChain([0, 0, 2, 2, 4, 0])
    assert chain.latticePoints().count(Point(2, 2)) == 1


# --- what counts as a point of the shape ------------------------------------


def test_the_boundary_is_included():
    triangle = Triangle(Point(0, 0), Point(4, 0), Point(0, 4))
    points = triangle.latticePoints()
    assert Point(0, 0) in points  # a vertex
    assert Point(2, 0) in points  # on an edge
    assert Point(2, 2) in points  # on the hypotenuse
    assert Point(3, 3) not in points


def test_a_hole_is_not_part_of_the_region_but_its_boundary_is():
    region = region_with_hole()
    points = region.latticePoints()
    assert Point(4, 4) not in points  # inside the hole
    assert Point(2, 4) in points  # on the hole's boundary
    assert Point(0, 0) in points  # on the outer boundary


def test_a_point_shared_by_two_components_is_reported_once():
    left = PolygonWithHoles(Polygon([0, 0, 2, 0, 2, 2, 0, 2]))
    right = PolygonWithHoles(Polygon([2, 0, 4, 0, 4, 2, 2, 2]))
    touching = PolygonSet([left, right])
    points = touching.latticePoints()
    assert points.count(Point(2, 1)) == 1
    assert len(set(points)) == len(points)


def test_a_disk_includes_a_point_at_exactly_the_radius():
    disk = Disk(Point(0, 0), 5)
    points = disk.latticePoints()
    assert Point(5, 0) in points
    assert Point(3, 4) in points  # 3-4-5, exactly on the boundary
    assert Point(4, 4) not in points


# --- the fractional and the very large --------------------------------------


def test_a_fractional_segment_still_reports_the_grid_points_it_passes_through():
    segment = Segment(Point(Fraction(1, 2), Fraction(1, 3)), Point(10, 7))
    assert segment.latticePoints() == [Point(10, 7)]


def test_a_supporting_line_that_misses_the_grid_reports_nothing():
    assert Segment(Point(Fraction(1, 2), 0), Point(Fraction(1, 2), 9)).latticePoints() == []


def test_an_endpoint_is_reported_only_when_it_is_a_lattice_point_itself():
    fractional = Segment(Point(Fraction(1, 2), Fraction(1, 2)), Point(4, 4))
    assert Point(4, 4) in fractional.latticePoints()
    assert Point(1, 1) in fractional.latticePoints()
    assert len(fractional.latticePoints()) == 4


def test_coordinates_beyond_a_machine_integer_are_named_exactly():
    """The answer is a Point, so it is never capped by the grid type."""
    huge = 10**20
    segment = Segment(Point(huge, 0), Point(huge, 3))
    assert segment.latticePoints() == [Point(huge, y) for y in range(4)]


# --- degenerate and empty ---------------------------------------------------


def test_a_degenerate_shape_answers_for_the_points_it_covers():
    assert Segment(Point(2, 3), Point(2, 3)).latticePoints() == [Point(2, 3)]
    assert Triangle(Point(0, 0), Point(2, 0), Point(4, 0)).latticePoints() == [
        Point(0, 0),
        Point(1, 0),
        Point(2, 0),
        Point(3, 0),
        Point(4, 0),
    ]


def test_a_shape_missing_the_grid_entirely_answers_with_nothing():
    quarter, three_quarters = Fraction(1, 4), Fraction(3, 4)
    tiny = Rectangle(Point(quarter, quarter), Point(three_quarters, three_quarters))
    assert tiny.latticePoints() == []
    assert Disk(Point(Fraction(1, 2), Fraction(1, 2)), Fraction(1, 4)).latticePoints() == []


# --- which shapes have it ---------------------------------------------------


def test_an_unbounded_region_raises():
    whole_plane = HalfplaneIntersection()
    with pytest.raises(Exception):
        whole_plane.latticePoints()
    wedge = HalfplaneIntersection([Halfplane(Point(0, 0), Point(1, 0))])
    with pytest.raises(Exception):
        wedge.latticePoints()


def test_the_unbounded_shapes_do_not_have_it():
    for shape in (
        Line(Point(0, 0), Point(1, 1)),
        OrientedLine(Point(0, 0), Point(1, 1)),
        Ray(Point(0, 0), Point(1, 1)),
        Halfplane(Point(0, 0), Point(1, 0)),
    ):
        assert not hasattr(shape, "latticePoints")
    # A Point is bounded but has none either: it is its own answer.
    assert not hasattr(Point(0, 0), "latticePoints")
