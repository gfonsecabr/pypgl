"""Polygon: an arbitrary (possibly non-convex) simple polygon.

Mirrors Convex's storage (vertices + a lazy translation) but makes no
convexity assumption, so it is mutable/unhashable the same way. Covers
construction (trusted vs. normalized), measures, isSimple/isConvex/untangle,
indexing, mutability, transforms, the predicate/squared-distance matrix
(including against Disk, which sits outside the shared matrix macro), and
intersection (list-of-pieces results, unlike Convex's single optional piece).
"""

from fractions import Fraction

import pytest

import pypgl
from pypgl import Convex, Disk, Point, Polygon, Rectangle, Segment, Triangle


def _square():
    return Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])


# --- importability, construction ------------------------------------------

def test_polygon_importable_and_in_all():
    assert hasattr(pypgl, "Polygon")
    assert "Polygon" in pypgl.__all__


def test_empty_polygon():
    p = Polygon()
    assert p.size() == 0
    assert list(p) == []


def test_construction_normalizes_to_ccw_lex_min_first():
    # Given clockwise / rotated, normalization reorders to CCW starting at
    # the lexicographically smallest vertex.
    p = Polygon([Point(4, 4), Point(0, 4), Point(0, 0), Point(4, 0)])
    assert p == _square()
    assert p.vertices()[0] == Point(0, 0)


def test_trusted_skips_normalization():
    # Already-canonical vertices given with trusted=True are stored as-is.
    p = Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)], trusted=True)
    assert p.vertices() == [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]


def test_coordinates_accept_fraction_and_string():
    p = Polygon([Point(Fraction(1, 2), 0), Point("3/2", 0), Point(1, 1)])
    assert p.area() == Fraction(1, 2)


def test_float_coordinates_are_rejected():
    with pytest.raises(TypeError):
        Polygon([Point(0.0, 0), Point(1, 0), Point(1, 1)])


# --- measures ---------------------------------------------------------------

def test_area_and_twice_area_are_exact():
    p = _square()
    assert p.area() == 16
    assert isinstance(p.area(), Fraction)
    assert p.twiceArea() == 32


def test_centroid_and_vertices_centroid():
    p = _square()
    assert p.centroid() == Point(2, 2)
    assert p.verticesCentroid() == Point(2, 2)


def test_isDegenerate_for_collinear_points():
    p = Polygon([Point(0, 0), Point(1, 0), Point(2, 0)])
    assert p.isDegenerate()
    assert p.area() == 0


def test_isSimple_and_isConvex():
    square = _square()
    assert square.isSimple()
    assert square.isConvex()

    # A self-crossing "bowtie" quadrilateral is not simple.
    bowtie = Polygon([Point(0, 0), Point(2, 2), Point(2, 0), Point(0, 2)], trusted=True)
    assert not bowtie.isSimple()

    # An L-shape is simple but not convex.
    ell = Polygon([Point(0, 0), Point(4, 0), Point(4, 2), Point(2, 2), Point(2, 4), Point(0, 4)])
    assert ell.isSimple()
    assert not ell.isConvex()


def test_untangle_makes_bowtie_simple():
    bowtie = Polygon([Point(0, 0), Point(2, 2), Point(2, 0), Point(0, 2)], trusted=True)
    assert not bowtie.isSimple()
    assert bowtie.untangle() is None  # in-place mutator returns None
    assert bowtie.isSimple()


def test_diameter_and_bbox():
    p = _square()
    assert p.diameter().length() == pytest.approx((4 * 4 + 4 * 4) ** 0.5)
    assert p.bbox() == Rectangle(0, 0, 4, 4)


def test_vertices_edges_orientedEdges():
    p = _square()
    assert p.vertices() == [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]
    assert len(p.edges()) == 4
    assert Segment(0, 0, 4, 0) in p.edges()
    assert len(p.orientedEdges()) == 4


# --- indexing / iteration ----------------------------------------------------

def test_indexing_and_iteration_over_vertices():
    p = _square()
    assert len(p) == 4
    assert p[0] == Point(0, 0)
    assert p[-1] == Point(0, 4)          # cyclic, from the end
    assert p[10] == p[10 % 4]            # cyclic, wraps past size()
    assert list(p) == p.vertices()


def test_index_of_vertex():
    p = _square()
    assert p.index(Point(4, 4)) == 2
    assert p.index(Point(100, 100)) is None


def test_point_in_polygon_sugar():
    p = _square()
    assert Point(2, 2) in p
    assert Point(100, 100) not in p


# --- mutability: mutable + unhashable, like Convex ---------------------------

def test_polygon_is_mutable_and_unhashable():
    p = _square()
    with pytest.raises(TypeError):
        hash(p)
    with pytest.raises(TypeError):
        {p: "label"}


def test_in_place_translation_keeps_identity():
    p = _square()
    before = id(p)
    p += Point(10, 10)
    assert id(p) == before
    assert p == Polygon([Point(10, 10), Point(14, 10), Point(14, 14), Point(10, 14)])


