"""PolygonWithHoles: a closed region, an outer simple polygon minus the
*interiors* of a set of pairwise interior-disjoint polygonal holes.

Covers construction and the hole canonicalization, the ring accessors, the
measures (which net the holes out), the structural predicates isValid /
isRegular / isSimple and the regularized() that removes slits, the
triangulation that leaves hole interiors out of the domain, and the Python
container sugar -- which, unlike C++, iterates the region's *vertices* rather
than its holes.

The boolean operations and the Minkowski sum that produce regions live in
test_booleans.py and test_minkowski.py.
"""

from fractions import Fraction

import pytest

import pypgl
from pypgl import (
    Point,
    Polygon,
    PolygonWithHoles,
    Rectangle,
    Segment,
    Triangle,
)


def _square(side=10):
    return Polygon([Point(0, 0), Point(side, 0), Point(side, side), Point(0, side)])


def _hole(lo=4, hi=6):
    return Polygon([Point(lo, lo), Point(hi, lo), Point(hi, hi), Point(lo, hi)])


def _annulus():
    return PolygonWithHoles(_square(), [_hole()])


def _slit_partner():
    """A hole sharing the whole edge x == 3, 1 <= y <= 3 with ``_hole(1, 3)``.

    Two holes meeting along a stretch of edge pinch the region shut there --
    that is a slit. Meeting at a single corner, as ``_hole(1, 3)`` and
    ``_hole(3, 5)`` do, is not.
    """
    return Polygon([Point(3, 1), Point(5, 1), Point(5, 3), Point(3, 3)])


# --- importability, construction ------------------------------------------

def test_region_importable_and_in_all():
    assert hasattr(pypgl, "PolygonWithHoles")
    assert "PolygonWithHoles" in pypgl.__all__


def test_empty_region():
    r = PolygonWithHoles()
    assert r.isEmpty()
    assert not r.hasHoles()
    assert r.holeCount() == 0
    assert r.vertexCount() == 0
    # The empty region is degenerate and has no point or segment to be, so it
    # falls in the undefined bucket.
    assert r.isDegenerate()
    assert r.isUndefined()


def test_hole_free_region_from_polygon():
    r = PolygonWithHoles(_square())
    assert not r.isEmpty()
    assert not r.hasHoles()
    assert r.outer() == _square()
    assert r.area() == 100


def test_region_with_a_hole():
    r = _annulus()
    assert r.holeCount() == 1
    assert r.hasHoles()
    assert r.hole(0) == _hole()
    assert r.holes() == [_hole()]
    assert r.outer() == _square()


def test_hole_order_does_not_affect_identity():
    # The holes are stored in canonical (sorted) order, so the order they are
    # given in is not part of the region's identity.
    a, b = _hole(1, 2), _hole(7, 8)
    assert PolygonWithHoles(_square(), [a, b]) == PolygonWithHoles(_square(), [b, a])


def test_zero_area_hole_is_dropped():
    # A ring with no area removes nothing, so it is not kept.
    flat = Polygon([Point(1, 1), Point(3, 1), Point(2, 1)])
    r = PolygonWithHoles(_square(), [flat])
    assert r.holeCount() == 0
    assert r.area() == 100


def test_region_is_unhashable_because_mutable():
    with pytest.raises(TypeError):
        {_annulus()}


# --- adding and erasing holes ---------------------------------------------

def test_add_and_erase_hole_by_value():
    r = PolygonWithHoles(_square())
    r.addHole(_hole())
    assert r.holeCount() == 1
    assert r.area() == 96
    assert r.eraseHole(_hole()) is True
    assert r.holeCount() == 0
    assert r.area() == 100
    # Erasing one that is not there reports so rather than raising.
    assert r.eraseHole(_hole()) is False


def test_erase_hole_by_index():
    r = PolygonWithHoles(_square(), [_hole(1, 2), _hole(7, 8)])
    r.eraseHole(0)
    assert r.holeCount() == 1
    # Index 0 is the first in canonical order, which is the lower-left hole.
    assert r.hole(0) == _hole(7, 8)


