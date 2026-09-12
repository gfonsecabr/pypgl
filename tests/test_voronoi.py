"""Voronoi, farthest-point and power diagrams.

Every diagram is an arrangement whose faces carry the sites that own them, so
the one property worth pinning down is the defining one: locating a query and
reading the label answers the nearest- (farthest-, k-nearest-) site question.
Each test checks that against brute force, over queries offset off the integer
lattice so that none of them lands on a diagram edge, where the answer ties.

The order-k and power diagrams have label types of their own and therefore
classes of their own, but they share one family of handles with Arrangement --
which is what the handle tests at the end pin.
"""

from fractions import Fraction
import random

import pytest

from pypgl import (
    Arrangement,
    ArrangementGraph,
    Disk,
    DiskArrangement,
    DiskListArrangement,
    FaceId,
    HalfedgeId,
    OrientedSegment,
    Point,
    PointListArrangement,
    Triangulation,
    VertexId,
    farthestVoronoiDiagram,
    powerDiagram,
    voronoiDiagram,
)


def _sites(n=12, seed=7):
    rng = random.Random(seed)
    seen = set()
    while len(seen) < n:
        seen.add((rng.randint(-20, 20), rng.randint(-20, 20)))
    return [Point(x, y) for x, y in sorted(seen)]


def _queries():
    # Offsets with incommensurable denominators keep every query off the
    # bisectors of integer sites, so the brute-force answer is strict.
    return [Point(Fraction(40 * i + 1, 7), Fraction(35 * j + 1, 11)) for i in range(-6, 6) for j in range(-6, 6)]


def _sq(p, q):
    return (p.x() - q.x()) ** 2 + (p.y() - q.y()) ** 2


def _power(disk, q):
    return _sq(disk.center(), q) - disk.squaredRadius()


def _least(values, k=1):
    """Positions of the k least values, in position order, or None on a tie.

    A query that does not separate the k least strictly from the rest lies on a
    diagram edge, where the located face is one of several correct answers.
    The off-lattice queries make that rare, and the callers skip it.
    """
    order = sorted(range(len(values)), key=values.__getitem__)
    if k < len(values) and values[order[k - 1]] == values[order[k]]:
        return None
    return sorted(order[:k])


def _pick(items, positions, k=None):
    """The items at positions: one item when k is None, else a list of them."""
    if positions is None:
        return None
    return items[positions[0]] if k is None else [items[i] for i in positions]


def _checked(pairs):
    """Assert each (located, expected) pair that is not a tie; most must count."""
    compared = 0
    for located, expected in pairs:
        if expected is not None:
            assert located == expected
            compared += 1
    assert compared >= 0.9 * len(_queries())


# --- the ordinary diagram ------------------------------------------------------

def test_voronoi_diagram_labels_each_face_with_the_nearest_site():
    sites = _sites()
    diagram = voronoiDiagram(sites)
    assert isinstance(diagram, Arrangement)
    assert diagram.faceCount() == len(sites)
    diagram.buildPointLocation()
    _checked(
        (diagram.label(diagram.locateFace(q)), _pick(sites, _least([_sq(s, q) for s in sites])))
        for q in _queries())


def test_voronoi_diagram_agrees_with_the_triangulation_dual():
    sites = _sites()
    ours = voronoiDiagram(sites)
    dual = Triangulation(sites).voronoiDiagram()
    assert (ours.vertexCount(), ours.edgeCount(), ours.faceCount()) == (
        dual.vertexCount(), dual.edgeCount(), dual.faceCount())
    for q in _queries():
        assert ours.label(ours.locateFace(q)) == dual.label(dual.locateFace(q))


def test_voronoi_diagram_of_collinear_sites_is_a_set_of_parallel_lines():
    sites = [Point(0, 0), Point(2, 0), Point(6, 0)]
    diagram = voronoiDiagram(sites)
    assert diagram.faceCount() == 3
    assert diagram.label(diagram.locateFace(Point(3, 5))) == Point(2, 0)
    assert diagram.label(diagram.locateFace(Point(5, -5))) == Point(6, 0)