def test_value_returning_operator_is_a_copy():
    p = _square()
    moved = p + Point(10, 10)
    assert moved is not p
    assert p == _square()


def test_in_place_scale_and_transforms():
    p = _square()
    p *= 2
    assert p == Polygon([Point(0, 0), Point(8, 0), Point(8, 8), Point(0, 8)])
    assert p.rotate90() is None
    assert isinstance(_square().rotated90(), Polygon)


# --- predicates: spot-check the shared matrix, including Disk ---------------

def test_predicates_against_point_and_self():
    p = _square()
    assert p.contains(Point(2, 2))
    assert not p.interiorContains(Point(0, 0))   # on the boundary
    assert p.boundaryContains(Point(0, 2))
    assert p.contains(p)
    assert p.intersects(p)


def test_predicates_against_other_bound_shapes():
    p = _square()
    tri = Triangle(Point(-1, -1), Point(10, -1), Point(-1, 10))
    assert tri.contains(p)
    assert p.intersects(tri)
    rect = Rectangle(2, 2, 10, 10)
    assert p.intersects(rect)
    convex = Convex([Point(2, 2), Point(10, 2), Point(10, 10), Point(2, 10)])
    assert p.intersects(convex)


def test_predicates_against_disk_reach_via_polygon_column():
    # Disk sits outside the shared PGL_BIND_ALL_PREDICATES macro, so this pair
    # is bound explicitly on both sides (bind_polygon.cpp and, transitively,
    # bind_disk.cpp's own call to the shared macro).
    p = _square()
    small = Disk(1, 1, Fraction(1, 2))
    assert p.contains(small)
    assert p.intersects(small)
    assert small.intersects(p)
    far = Disk(100, 100, 1)
    assert not p.intersects(far)


# --- squared distance ---------------------------------------------------------

def test_squared_distance_is_exact_fraction():
    p = _square()
    assert p.squaredDistance(Point(4, 0)) == 0
    assert p.squaredDistance(Point(8, 0)) == 16
    assert isinstance(p.squaredDistance(Point(8, 0)), Fraction)


def test_squared_distance_to_disk_is_float():
    p = _square()
    d = Disk(10, 0, 1)
    assert isinstance(p.squaredDistance(d), float)
    assert p.squaredDistance(d) == pytest.approx(25.0)


def test_squared_distance_to_disk_is_symmetric():
    # Disk.squaredDistance(Polygon) reaches Polygon's own implementation via a
    # generic shapeRank-based forwarder on Disk (a pgl gap since fixed).
    p = _square()
    d = Disk(10, 0, 1)
    assert d.squaredDistance(p) == p.squaredDistance(d)
    overlapping = Disk(1, 1, 1)
    assert p.squaredDistance(overlapping) == 0.0
    assert overlapping.squaredDistance(p) == 0.0


# --- intersection: list-of-pieces results ------------------------------------

def test_intersection_with_point():
    p = _square()
    assert p.intersection(Point(2, 2)) == Point(2, 2)
    assert p.intersection(Point(100, 100)) is None


def test_intersection_with_segment_returns_list_of_pieces():
    p = _square()
    seg = Segment(-1, 2, 10, 2)
    pieces = p.intersection(seg)
    assert pieces == [Segment(0, 2, 4, 2)]


def test_point_intersection_with_polygon_via_forwarding():
    # Point.intersection(anything) is always optional[Point]; confirm the
    # Polygon overload was added alongside the other shapes.
    p = _square()
    assert Point(2, 2).intersection(p) == Point(2, 2)
    assert Point(100, 100).intersection(p) is None


def test_intersection_with_convex_returns_polygon_piece():
    p = _square()
    convex = Convex([Point(2, 2), Point(10, 2), Point(10, 10), Point(2, 10)])
    pieces = p.intersection(convex)
    assert len(pieces) == 1
    assert pieces[0] == Polygon([Point(2, 2), Point(4, 2), Point(4, 4), Point(2, 4)])


# --- triangulation() shortcut -------------------------------------------------
# Polygon.triangulation() / triangulation(segments) are equivalent to
# Triangulation(polygon) / Triangulation(polygon, segments=segments) -- see
# tests/test_triangulation.py for Triangulation's own surface.

def test_triangulation_matches_direct_constructor():
    from pypgl import Triangulation

    p = _square()
    assert p.triangulation().numTriangles() == Triangulation(p).numTriangles()


def test_triangulation_with_constraint_segments():
    p = _square()
    diagonal = Segment(Point(0, 0), Point(4, 4))
    t = p.triangulation([diagonal])
    assert t.isConstrained(diagonal)


# --- Canvas / repr ------------------------------------------------------------

def test_repr_and_str():
    p = _square()
    assert repr(p) == str(p)
    assert repr(p).startswith("Polygon[")


def test_canvas_can_draw_polygon():
    p = _square()
    svg = pypgl.Canvas().draw(p).toSVG()
    assert "<svg" in svg
    assert "</svg>" in svg


def test_repr_svg_renders_inline():
    p = _square()
    svg = p._repr_svg_()
    assert "<svg" in svg
