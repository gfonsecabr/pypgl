"""Arrangement: the subdivision of the plane induced by segments, rays and lines.

Two things about it are worth pinning down here. Its vertices are *constructed*
points -- two integer segments generally cross at a rational one -- which is
exactly the case pypgl's single exact instantiation handles without a caveat.
And its cells are named by strongly typed handles, so locateCell() can answer
"the cell containing this point" as whichever of the three kinds it is.
"""

from fractions import Fraction

import pytest

from pypgl import (
    Arrangement,
    ArrangementGraph,
    FaceId,
    HalfedgeId,
    Line,
    MonotoneChain,
    OrientedSegment,
    Point,
    Polygon,
    PolygonWithHoles,
    Ray,
    Rectangle,
    Segment,
    Triangulation,
    VertexId,
)


def _cross():
    """Two segments crossing at (2, 2)."""
    return Arrangement([Segment(0, 0, 4, 4), Segment(0, 4, 4, 0)])


def _square_boundary():
    return Arrangement(
        [Segment(0, 0, 4, 0), Segment(4, 0, 4, 4), Segment(4, 4, 0, 4), Segment(0, 4, 0, 0)]
    )


# --- construction and counts ------------------------------------------------

def test_a_crossing_splits_both_segments():
    a = _cross()
    assert a.vertexCount() == 5              # four endpoints plus the crossing
    assert a.edgeCount() == 4
    assert a.halfedgeCount() == 8
    assert a.faceCount() == 1                # nothing encloses anything
    assert not a.isUnbounded()               # no unbounded *edge*
    assert Point(2, 2) in a.vertices()


def test_a_closed_boundary_encloses_a_face():
    a = _square_boundary()
    assert a.faceCount() == 2                # the inside and the outside
    inside = a.locateFace(Point(2, 2))
    assert not a.isUnbounded(inside)
    assert a.isUnbounded(FaceId(0))          # face 0 is always unbounded
    assert a.polygonWithHoles(inside).area() == 16
    assert a.witness(inside) in Rectangle(Point(0, 0), Point(4, 4))


def test_lines_reach_the_symbolic_vertex_at_infinity():
    a = Arrangement([Line(Point(0, 0), Point(1, 0)), Line(Point(0, 0), Point(0, 1))])
    assert a.isUnbounded()
    assert a.vertexCount() == 1              # the origin; infinity is not counted
    assert a.faceCount() == 4                # the four quadrants
    # The infinity vertex's handle index is exactly the finite vertex count.
    assert a.isFictitious(VertexId(a.vertexCount()))
    with pytest.raises(Exception):
        a.position(VertexId(a.vertexCount()))


def test_extra_points_become_vertices_wherever_they_fall():
    segments = [Segment(0, 0, 4, 0)]
    on_nothing = Arrangement(segments, [Point(9, 9)])
    assert on_nothing.vertexCount() == 3
    on_the_segment = Arrangement(segments, [Point(2, 0)])
    assert on_the_segment.vertexCount() == 3
    assert on_the_segment.edgeCount() == 2   # the point split it


def test_the_empty_arrangement_is_one_unbounded_face():
    a = Arrangement()
    assert a.vertexCount() == a.edgeCount() == 0
    assert a.faceCount() == 1
    assert a.halfplaneIntersection(FaceId(0)).isPlane()


# --- exactness --------------------------------------------------------------

def test_integer_input_crosses_at_an_exact_rational_vertex():
    a = Arrangement([Segment(0, 0, 3, 1), Segment(0, 1, 1, 0)])
    off_lattice = [v for v in a.vertices() if v.x().denominator != 1]
    assert off_lattice == [Point(Fraction(3, 4), Fraction(1, 4))]


# --- handles ----------------------------------------------------------------

def test_locate_cell_names_the_kind_of_cell_a_point_is_in():
    a = _cross()
    assert isinstance(a.locateCell(Point(2, 2)), VertexId)     # the crossing
    assert isinstance(a.locateCell(Point(1, 1)), HalfedgeId)   # on an edge
    assert isinstance(a.locateCell(Point(0, 3)), FaceId)       # off everything


def test_a_handle_family_is_its_own_type():
    assert VertexId(2) == VertexId(2)
    assert VertexId(2) != VertexId(3)
    assert not VertexId().valid() and not bool(VertexId())
    assert VertexId(2).index() == 2
    assert len({VertexId(1), VertexId(1), VertexId(2)}) == 2    # hashable
    assert repr(FaceId(3)) == "FaceId(3)"


def test_point_location_can_be_indexed_without_changing_the_answers():
    a = _square_boundary()
    before = a.locateFace(Point(2, 2))
    assert not a.hasPointLocation()
    a.buildPointLocation()
    assert a.hasPointLocation()
    assert a.locateFace(Point(2, 2)) == before
    a.clearPointLocation()
    assert not a.hasPointLocation()


# --- topology ---------------------------------------------------------------

