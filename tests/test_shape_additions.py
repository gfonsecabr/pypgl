"""The per-shape methods that arrived alongside the two new shape classes.

Convex's incremental growth and its two hull chains, Polygon's star-shapedness
(whose kernel is a HalfplaneIntersection), MonotoneChain's erase and its
conversion to a Polyline, Polyline's 2-opt edge flip and in-place vertex
editing -- which the upstream change to verbatim storage is what made possible
-- and the region-valued polyomino enumeration.
"""

from fractions import Fraction

import pytest

import pypgl
from pypgl import (
    Convex,
    HalfplaneIntersection,
    MonotoneChain,
    Point,
    Polygon,
    PolygonWithHoles,
    Polyline,
    Rectangle,
    Segment,
    Triangle,
)


# --- Convex: growing a hull -------------------------------------------------

def test_insert_a_point_grows_the_hull():
    c = Convex([Point(0, 0), Point(4, 0), Point(0, 4)])
    c.insert(Point(4, 4))
    assert c == Convex([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])


def test_inserting_an_interior_point_changes_nothing():
    c = Convex([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])
    before = c.vertices()
    c.insert(Point(2, 2))
    assert c.vertices() == before


def test_insert_a_list_of_points():
    c = Convex([Point(0, 0)])
    c.insert([Point(4, 0), Point(4, 4), Point(0, 4)])
    assert c.area() == 16


@pytest.mark.parametrize(
    "shape",
    [
        Segment(Point(4, 0), Point(4, 4)),
        pypgl.OrientedSegment(Point(4, 0), Point(4, 4)),
        Triangle(Point(4, 0), Point(4, 4), Point(3, 2)),
        Rectangle(Point(0, 0), Point(4, 4)),
        Convex([Point(4, 0), Point(4, 4)]),
        Polygon([Point(4, 0), Point(4, 4), Point(3, 2)]),
    ],
)
def test_insert_a_shape_grows_the_hull_to_contain_it(shape):
    c = Convex([Point(0, 0), Point(0, 4)])
    c.insert(shape)
    assert c.contains(shape)


@pytest.mark.parametrize(
    "shape",
    [
        pypgl.Disk(Point(10, 10), 2),
        pypgl.Line(Point(0, 0), Point(1, 1)),
        pypgl.OrientedLine(Point(0, 0), Point(1, 1)),
        pypgl.Ray(Point(0, 0), Point(1, 1)),
        pypgl.Halfplane(Point(0, 0), Point(1, 1)),
    ],
    ids=lambda s: type(s).__name__,
)
def test_insert_rejects_a_shape_with_no_vertices(shape):
    # C++ takes only shapes exposing vertices(), so these are a compile error
    # there. They have to be refused explicitly here: every pypgl shape is
    # iterable over its defining points, so without a guard a Disk would satisfy
    # the list-of-points overload and quietly contribute its three *boundary*
    # points -- whose hull the disk bulges straight past.
    c = Convex([Point(0, 0), Point(4, 4)])
    with pytest.raises(TypeError):
        c.insert(shape)


def test_the_refusal_is_not_merely_conservative():
    # Guard the guard: the points a Disk would have contributed really do not
    # contain it.
    disk = pypgl.Disk(Point(10, 10), 2)
    hull_of_its_points = Convex([Point(0, 0), Point(4, 4)] + list(disk))
    assert not hull_of_its_points.contains(disk)


# --- Convex: the two hull chains --------------------------------------------

def test_upper_and_lower_hulls_are_monotone_chains():
    c = Convex([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])
    assert isinstance(c.upperHull(), MonotoneChain)
    assert isinstance(c.lowerHull(), MonotoneChain)


def test_the_two_hulls_split_the_boundary_at_the_extreme_vertices():
    c = Convex([Point(0, 0), Point(2, 3), Point(4, 0), Point(2, -3)])
    upper, lower = c.upperHull(), c.lowerHull()
    # Both run between the leftmost and rightmost vertices.
    assert upper[0] == lower[0] == Point(0, 0)
    assert upper[-1] == lower[-1] == Point(4, 0)
    # The apex belongs to the upper chain and the nadir to the lower one.
    assert Point(2, 3) in upper.vertices()
    assert Point(2, -3) in lower.vertices()