def test_voronoi_diagram_of_one_site_is_the_whole_plane():
    diagram = voronoiDiagram([Point(3, 4)])
    assert (diagram.edgeCount(), diagram.faceCount()) == (0, 1)
    assert diagram.label(diagram.locateFace(Point(-100, 7))) == Point(3, 4)


def test_voronoi_diagram_without_sites_raises():
    with pytest.raises(ValueError):
        voronoiDiagram([])


# --- the order-k diagram -------------------------------------------------------

@pytest.mark.parametrize("k", [1, 2, 3])
def test_order_k_diagram_labels_each_face_with_the_k_nearest_sites_in_input_order(k):
    sites = _sites()
    rng = random.Random(k)
    rng.shuffle(sites)  # the label order is the input order, not a sorted one
    diagram = voronoiDiagram(sites, k)
    assert isinstance(diagram, PointListArrangement)
    diagram.buildPointLocation()
    _checked(
        (diagram.label(diagram.locateFace(q)), _pick(sites, _least([_sq(s, q) for s in sites], k), k))
        for q in _queries())


def test_order_one_through_the_order_k_overload_matches_the_ordinary_diagram():
    sites = _sites()
    ordinary = voronoiDiagram(sites)
    listed = voronoiDiagram(sites, 1)
    assert isinstance(listed, PointListArrangement)
    assert listed.faceCount() == ordinary.faceCount()
    for q in _queries():
        assert listed.label(listed.locateFace(q)) == [ordinary.label(ordinary.locateFace(q))]


def test_order_n_diagram_is_one_face_owned_by_every_site():
    sites = _sites(5)
    diagram = voronoiDiagram(sites, len(sites))
    assert diagram.faceCount() == 1
    assert diagram.label(diagram.locateFace(Point(0, 0))) == sites


@pytest.mark.parametrize("k", [0, 13, -1])
def test_order_out_of_range_raises(k):
    with pytest.raises(ValueError):
        voronoiDiagram(_sites(), k)


def test_order_k_diagram_of_collinear_sites_takes_the_bisector_route():
    sites = [Point(0, 0), Point(1, 0), Point(3, 0), Point(7, 0)]
    diagram = voronoiDiagram(sites, 2)
    # Order-2 cells along a line: {0,1}, {1,3}, {3,7} -- three strips.
    assert diagram.faceCount() == 3
    assert diagram.label(diagram.locateFace(Point(2, 9))) == [Point(1, 0), Point(3, 0)]


# --- the farthest-point diagram ------------------------------------------------

def test_farthest_diagram_labels_each_face_with_the_farthest_site():
    sites = _sites()
    diagram = farthestVoronoiDiagram(sites)
    assert isinstance(diagram, Arrangement)
    diagram.buildPointLocation()
    _checked(
        (diagram.label(diagram.locateFace(q)), _pick(sites, _least([-_sq(s, q) for s in sites])))
        for q in _queries())


def test_farthest_diagram_cells_are_unbounded_and_owned_by_hull_vertices():
    sites = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10), Point(5, 5), Point(5, 0)]
    diagram = farthestVoronoiDiagram(sites)
    assert diagram.faceCount() == 4  # the interior and the edge-interior sites own nothing
    assert all(diagram.isUnbounded(FaceId(f)) for f in range(diagram.faceCount()))
    owners = {diagram.label(FaceId(f)) for f in range(diagram.faceCount())}
    assert owners == {Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)}


def test_farthest_diagram_without_sites_raises():
    with pytest.raises(ValueError):
        farthestVoronoiDiagram([])


# --- power diagrams ------------------------------------------------------------

def _disks():
    return [
        Disk(Point(0, 0), 3),
        Disk(Point(9, 1), 5),
        Disk(Point(3, 8), 2),
        Disk(Point(-6, 5), 4),
        Disk(Point(5, -7), 1),
        Disk(Point(-4, -6), 3),
    ]


def test_power_diagram_labels_each_face_with_the_disk_of_least_power():
    disks = _disks()
    diagram = powerDiagram(disks)
    assert isinstance(diagram, DiskArrangement)
    _checked(
        (diagram.label(diagram.locateFace(q)), _pick(disks, _least([_power(d, q) for d in disks])))
        for q in _queries())