# --- vertices and edges over every ring ------------------------------------

def test_vertex_count_spans_every_ring():
    r = _annulus()
    assert r.vertexCount() == 8  # four outer, four on the hole
    assert len(r.vertices()) == 8
    # The outer boundary comes first.
    assert r.vertices()[:4] == list(_square())


def test_edges_span_every_ring():
    r = _annulus()
    assert len(r.edges()) == 8
    assert len(r.orientedEdges()) == 8


def test_oriented_edges_wind_holes_backwards():
    # The boundary is directed so the region lies to the left: the outer ring
    # counterclockwise as stored, the holes reversed.
    r = _annulus()
    oriented = r.orientedEdges()
    hole_edges = oriented[4:]
    # The hole is stored counterclockwise as a Polygon, so its oriented edges
    # here must be the reverse of the ring's own oriented edges.
    assert [e.opposite() for e in hole_edges] == _hole().orientedEdges()


# --- measures --------------------------------------------------------------

def test_area_nets_out_the_holes():
    r = _annulus()
    assert r.area() == 96  # 100 - 4
    assert r.twiceArea() == 192


def test_centroid_weights_holes_negatively():
    # A hole centred on the square's centre leaves the centroid where it was.
    assert _annulus().centroid() == Point(5, 5)


def test_off_centre_hole_shifts_the_centroid():
    r = PolygonWithHoles(_square(), [_hole(1, 3)])
    assert r.centroid() != Point(5, 5)


def test_vertices_centroid_ignores_area():
    r = _annulus()
    assert r.verticesCentroid() == Point(5, 5)


def test_point_inside_avoids_the_holes():
    r = _annulus()
    p = r.pointInside()
    assert r.contains(p)
    assert not _hole().interiorContains(p)


def test_bbox_and_diameter_come_from_the_outer_ring():
    r = _annulus()
    assert r.bbox() == Rectangle(Point(0, 0), Point(10, 10))
    assert r.diameter() == _square().diameter()


# --- structure -------------------------------------------------------------

def test_valid_region_is_valid():
    assert _annulus().isValid()
    assert _annulus().isSimple()


def test_hole_poking_out_is_invalid():
    # isValid is the on-demand check; the constructor does not enforce it.
    r = PolygonWithHoles(_square(), [_hole(8, 12)])
    assert not r.isValid()


def test_overlapping_holes_are_invalid():
    r = PolygonWithHoles(_square(), [_hole(1, 5), _hole(3, 7)])
    assert not r.isValid()


def test_holes_touching_at_a_boundary_stay_valid():
    # Only the hole *interiors* must be disjoint; their boundaries may meet.
    r = PolygonWithHoles(_square(), [_hole(1, 3), _slit_partner()])
    assert r.isValid()


def test_region_with_area_and_no_slit_is_regular():
    r = _annulus()
    assert r.isRegular()
    assert r.regularized() == [r]


def test_holes_meeting_at_a_point_stay_regular():
    # Pinching at an isolated *point* is not a slit: the interior still reaches
    # the point from every side. These two holes meet only at (3,3).
    r = PolygonWithHoles(_square(), [_hole(1, 3), _hole(3, 5)])
    assert r.isValid()
    assert r.isRegular()


def test_a_slit_makes_a_region_irregular():
    # Two holes sharing a whole *edge* pinch the region shut along it: that
    # stretch is region material with no area on either side, so the region is
    # not the closure of its own interior.
    r = PolygonWithHoles(_square(), [_hole(1, 3), _slit_partner()])
    assert r.isValid()
    assert not r.isRegular()
    # regularized() drops the slit, which here merges the two holes into one.
    pieces = r.regularized()
    assert len(pieces) == 1
    assert pieces[0].isRegular()
    assert pieces[0].area() == r.area()