def test_every_hull_vertex_lies_on_one_of_the_two_chains():
    c = Convex([Point(0, 0), Point(2, 3), Point(4, 0), Point(2, -3)])
    covered = set(c.upperHull().vertices()) | set(c.lowerHull().vertices())
    assert set(c.vertices()) <= covered


# --- Polygon: star-shapedness ------------------------------------------------

def test_a_convex_polygon_is_star_shaped_from_anywhere_inside():
    p = Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])
    assert p.isStarShaped()
    kernel = p.getStarShapedKernel()
    assert isinstance(kernel, HalfplaneIntersection)
    # For a convex polygon the kernel is the polygon itself.
    assert kernel.area() == p.area()


def test_an_l_shape_is_star_shaped_with_a_smaller_kernel():
    ell = Polygon(
        [
            Point(0, 0), Point(6, 0), Point(6, 2),
            Point(2, 2), Point(2, 6), Point(0, 6),
        ]
    )
    assert ell.isStarShaped()
    kernel = ell.getStarShapedKernel()
    assert kernel.area() < ell.area()
    # Every point of the kernel sees the whole polygon, so in particular the
    # kernel lies inside the polygon.
    assert ell.contains(kernel.pointInside())


def test_a_spiral_is_not_star_shaped_and_has_no_kernel():
    # A U with deep arms: no single point sees into both of them.
    u = Polygon(
        [
            Point(0, 0), Point(6, 0), Point(6, 8), Point(4, 8),
            Point(4, 2), Point(2, 2), Point(2, 8), Point(0, 8),
        ]
    )
    assert not u.isStarShaped()
    assert u.getStarShapedKernel() is None


def test_the_kernel_sees_the_whole_polygon():
    ell = Polygon(
        [
            Point(0, 0), Point(6, 0), Point(6, 2),
            Point(2, 2), Point(2, 6), Point(0, 6),
        ]
    )
    centre = ell.getStarShapedKernel().pointInside()
    for vertex in ell:
        assert ell.contains(Segment(centre, vertex))


# --- MonotoneChain: erase and the Polyline conversion -----------------------

def test_erase_a_vertex_by_value():
    c = MonotoneChain([Point(0, 0), Point(2, 2), Point(4, 0)])
    assert c.erase(Point(2, 2)) is True
    assert c.vertices() == [Point(0, 0), Point(4, 0)]
    # Erasing one that is not there reports so rather than raising.
    assert c.erase(Point(9, 9)) is False


def test_erasing_an_interior_vertex_reroutes_the_chain():
    c = MonotoneChain([Point(0, 0), Point(2, 5), Point(4, 0)])
    c.erase(Point(2, 5))
    # The neighbours are now joined by a single edge.
    assert c.edges() == [Segment(Point(0, 0), Point(4, 0))]


def test_erasing_an_extreme_vertex_shortens_the_chain():
    c = MonotoneChain([Point(0, 0), Point(2, 2), Point(4, 0)])
    c.erase(Point(4, 0))
    assert c.vertices() == [Point(0, 0), Point(2, 2)]


def test_erase_a_vertex_by_index():
    c = MonotoneChain([Point(0, 0), Point(2, 2), Point(4, 0)])
    c.erase(1)  # index is over the lexicographic order, as indexing is
    assert c.vertices() == [Point(0, 0), Point(4, 0)]


def test_as_polyline_keeps_the_vertex_sequence():
    c = MonotoneChain([Point(0, 0), Point(2, 2), Point(4, 0)])
    p = c.asPolyline()
    assert isinstance(p, Polyline)
    assert p.vertices() == c.vertices()


# --- Polyline: verbatim storage and in-place editing -------------------------

def test_the_stored_order_is_the_order_given():
    # Upstream stopped canonicalizing the traversal direction, so the sequence
    # comes back exactly as passed.
    points = [Point(4, 4), Point(0, 0), Point(2, 9)]
    assert Polyline(points).vertices() == points


def test_a_polyline_still_equals_its_own_reverse():
    # Direction is not part of a polyline's identity: equality, ordering and
    # hashing read the vertices through the canonical direction.
    forward = [Point(0, 0), Point(2, 2), Point(4, 0)]
    assert Polyline(forward) == Polyline(list(reversed(forward)))