@pytest.mark.parametrize("k", [1, 2, 4])
def test_order_k_power_diagram_labels_each_face_with_the_k_least_powers(k):
    disks = _disks()
    diagram = powerDiagram(disks, k)
    assert isinstance(diagram, DiskListArrangement)
    _checked(
        (diagram.label(diagram.locateFace(q)), _pick(disks, _least([_power(d, q) for d in disks], k), k))
        for q in _queries())


def test_power_diagram_of_equal_disks_is_the_voronoi_diagram_of_their_centers():
    centers = _sites(8)
    power = powerDiagram([Disk(c, 2) for c in centers])
    voronoi = voronoiDiagram(centers)
    assert power.faceCount() == voronoi.faceCount()
    for q in _queries():
        assert power.label(power.locateFace(q)).center() == voronoi.label(voronoi.locateFace(q))


def test_a_swallowed_disk_owns_no_cell():
    big, small = Disk(Point(0, 0), 10), Disk(Point(1, 0), 1)
    diagram = powerDiagram([big, small, Disk(Point(30, 0), 2)])
    labels = [diagram.label(FaceId(f)) for f in range(diagram.faceCount())]
    assert small not in labels
    assert big in labels


def test_power_diagram_is_exact_for_a_disk_with_an_irrational_radius():
    # Through three points: squared radius 25/2, radius irrational.
    through = Disk(Point(0, 0), Point(5, 0), Point(0, 5))
    other = Disk(Point(12, 0), 1)
    diagram = powerDiagram([through, other])
    assert diagram.faceCount() == 2
    # The one edge is the radical axis: both disks have the same power on it.
    (edge,) = diagram.edges()
    for p in (edge.min(), edge.max()):
        assert _power(through, p) == _power(other, p)


def test_power_diagram_without_sites_raises():
    with pytest.raises(ValueError):
        powerDiagram([])
    with pytest.raises(ValueError):
        powerDiagram(_disks(), 7)


# --- one handle family across every label type ---------------------------------

@pytest.mark.parametrize("build", [
    lambda: voronoiDiagram(_sites(), 2),
    lambda: powerDiagram(_disks()),
    lambda: powerDiagram(_disks(), 2),
])
def test_every_diagram_class_speaks_the_same_handles(build):
    diagram = build()
    q = Point(Fraction(1, 3), Fraction(1, 7))
    face = diagram.locateFace(q)
    assert type(face) is FaceId
    assert isinstance(diagram.locateCell(q), FaceId)
    for h in diagram.boundaryOf(face):
        assert type(h) is HalfedgeId
        assert diagram.face(h) == face
        assert type(diagram.source(h)) is VertexId
        assert diagram.twin(diagram.twin(h)) == h
    assert isinstance(diagram.asGraph(), ArrangementGraph)
    assert diagram.asGraph().vertexCount() >= diagram.vertexCount()
    if diagram.isUnbounded(face):
        assert not diagram.outerCycle(face)


def test_curve_tracing_reports_python_handles_on_a_list_labelled_diagram():
    diagram = voronoiDiagram(_sites(), 2)
    cells = diagram.reportIntersecting(OrientedSegment(Point(-30, 1), Point(30, 1)))
    assert cells and all(type(c) in (HalfedgeId, VertexId) for c in cells)
    first = diagram.firstIntersecting(OrientedSegment(Point(-30, 1), Point(30, 1)))
    assert first == cells[0]


def test_set_label_on_a_list_labelled_diagram():
    diagram = voronoiDiagram(_sites(), 2)
    face = diagram.locateFace(Point(0, 0))
    diagram.setLabel(face, [Point(1, 2)])
    assert diagram.label(face) == [Point(1, 2)]


# --- Triangulation.voronoiEdges ------------------------------------------------

def test_voronoi_edges_are_the_edges_of_the_diagram():
    sites = _sites()
    triangulation = Triangulation(sites)
    loose = triangulation.voronoiEdges()
    assembled = triangulation.voronoiDiagram().edges()
    assert len(loose) == len(assembled)
    for piece in loose:
        assert sum(piece.samePointSet(edge) for edge in assembled) == 1
