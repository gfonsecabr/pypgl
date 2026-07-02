"""Triangulation: a mutable mesh over a fixed vertex set.

Unlike every other bound type, Triangulation is not a fixed-extent "shape" --
it has no contains(Point)/pointInside/index/get -- so it deliberately opts out
of the point-in-shape (`in`) and indexing (`len`/`[]`/iteration) sugar every
other class gets in pypgl/__init__.py and the generated stub. This file covers
its own surface instead: the four construction modes (explicit triangle set,
explicit edge set, Delaunay from points, constrained Delaunay from a Polygon
with optional extra points/segments), sizes, membership, navigation queries,
the directed/region traversal matrix, point location, constrained edges,
flipping (single and batch), invariants, and Canvas rendering.
"""

from fractions import Fraction

import pytest

import pypgl
from pypgl import (
    Canvas,
    Convex,
    Disk,
    Halfplane,
    Line,
    OrientedLine,
    OrientedSegment,
    Point,
    Polygon,
    Ray,
    Rectangle,
    Segment,
    Triangle,
    Triangulation,
)


def _square_points():
    return [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]


def _square_polygon():
    return Polygon(_square_points())


# --- importability, construction --------------------------------------------

def test_triangulation_importable_and_in_all():
    assert hasattr(pypgl, "Triangulation")
    assert "Triangulation" in pypgl.__all__


def test_empty_triangulation():
    t = Triangulation()
    assert t.empty()
    assert t.numVertices() == 0
    assert t.numTriangles() == 0
    assert t.numEdges() == 0
    assert t.triangles() == []
    assert t.edges() == []


def test_delaunay_from_points():
    t = Triangulation(_square_points() + [Point(2, 2)])
    assert t.numVertices() == 5
    assert t.numTriangles() == 4
    assert not t.empty()


def test_from_explicit_triangle_set():
    tris = Triangulation(_square_points()).triangles()
    t = Triangulation(tris)
    assert sorted(t.triangles(), key=repr) == sorted(tris, key=repr)


def test_from_explicit_edge_set():
    edges = Triangulation(_square_points()).edges()
    t = Triangulation(edges)
    assert t.numTriangles() == 2


def test_from_polygon_constrained():
    t = Triangulation(_square_polygon())
    assert t.numTriangles() == 2
    assert t.numVertices() == 4


def test_from_polygon_with_extra_points():
    t = Triangulation(_square_polygon(), points=[Point(2, 2)])
    assert t.numVertices() == 5
    assert t.numTriangles() == 4


def test_from_polygon_with_constraint_segments():
    t = Triangulation(_square_polygon(), segments=[Segment(Point(0, 0), Point(4, 4))])
    assert t.isConstrained(Segment(Point(0, 0), Point(4, 4)))


def test_from_polygon_with_points_and_segments():
    t = Triangulation(
        _square_polygon(),
        points=[Point(2, 2)],
        segments=[Segment(Point(0, 0), Point(2, 2))],
    )
    assert t.isConstrained(Segment(Point(0, 0), Point(2, 2)))
    assert t.numVertices() == 5


def test_coordinates_accept_fraction_and_string():
    t = Triangulation([Point(Fraction(1, 2), 0), Point("3/2", 0), Point(1, 1)])
    assert t.numTriangles() == 1


def test_float_coordinates_are_rejected():
    with pytest.raises(TypeError):
        Point(0.0, 0)


# --- sizes, membership -------------------------------------------------------

def test_sizes_match_a_triangulated_square():
    t = Triangulation(_square_points())
    assert t.numVertices() == 4
    assert t.numTriangles() == 2
    assert t.numEdges() == 5  # 4 boundary + 1 diagonal


def test_contains_triangle_and_edge():
    t = Triangulation(_square_points())
    tri = t.triangles()[0]
    assert t.contains(tri)
    assert not t.contains(Triangle(Point(100, 100), Point(101, 100), Point(100, 101)))

    edge = t.edges()[0]
    assert t.contains(edge)
    assert not t.contains(Segment(Point(100, 100), Point(101, 101)))


# --- navigation ---------------------------------------------------------------

def test_edge_and_vertex_adjacent_triangles():
    t = Triangulation(_square_points())
    tri = t.triangles()[0]
    edge_adj = t.edgeAdjacentTriangles(tri)
    vertex_adj = t.vertexAdjacentTriangles(tri)
    assert set(edge_adj) <= set(vertex_adj)
    assert tri not in vertex_adj


def test_other_triangle_across_shared_edge():
    t = Triangulation(_square_points())
    tri = t.triangles()[0]
    shared = t.edgeAdjacentTriangles(tri)
    assert len(shared) == 1
    other = shared[0]
    diag = [e for e in tri.edges() if t.otherTriangle(tri, e) is not None][0]
    assert t.otherTriangle(tri, diag) == other
    assert t.otherTriangle(other, diag) == tri


def test_incident_triangles_by_vertex_and_edge():
    t = Triangulation(_square_points())
    assert len(t.incidentTriangles(Point(0, 0))) >= 1
    assert t.incidentTriangles(Point(1000, 1000)) == []
    edge = t.edges()[0]
    assert 1 <= len(t.incidentTriangles(edge)) <= 2


# --- traversal: directed and region queries ----------------------------------