def test_set_replaces_a_vertex():
    p = Polyline([Point(0, 0), Point(2, 2), Point(4, 0)])
    p.set(1, Point(2, 9))
    assert p.vertices() == [Point(0, 0), Point(2, 9), Point(4, 0)]


def test_insert_shifts_the_rest_along():
    p = Polyline([Point(0, 0), Point(4, 0)])
    p.insert(1, Point(2, 2))
    assert p.vertices() == [Point(0, 0), Point(2, 2), Point(4, 0)]


def test_insert_several_vertices_at_once():
    p = Polyline([Point(0, 0), Point(6, 0)])
    p.insert(1, [Point(2, 2), Point(4, 2)])
    assert p.vertices() == [Point(0, 0), Point(2, 2), Point(4, 2), Point(6, 0)]


def test_push_back_extends_by_one_edge():
    p = Polyline([Point(0, 0), Point(2, 2)])
    p.pushBack(Point(4, 0))
    assert len(p.edges()) == 2
    assert p.vertices()[-1] == Point(4, 0)


def test_push_back_several_vertices():
    p = Polyline([Point(0, 0)])
    p.pushBack([Point(2, 2), Point(4, 0)])
    assert p.vertices() == [Point(0, 0), Point(2, 2), Point(4, 0)]


# --- Polyline: the 2-opt edge flip ------------------------------------------

def _crossed():
    """A self-crossing polyline whose crossing one flip removes."""
    return Polyline([Point(0, 0), Point(4, 4), Point(4, 0), Point(0, 4)])


# Removing the first edge leaves A = [(0,0)] and B = [(4,4),(4,0),(0,4)], and
# rejoining (0,0) to B's far end reverses B -- one of the three reconnections.
UNCROSSING_OLD = Segment(Point(0, 0), Point(4, 4))
UNCROSSING_NEW = Segment(Point(0, 0), Point(0, 4))


def test_a_flip_uncrosses_a_polyline():
    p = _crossed()
    assert not p.isSimple()
    assert p.flippable(UNCROSSING_OLD, UNCROSSING_NEW)
    flipped = p.flipped(UNCROSSING_OLD, UNCROSSING_NEW)
    assert flipped.isSimple()
    assert flipped.vertices() == [Point(0, 0), Point(0, 4), Point(4, 0), Point(4, 4)]


def test_flip_mutates_in_place_and_flipped_copies():
    p = _crossed()
    copy = p.flipped(UNCROSSING_OLD, UNCROSSING_NEW)
    assert not p.isSimple()  # flipped() left the original alone
    p.flip(UNCROSSING_OLD, UNCROSSING_NEW)
    assert p == copy
    assert p.isSimple()


def test_a_flip_that_is_valid_need_not_uncross():
    # flippable only promises a path over the same vertices, not a simple one.
    p = _crossed()
    old, new = Segment(Point(4, 0), Point(4, 4)), Segment(Point(0, 0), Point(4, 0))
    assert p.flippable(old, new)
    assert not p.flipped(old, new).isSimple()


def test_readding_the_removed_edge_is_not_a_flip():
    p = _crossed()
    edge = Segment(Point(4, 4), Point(4, 0))
    assert not p.flippable(edge, edge)


def test_a_flip_needs_an_existing_edge():
    p = _crossed()
    assert not p.flippable(
        Segment(Point(9, 9), Point(9, 8)), Segment(Point(0, 0), Point(4, 0))
    )


def test_a_flip_preserves_the_vertex_set():
    p = _crossed()
    before = set(p.vertices())
    p.flip(UNCROSSING_OLD, UNCROSSING_NEW)
    assert set(p.vertices()) == before


# --- polyominoRegions --------------------------------------------------------

def test_polyomino_regions_are_regions():
    regions = pypgl.polyominoRegions(4)
    assert all(isinstance(r, PolygonWithHoles) for r in regions)
    assert len(regions) == 5  # the five tetrominoes


def test_each_region_has_area_equal_to_its_cell_count():
    for size in (1, 2, 3, 4, 5):
        for r in pypgl.polyominoRegions(size):
            assert r.area() == size


def test_regions_keep_the_holed_polyominoes_that_polygons_drop():
    # A region can represent a polyomino enclosing a hole, where a polygon
    # cannot: such a boundary is not a simple polygon. So the counts differ from
    # size seven onward, and the region counts are the full free-polyomino ones.
    assert len(pypgl.polyominoRegions(6)) == len(pypgl.polyominoes(6))
    assert len(pypgl.polyominoRegions(7)) == 108
    assert len(pypgl.polyominoes(7)) == 107