def test_twins_next_and_endpoints_walk_a_boundary_cycle():
    a = _square_boundary()
    inside = a.locateFace(Point(2, 2))
    cycle = a.outerBoundaryOf(inside)
    assert len(cycle) == 4
    assert a.hasSimpleBoundary(inside)
    assert all(a.face(h) == inside for h in cycle)
    # next() walks the cycle back to where it started.
    h = cycle[0]
    for _ in range(4):
        h = a.next(h)
    assert h == cycle[0]
    assert a.target(cycle[0]) == a.source(a.next(cycle[0]))
    assert a.twin(a.twin(cycle[0])) == cycle[0]


def test_edges_and_halfedges_come_back_as_ordinary_shapes():
    a = _cross()
    assert all(isinstance(e, Segment) for e in a.edges())
    assert len(a.boundedEdges()) == 4
    assert isinstance(a.halfedge(HalfedgeId(0)), OrientedSegment)
    unbounded = Arrangement([Line(Point(0, 0), Point(1, 0))])
    assert all(isinstance(e, Line) for e in unbounded.edges())
    assert unbounded.boundedEdges() == []


def test_a_vertex_knows_the_edges_leaving_it():
    a = _cross()
    crossing = VertexId(a.vertices().index(Point(2, 2)))
    assert a.degree(crossing) == 4
    assert len(a.outgoingHalfedges(crossing)) == 4
    assert all(a.source(h) == crossing for h in a.outgoingHalfedges(crossing))


def test_origins_say_which_input_shape_produced_a_cell():
    a = Arrangement([Segment(0, 0, 4, 0), Segment(2, -2, 2, 2)])
    crossing = VertexId(a.vertices().index(Point(2, 0)))
    assert a.originsOf(crossing) == [0, 1]      # both inputs pass through it


# --- labels -----------------------------------------------------------------

def test_a_face_label_records_a_classification_per_cell():
    a = _square_boundary()
    inside = a.locateFace(Point(2, 2))
    assert a.label(inside) == Point(0, 0)       # default-constructed
    a.setLabel(inside, Point(7, 7))
    assert a.label(inside) == Point(7, 7)


# --- tracing a curve through the cells --------------------------------------

def test_a_directed_curve_reports_the_cells_it_meets_in_order():
    a = _square_boundary()
    crossing = OrientedSegment(Point(-1, 2), Point(5, 2))
    met = a.reportIntersecting(crossing)
    assert len(met) == 2                        # the left wall, then the right
    assert a.firstIntersecting(crossing) == met[0]
    assert not a.emptyIntersecting(crossing)
    assert a.emptyIntersecting(OrientedSegment(Point(-9, -9), Point(-8, -8)))


def test_a_chain_is_traced_edge_by_edge():
    a = _square_boundary()
    chain = MonotoneChain([Point(-1, 2), Point(2, 2), Point(5, 2)])
    assert len(a.reportIntersecting(chain)) == 2


# --- the combinatorial view -------------------------------------------------

def test_as_graph_is_keyed_by_handles_not_points():
    a = _square_boundary()
    g = a.asGraph()
    assert isinstance(g, ArrangementGraph)
    assert g.vertexCount() == a.vertexCount()
    assert g.edgeCount() == a.edgeCount()
    assert VertexId(0) in g


def test_a_lines_two_ends_are_the_same_vertex_so_it_carries_no_graph_edge():
    a = Arrangement([Line(Point(0, 0), Point(1, 1))])
    assert a.isUnbounded()
    g = a.asGraph()
    assert g.vertexCount() == 1                 # only the infinity vertex
    assert g.edgeCount() == 0                   # a self-loop is not an edge


# --- the Voronoi diagram is an arrangement ----------------------------------

def test_a_voronoi_diagram_labels_each_face_with_its_site():
    sites = [Point(0, 0), Point(10, 0), Point(0, 10), Point(10, 10)]
    diagram = Triangulation(sites).voronoiDiagram()
    assert isinstance(diagram, Arrangement)
    assert diagram.isUnbounded()
    for site in sites:
        # Every site lies in its own cell, so it is the nearest one to itself.
        assert diagram.label(diagram.locateFace(site)) == site
    # A query point nearer one site than the others lands in that site's cell.
    assert diagram.label(diagram.locateFace(Point(1, 2))) == Point(0, 0)


def test_a_face_can_be_read_back_as_a_region():
    a = Arrangement([Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])])
    inside = a.locateFace(Point(2, 2))
    region = a.polygonWithHoles(inside)
    assert isinstance(region, PolygonWithHoles)
    assert region.area() == 16
    with pytest.raises(Exception):
        a.polygonWithHoles(FaceId(0))           # unbounded


def test_a_ray_has_one_finite_end():
    a = Arrangement([Ray(Point(0, 0), Point(1, 0))])
    assert a.vertexCount() == 1
    assert a.isUnbounded()
    assert a.isUnbounded(HalfedgeId(0))