def test_degenerate_region_regularizes_to_nothing():
    flat = Polygon([Point(0, 0), Point(4, 0), Point(2, 0)])
    r = PolygonWithHoles(flat)
    assert r.isDegenerate()
    assert r.regularized() == []


# --- degeneracy classification ---------------------------------------------

def test_region_collapsing_to_a_segment():
    # PolygonWithHoles has isPoint/isSegment but no getIf* pair upstream.
    flat = Polygon([Point(0, 0), Point(4, 0), Point(2, 0)])
    r = PolygonWithHoles(flat)
    assert r.isSegment()
    assert not r.isPoint()
    assert not r.isUndefined()


def test_region_collapsing_to_a_point():
    r = PolygonWithHoles(Polygon([Point(2, 2), Point(2, 2), Point(2, 2)]))
    assert r.isPoint()
    assert not r.isSegment()


# --- triangulation ---------------------------------------------------------

def test_triangulation_leaves_the_holes_out_of_the_domain():
    r = _annulus()
    t = r.triangulation()
    # The in-domain triangles cover exactly the part of the region with area.
    assert sum((tri.area() for tri in t.triangles()), Fraction(0)) == r.area()


def test_triangulation_constrains_every_ring():
    t = _annulus().triangulation()
    assert t.isConstrained(Segment(Point(4, 4), Point(6, 4)))  # a hole edge
    assert t.isConstrained(Segment(Point(0, 0), Point(10, 0)))  # an outer edge


def test_triangulation_constructor_matches_the_shortcut():
    r = _annulus()
    from pypgl import Triangulation

    assert Triangulation(r).numTriangles() == r.triangulation().numTriangles()


def test_triangulation_accepts_extra_constraints():
    r = _annulus()
    extra = Segment(Point(0, 0), Point(4, 4))
    assert r.triangulation([extra]).isConstrained(extra)


# --- conversions into a region ---------------------------------------------

@pytest.mark.parametrize(
    "shape",
    [
        Triangle(Point(0, 0), Point(4, 0), Point(0, 4)),
        Rectangle(Point(0, 0), Point(4, 4)),
        pypgl.Convex([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]),
        Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]),
    ],
)
def test_area_shapes_convert_to_a_hole_free_region(shape):
    r = shape.asPolygonWithHoles()
    assert isinstance(r, PolygonWithHoles)
    assert not r.hasHoles()
    assert r.area() == shape.area()


# --- Python container sugar -------------------------------------------------

def test_len_counts_vertices_not_holes():
    # C++ iterates a region's holes and gives it vertexCount() rather than
    # size(); the Python layer flattens the rings instead, so a region reads
    # like every other pypgl shape.
    r = _annulus()
    assert len(r) == r.vertexCount() == 8
    assert len(r) != r.holeCount()


def test_iteration_yields_vertices_outer_ring_first():
    r = _annulus()
    assert list(r) == r.vertices()
    assert list(r)[:4] == list(_square())


def test_indexing_is_cyclic_like_every_other_shape():
    r = _annulus()
    assert r[0] == r.vertices()[0]
    assert r[-1] == r.vertices()[-1]
    assert r[len(r)] == r[0]


def test_point_in_region_is_point_containment():
    r = _annulus()
    assert Point(1, 1) in r
    assert Point(5, 5) not in r  # inside the hole
    assert Point(50, 50) not in r


def test_region_renders_inline():
    assert _annulus()._repr_svg_().startswith("<svg")


# --- transforms and translation ---------------------------------------------

def test_translation_moves_every_ring():
    r = _annulus() + Point(1, 1)
    assert r.outer() == _square() + Point(1, 1)
    assert r.hole(0) == _hole() + Point(1, 1)


def test_in_place_translation_mutates():
    r = _annulus()
    r += Point(1, 1)
    assert r.outer() == _square() + Point(1, 1)


def test_scaling_scales_the_area():
    assert (_annulus() * 2).area() == _annulus().area() * 4


def test_rotated90_preserves_area():
    assert _annulus().rotated90().area() == _annulus().area()