def test_the_smallest_holed_polyomino_pinches_its_hole_shut_at_a_point():
    # Two diagonally opposite cells close the hole against the outside; isValid
    # accepts that, and the pinch point is in the region without having any
    # region interior around it.
    holed = [r for r in pypgl.polyominoRegions(7) if r.hasHoles()]
    assert len(holed) == 1
    assert holed[0].isValid()
    assert holed[0].area() == 7


def test_the_range_and_up_to_overloads_mirror_the_polygon_ones():
    assert len(pypgl.polyominoRegions(1, 3)) == sum(
        len(pypgl.polyominoRegions(n)) for n in (1, 2, 3)
    )
    assert pypgl.polyominoRegionsUpTo(3) == pypgl.polyominoRegions(1, 3)


def test_polyomino_regions_are_exported():
    assert "polyominoRegions" in pypgl.__all__
    assert "polyominoRegionsUpTo" in pypgl.__all__


# --- accessors that were declared upstream but never bound ------------------
#
# These are all pre-existing omissions rather than new upstream API, found by
# auditing every class's documented C++ methods against dir(cls) after porting
# pgl's examples turned up the first of them (Convex.verticesCentroid, which
# example3 needs).

def test_convex_vertices_centroid():
    # The vertex-set centroid, which for a non-regular polygon differs from the
    # area-weighted one. Polygon and PolygonWithHoles already had it.
    c = Convex([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])
    assert c.verticesCentroid() == Point(2, 2)
    # A triangle's two centroids coincide by definition, so the difference needs
    # at least four vertices: this trapezoid puts more area near the long base
    # than the vertex average sees.
    trapezoid = Convex([Point(0, 0), Point(8, 0), Point(6, 4), Point(0, 4)])
    assert trapezoid.verticesCentroid() == Point(Fraction(7, 2), 2)
    assert trapezoid.verticesCentroid() != trapezoid.centroid()


@pytest.mark.parametrize(
    "shape,count",
    [
        (Triangle(Point(0, 0), Point(4, 0), Point(0, 4)), 3),
        (Rectangle(Point(0, 0), Point(4, 4)), 4),
        (Convex([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]), 4),
    ],
    ids=["Triangle", "Rectangle", "Convex"],
)
def test_oriented_edges_wind_counterclockwise(shape, count):
    # orientedEdges was bound on Polygon and the chains but not on these three,
    # though pgl documents it for all of them.
    oriented = shape.orientedEdges()
    assert len(oriented) == count
    # Consecutive oriented edges join head to tail, all the way round.
    for current, following in zip(oriented, oriented[1:] + oriented[:1]):
        assert current.target() == following.source()
    # Same edges as edges(), just directed.
    assert {pypgl.Segment(e.source(), e.target()) for e in oriented} == set(shape.edges())


def test_triangle_named_vertex_accessors():
    # The counterpart of Disk.a/b/c, which pypgl already bound.
    t = Triangle(Point(0, 0), Point(4, 0), Point(0, 4))
    assert (t.a(), t.b(), t.c()) == (t[0], t[1], t[2])


def test_rectangle_center_width_height():
    r = Rectangle(Point(1, 2), Point(5, 8))
    assert r.center() == Point(3, 5) == r.centroid()
    assert r.width() == 4
    assert r.height() == 6


def test_rectangle_insert_grows_the_box():
    r = Rectangle(Point(0, 0), Point(1, 1))
    r.insert(Point(5, 5))
    assert r == Rectangle(Point(0, 0), Point(5, 5))
    r.insert([Point(-2, 0), Point(0, -3)])
    assert r == Rectangle(Point(-2, -3), Point(5, 5))


@pytest.mark.parametrize(
    "shape",
    [
        Rectangle(Point(6, 6), Point(8, 8)),
        Segment(Point(6, 6), Point(8, 8)),
        Triangle(Point(6, 6), Point(8, 6), Point(6, 8)),
        Convex([Point(6, 6), Point(8, 6), Point(6, 8)]),
        Polygon([Point(6, 6), Point(8, 6), Point(6, 8)]),
        # Unlike Convex.insert, this one needs only a bbox(), so a Disk works.
        pypgl.Disk(Point(7, 7), 1),
    ],
    ids=lambda s: type(s).__name__,
)
def test_rectangle_insert_accepts_anything_bounded(shape):
    r = Rectangle(Point(0, 0), Point(1, 1))
    r.insert(shape)
    assert r.contains(shape)