def test_triangles_intersecting_segment_and_line():
    t = Triangulation(_square_points())
    seg = Segment(Point(-1, -1), Point(5, 5))
    hit = t.trianglesIntersecting(seg)
    assert len(hit) == 2  # crosses both triangles of the square
    assert t.trianglesIntersecting(Line(Point(-1, -1), Point(5, 5))) != []


def test_triangles_intersecting_region_shapes():
    t = Triangulation(_square_points())
    # (1, 3) is strictly on one side of the (0,0)-(4,4) diagonal, so it meets
    # exactly one triangle; (1, 1) would sit exactly on the diagonal itself.
    assert len(t.trianglesIntersecting(Point(1, 3))) == 1
    assert len(t.trianglesIntersecting(Rectangle(Point(0, 0), Point(4, 4)))) == 2
    assert len(t.trianglesIntersecting(Disk(2, 2, 1))) >= 1
    assert len(t.trianglesIntersecting(Convex(_square_points()))) == 2
    assert len(t.trianglesIntersecting(Halfplane(Point(0, 0), Point(0, 4)))) >= 1


def test_interior_intersecting_excludes_boundary_only_touches():
    t = Triangulation(_square_points())
    # A point exactly on the shared diagonal touches both triangles' boundaries
    # but is interior to neither.
    diag_point = t.edgeAdjacentTriangles(t.triangles()[0])
    assert t.trianglesInteriorIntersecting(Point(4, 4)) == []


def test_edges_intersecting_and_interior_intersecting():
    t = Triangulation(_square_points())
    seg = Segment(Point(-1, 2), Point(5, 2))
    all_hit = t.edgesIntersecting(seg)
    interior_hit = t.edgesInteriorIntersecting(seg)
    assert set(interior_hit) <= set(all_hit)


def test_directed_query_types_all_accepted():
    t = Triangulation(_square_points())
    p1, p2 = Point(-1, -1), Point(5, 5)
    for query in (
        Segment(p1, p2),
        OrientedSegment(p1, p2),
        Line(p1, p2),
        OrientedLine(p1, p2),
        Ray(p1, p2),
    ):
        assert t.trianglesIntersecting(query) != []


# --- point location ------------------------------------------------------------

def test_locate_inside_and_outside():
    t = Triangulation(_square_points())
    assert t.locate(Point(2, 2)) is not None
    assert t.locate(Point(100, 100)) is None
    assert t.locate(Point(2, 2)) in t.triangles()


def test_locate_on_empty_triangulation():
    assert Triangulation().locate(Point(0, 0)) is None


# --- constrained edges ----------------------------------------------------------

def test_is_constrained_reflects_polygon_boundary():
    t = Triangulation(_square_polygon())
    boundary_edge = Segment(Point(0, 0), Point(4, 0))
    assert t.isConstrained(boundary_edge)


def test_set_constrained_toggles_flag():
    t = Triangulation(_square_points())
    edge = t.edges()[0]
    assert not t.isConstrained(edge)
    t.setConstrained(edge, True)
    assert t.isConstrained(edge)
    t.setConstrained(edge, False)
    assert not t.isConstrained(edge)
    # Default value is True.
    t.setConstrained(edge)
    assert t.isConstrained(edge)


# --- flipping ---------------------------------------------------------------

def test_flip_single_edge_round_trips():
    t = Triangulation(_square_points())
    diag = [e for e in t.triangles()[0].edges() if t.flippable(e)]
    assert len(diag) == 1
    diag = diag[0]
    new_diag = t.flip(diag)
    assert new_diag is not None
    assert not t.contains(diag)
    assert t.contains(new_diag)
    # Flipping back restores the original diagonal.
    assert t.flip(new_diag) == diag


def test_flip_non_flippable_boundary_edge_returns_none():
    t = Triangulation(_square_points())
    boundary_edge = Segment(Point(0, 0), Point(4, 0))
    assert not t.flippable(boundary_edge)
    assert t.flip(boundary_edge) is None


def test_batch_flip_all_or_nothing():
    t = Triangulation(_square_points())
    diag = [e for e in t.triangles()[0].edges() if t.flippable(e)][0]
    boundary_edge = Segment(Point(0, 0), Point(4, 0))
    assert t.flippable([diag]) is True
    assert t.flippable([boundary_edge]) is False
    assert t.flip([boundary_edge]) is None

    result = t.flip([diag])
    assert len(result) == 1
    assert diag not in t.edges()
    assert result[0] in t.edges()


# --- validation, repr ---------------------------------------------------------

def test_check_invariants_holds_after_mutation():
    t = Triangulation(_square_points())
    assert t.checkInvariants()
    diag = [e for e in t.triangles()[0].edges() if t.flippable(e)][0]
    t.flip(diag)
    assert t.checkInvariants()


def test_repr_reports_sizes():
    t = Triangulation(_square_points())
    r = repr(t)
    assert "numVertices=4" in r
    assert "numTriangles=2" in r


# --- no shape sugar -----------------------------------------------------------

def test_triangulation_has_no_point_sugar():
    t = Triangulation(_square_points())
    assert not hasattr(t, "__len__")
    assert not hasattr(t, "__getitem__")
    assert not hasattr(t, "__contains__")
    assert not hasattr(t, "__iter__")


# --- Canvas / inline rendering --------------------------------------------------

def test_canvas_draw_triangulation():
    t = Triangulation(_square_points())
    svg = Canvas().draw(t).toSVG()
    assert "<svg" in svg


def test_repr_svg():
    t = Triangulation(_square_points())
    svg = t._repr_svg_()
    assert "<svg" in svg