@pytest.mark.parametrize(
    "shape",
    [
        pypgl.Line(Point(0, 0), Point(1, 1)),
        pypgl.OrientedLine(Point(0, 0), Point(1, 1)),
        pypgl.Ray(Point(0, 0), Point(1, 1)),
        pypgl.Halfplane(Point(0, 0), Point(1, 1)),
    ],
    ids=lambda s: type(s).__name__,
)
def test_rectangle_insert_refuses_the_unbounded_shapes(shape):
    # No finite bounding box to grow to. Refused explicitly for the same reason
    # Convex.insert refuses: every shape is iterable, so the list-of-points
    # overload would otherwise take them.
    r = Rectangle(Point(0, 0), Point(1, 1))
    with pytest.raises(TypeError):
        r.insert(shape)


def test_monotone_chain_edges_cross():
    # Robust crossing: one chain has a point strictly above the other and one
    # strictly below, so no small perturbation separates them.
    rising = MonotoneChain([Point(0, 0), Point(4, 4)])
    falling = MonotoneChain([Point(0, 4), Point(4, 0)])
    assert rising.edgesCross(falling)
    assert falling.edgesCross(rising)
    # A chain that stays strictly above never swaps sides.
    above = MonotoneChain([Point(0, 10), Point(4, 12)])
    assert not rising.edgesCross(above)
    # Touching without swapping sides does not count either, unlike crosses().
    touching = MonotoneChain([Point(0, 4), Point(2, 2), Point(4, 4)])
    assert not rising.edgesCross(touching)


@pytest.mark.parametrize(
    "shape",
    [
        pypgl.Line(Point(0, 0), Point(1, 1)),
        pypgl.OrientedLine(Point(0, 0), Point(1, 1)),
        pypgl.Ray(Point(0, 0), Point(1, 1)),
        pypgl.Halfplane(Point(0, 0), Point(1, 1)),
        pypgl.Disk(Point(0, 0), 2),
        MonotoneChain([Point(0, 0), Point(2, 2)]),
        HalfplaneIntersection(Rectangle(Point(0, 0), Point(4, 4))),
    ],
    ids=lambda s: type(s).__name__,
)
def test_translation_only_shapes_still_have_the_named_minkowski_sum(shape):
    # Their only summable pair is with a Point. `shape + point` always worked;
    # the named spelling was missing, so which one you could use depended on
    # which shape you had.
    assert shape.minkowskiSum(Point(3, 4)) == shape + Point(3, 4)


@pytest.mark.parametrize(
    "shape",
    [
        PolygonWithHoles(
            Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]),
            [Polygon([Point(1, 1), Point(2, 1), Point(2, 2), Point(1, 2)])],
        ),
        HalfplaneIntersection(Rectangle(Point(0, 0), Point(4, 4))),
    ],
    ids=lambda s: type(s).__name__,
)
def test_the_new_mutable_shapes_have_in_place_transforms(shape):
    # Every other mutable shape (Convex, Polygon, the chains) had these; the two
    # new ones only got the value-returning forms.
    rotated = shape.rotated90()
    assert shape.rotate90() is None      # mutates, returns None
    assert shape == rotated

    scaled = shape.scaledUpX(3)
    shape.scaleUpX(3)
    assert shape == scaled
    shape.scaleDownX(3)
    assert shape == scaled.scaledDownX(3)

    scaled_y = shape.scaledUpY(2)
    shape.scaleUpY(2)
    assert shape == scaled_y
    shape.scaleDownY(2)
    assert shape == scaled_y.scaledDownY(2)


# --- the convex hull of any shape -------------------------------------------

@pytest.mark.parametrize(
    "shape, expected",
    [
        (Point(3, 4), Convex([3, 4])),
        (Segment(0, 0, 4, 3), Convex([0, 0, 4, 3])),
        (Triangle(0, 0, 4, 0, 0, 3), Convex([0, 0, 4, 0, 0, 3])),
        (Rectangle(Point(0, 0), Point(4, 3)), Convex([0, 0, 4, 0, 4, 3, 0, 3])),
        (Polyline([0, 0, 3, 4, 6, 0]), Convex([0, 0, 6, 0, 3, 4])),
        (MonotoneChain([0, 0, 3, 4, 6, 0]), Convex([0, 0, 6, 0, 3, 4])),
    ],
)
def test_a_shape_hands_back_its_own_convex_hull(shape, expected):
    hull = shape.convexHull()
    assert isinstance(hull, Convex)
    assert hull.samePointSet(expected)


def test_the_hull_of_a_non_convex_shape_fills_its_dents():
    c = Polygon([0, 0, 6, 0, 6, 2, 2, 2, 2, 4, 6, 4, 6, 6, 0, 6])
    hull = c.convexHull()
    assert hull.contains(c)
    assert hull.area() > c.area()
    assert hull.samePointSet(Rectangle(Point(0, 0), Point(6, 6)))


def test_a_region_takes_the_hull_of_its_outer_boundary():
    # A hole is interior to the outer ring, so it cannot reach the hull.
    ring = PolygonWithHoles(
        Polygon([0, 0, 8, 0, 8, 8, 0, 8]), [Polygon([2, 2, 6, 2, 6, 6, 2, 6])]
    )
    assert ring.convexHull().samePointSet(Rectangle(Point(0, 0), Point(8, 8)))


def test_a_set_takes_the_hull_of_every_component_at_once():
    apart = pypgl.PolygonSet(
        [
            PolygonWithHoles(Polygon([0, 0, 2, 0, 2, 2, 0, 2])),
            PolygonWithHoles(Polygon([8, 8, 10, 8, 10, 10, 8, 10])),
        ]
    )
    hull = apart.convexHull()
    assert hull.samePointSet(Convex([0, 0, 2, 0, 10, 8, 10, 10, 8, 10, 0, 2]))


def test_an_unbounded_convex_shape_has_no_hull_to_give():
    # A HalfplaneIntersection has the method, since a bounded one is a Convex;
    # an unbounded one has no finite vertex set and says so.
    assert HalfplaneIntersection(Rectangle(Point(0, 0), Point(4, 4))).convexHull(
    ).samePointSet(Rectangle(Point(0, 0), Point(4, 4)))
    with pytest.raises(Exception):
        HalfplaneIntersection().convexHull()


def test_the_shapes_with_no_hull_do_not_pretend_to_have_one():
    # The four unbounded shapes have no bbox to begin with, and a Disk's hull
    # is itself and is no polygon -- so none of them carries the method.
    for shape in (
        pypgl.Line(Point(0, 0), Point(1, 0)),
        pypgl.OrientedLine(Point(0, 0), Point(1, 0)),
        pypgl.Ray(Point(0, 0), Point(1, 0)),
        pypgl.Halfplane(Point(0, 0), Point(1, 0)),
        pypgl.Disk(Point(0, 0), 2),
    ):
        assert not hasattr(shape, "convexHull")


# --- monotone chain counts --------------------------------------------------

def test_a_convex_boundary_breaks_into_two_chains():
    # Lexicographically monotone chains: a convex ring turns from increasing to
    # decreasing exactly once, so it splits at its two extreme vertices.
    assert Polygon([0, 0, 4, 0, 4, 4, 0, 4]).chainCount() == 2
    assert Polygon([0, 0, 6, 0, 3, 5]).chainCount() == 2


def test_a_jagged_boundary_breaks_into_more():
    # Each tooth reverses the boundary in x twice, so a comb with three of them
    # costs six chains where its bounding box costs two. That count is what the
    # containment and intersection tests price themselves on.
    comb = Polygon([0, 0, 10, 0, 10, 10, 8, 10, 8, 3, 6, 3,
                    6, 10, 4, 10, 4, 3, 2, 3, 2, 10, 0, 10])
    assert comb.isSimple()
    assert comb.chainCount() == 6
    assert comb.bbox().asPolygon().chainCount() == 2


def test_a_region_counts_the_chains_of_every_ring():
    outer = Polygon([0, 0, 8, 0, 8, 8, 0, 8])
    hole = Polygon([2, 2, 6, 2, 6, 6, 2, 6])
    region = PolygonWithHoles(outer, [hole])
    assert region.chainCount() == outer.chainCount() + hole.chainCount()
