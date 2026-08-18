"""HalfplaneIntersection: the intersection of finitely many closed half-planes.

Convex like Convex, but -- unlike it -- possibly unbounded (a wedge, a strip, a
half-plane, the whole plane) and possibly empty. Two conventions drive most of
these tests: a default-constructed region is the *whole plane* rather than the
empty set, and its stored elements are half-planes rather than points, so
len()/[]/iteration run over the constraints while the implicit corners are
reached through vertexCount()/vertex(i)/vertices().

Those corners are generally not representable in the coordinate type of the
half-planes that bound them -- integer half-planes routinely bound regions with
rational vertices -- which is exactly the case pypgl's single exact ERational
instantiation handles without rounding.
"""

from fractions import Fraction

import pytest

import pypgl
from pypgl import (
    Convex,
    Halfplane,
    HalfplaneIntersection,
    Line,
    OrientedSegment,
    Point,
    Polygon,
    Ray,
    Rectangle,
    Segment,
    Triangle,
)


def _unit_square():
    return HalfplaneIntersection(Rectangle(Point(0, 0), Point(4, 4)))


def _upper():
    """The closed half-plane y >= 0."""
    return Halfplane(Point(0, 0), Point(1, 0))


# --- importability, construction --------------------------------------------

def test_importable_and_in_all():
    assert hasattr(pypgl, "HalfplaneIntersection")
    assert "HalfplaneIntersection" in pypgl.__all__


def test_default_is_the_whole_plane_not_the_empty_set():
    # The opposite convention from Convex(), which is empty. A region with no
    # constraints constrains nothing.
    k = HalfplaneIntersection()
    assert k.isPlane()
    assert not k.empty()
    assert not k.isBounded()
    assert len(k) == 0
    assert Point(10**6, -(10**6)) in k
    assert Convex([]).isDegenerate()  # ... whereas an empty Convex has nothing


@pytest.mark.parametrize(
    "shape",
    [
        Rectangle(Point(0, 0), Point(4, 4)),
        Triangle(Point(0, 0), Point(4, 0), Point(0, 4)),
        Convex([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]),
    ],
)
def test_constructed_from_a_bounded_convex_shape(shape):
    k = HalfplaneIntersection(shape)
    assert k.isBounded()
    assert k.area() == shape.area()
    assert len(k) == len(shape.edges())


def test_constructed_from_a_single_halfplane():
    k = HalfplaneIntersection(_upper())
    assert len(k) == 1
    assert k.isHalfplane()
    assert k.getIfHalfplane() == _upper()
    assert not k.isBounded()


def test_constructed_from_a_list_of_halfplanes():
    k = HalfplaneIntersection(list(_unit_square().halfplanes()))
    assert k == _unit_square()


def test_redundant_halfplanes_are_dropped():
    # y >= 0 is implied by y >= 1, so only one constraint survives.
    k = HalfplaneIntersection([_upper(), Halfplane(Point(0, 1), Point(1, 1))])
    assert len(k) == 1


def test_is_unhashable_because_mutable():
    with pytest.raises(TypeError):
        {_unit_square()}


# --- insert -----------------------------------------------------------------

def test_insert_narrows_the_region():
    k = HalfplaneIntersection()
    assert k.insert(_upper()) is True
    assert k.isHalfplane()
    assert k.insert(Halfplane(Point(0, 0), Point(0, -1))) is True  # x >= 0
    assert len(k) == 2
    assert not k.isBounded()


def test_insert_reports_a_redundant_halfplane():
    k = HalfplaneIntersection(_upper())
    assert k.insert(_upper()) is False
    assert len(k) == 1


def test_insert_reports_a_degenerate_halfplane():
    # A degenerate half-plane bounds no side, so it carries no constraint.
    k = HalfplaneIntersection(_upper())
    assert k.insert(Halfplane(Point(2, 2), Point(2, 2))) is False
    assert len(k) == 1


def test_insert_can_empty_the_region_stickily():
    k = HalfplaneIntersection(_upper())
    k.insert(Halfplane(Point(0, -1), Point(-1, -1)))  # y <= -1
    assert k.empty()
    # Once empty, it stays empty.
    k.insert(_upper())
    assert k.empty()


def test_insert_removes_the_constraints_it_makes_redundant():
    k = HalfplaneIntersection(_upper())
    k.insert(Halfplane(Point(0, 5), Point(1, 5)))  # y >= 5 implies y >= 0
    assert len(k) == 1


# --- the classification family ----------------------------------------------

def test_a_bounded_region_is_none_of_the_named_cases():
    k = _unit_square()
    for name in ("empty", "isPlane", "isHalfplane", "isLine", "isRay",
                 "isPoint", "isSegment", "isDegenerate"):
        assert getattr(k, name)() is False, name
    assert k.isBounded()


def test_is_undefined_is_always_false():
    # insert() ignores undefined half-planes, so every region -- empty,
    # degenerate or full-dimensional -- is well defined.
    for k in (HalfplaneIntersection(), _unit_square(),
              HalfplaneIntersection(_upper())):
        assert k.isUndefined() is False


def test_two_opposite_halfplanes_make_a_line():
    k = HalfplaneIntersection([_upper(), _upper().opposite()])
    assert k.isLine()
    assert k.isDegenerate()
    assert k.getIfLine() == Line(Point(0, 0), Point(1, 0))
    assert k.getIfPoint() is None


def test_a_wedge_can_close_down_to_a_ray():
    # x >= 0 together with y >= 0 and y <= 0.
    k = HalfplaneIntersection(
        [Halfplane(Point(0, 0), Point(0, -1)), _upper(), _upper().opposite()]
    )
    assert k.isRay()
    assert k.getIfRay() == Ray(Point(0, 0), Point(1, 0))


def test_a_region_can_close_down_to_a_point():
    k = HalfplaneIntersection(Rectangle(Point(2, 3), Point(2, 3)))
    assert k.isPoint()
    assert k.getIfPoint() == Point(2, 3)
    assert k.isDegenerate()


def test_a_region_can_close_down_to_a_segment():
    k = HalfplaneIntersection(Rectangle(Point(0, 3), Point(4, 3)))
    assert k.isSegment()
    assert k.getIfSegment() == Segment(Point(0, 3), Point(4, 3))


def test_the_getif_pair_is_none_when_the_case_does_not_apply():
    k = _unit_square()
    assert k.getIfPoint() is None
    assert k.getIfSegment() is None
    assert k.getIfLine() is None
    assert k.getIfRay() is None
    assert k.getIfHalfplane() is None


# --- the implicit corners ---------------------------------------------------

def test_vertices_of_a_bounded_region():
    k = _unit_square()
    assert k.vertexCount() == 4
    assert set(k.vertices()) == {
        Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)
    }


def test_vertices_are_exact_even_when_off_the_lattice():
    # This is the case the exact instantiation is for: half-planes with integer
    # boundaries routinely bound a region whose corners are not integral.
    k = HalfplaneIntersection(
        [
            Halfplane(Point(0, 0), Point(1, 0)),      # y >= 0
            Halfplane(Point(0, 0), Point(0, -1)),     # x >= 0
            Halfplane(Point(2, 0), Point(0, 3)),      # 3x + 2y <= 6
            Halfplane(Point(3, 0), Point(0, 1)),      # x + 3y <= 3
        ]
    )
    assert k.isBounded()
    # The last two boundaries cross at (12/7, 3/7), which no integer coordinate
    # type could hold; pypgl's exact rationals report it as it is.
    assert Point(Fraction(12, 7), Fraction(3, 7)) in k.vertices()


def test_edge_is_a_segment_ray_or_line_by_position():
    # Bounded: every edge is a segment.
    k = _unit_square()
    assert all(isinstance(k.edge(i), Segment) for i in range(len(k)))
    # A lone half-plane contributes its whole boundary line.
    assert isinstance(HalfplaneIntersection(_upper()).edge(0), Line)
    # A wedge's two edges are rays.
    wedge = HalfplaneIntersection(
        [Halfplane(Point(0, 0), Point(1, 0)), Halfplane(Point(0, 0), Point(0, -1))]
    )
    assert all(isinstance(wedge.edge(i), Ray) for i in range(len(wedge)))


# --- measures ---------------------------------------------------------------

def test_area_and_centroid_of_a_bounded_region():
    k = _unit_square()
    assert k.area() == 16
    assert k.twiceArea() == 32
    assert k.centroid() == Point(2, 2)


def test_bbox_and_as_convex_of_a_bounded_region():
    k = _unit_square()
    assert k.bbox() == Rectangle(Point(0, 0), Point(4, 4))
    assert k.asConvex() == Convex([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])


@pytest.mark.parametrize("method", ["bbox", "asConvex", "area", "twiceArea"])
def test_unbounded_regions_have_no_box_hull_or_area(method):
    with pytest.raises(Exception):
        getattr(HalfplaneIntersection(_upper()), method)()


def test_point_inside_is_inside():
    k = _unit_square()
    assert k.contains(k.pointInside())


# --- intersection is closed and exact ---------------------------------------

@pytest.mark.parametrize(
    "other",
    [
        Halfplane(Point(0, 1), Point(1, 1)),
        Rectangle(Point(1, 1), Point(9, 9)),
        Triangle(Point(0, 0), Point(9, 0), Point(0, 9)),
        Convex([Point(1, 1), Point(9, 1), Point(9, 9), Point(1, 9)]),
        HalfplaneIntersection(Rectangle(Point(1, 1), Point(9, 9))),
    ],
)
def test_intersection_with_a_convex_region_is_again_one(other):
    result = _unit_square().intersection(other)
    assert isinstance(result, HalfplaneIntersection)


def test_intersection_narrows_as_expected():
    k = _unit_square().intersection(Rectangle(Point(2, 2), Point(9, 9)))
    assert k.area() == 4
    assert k.bbox() == Rectangle(Point(2, 2), Point(4, 4))


def test_disjoint_intersection_is_the_empty_region():
    k = _unit_square().intersection(Rectangle(Point(50, 50), Point(60, 60)))
    assert k.empty()


def test_two_halfplanes_intersect_into_a_region():
    # Halfplane.intersection(Halfplane) is exact and division-free, whether the
    # result is a wedge, a strip, a nested half-plane, a line, or empty.
    k = _upper().intersection(Halfplane(Point(0, 0), Point(0, -1)))
    assert isinstance(k, HalfplaneIntersection)
    assert len(k) == 2


def test_intersection_with_a_line_gives_a_concrete_piece():
    # Against the 0D/1D shapes it is the usual optional/variant of pieces, not a
    # region.
    piece = _unit_square().intersection(Line(Point(0, 2), Point(1, 2)))
    assert piece == Segment(Point(0, 2), Point(4, 2))


# --- conversions into a region ----------------------------------------------

@pytest.mark.parametrize(
    "shape",
    [
        Point(1, 2),
        Segment(Point(0, 0), Point(2, 2)),
        Line(Point(0, 0), Point(1, 1)),
        Halfplane(Point(0, 0), Point(1, 0)),
        Triangle(Point(0, 0), Point(4, 0), Point(0, 4)),
        Rectangle(Point(0, 0), Point(4, 4)),
        Convex([Point(0, 0), Point(4, 0), Point(0, 4)]),
    ],
)
def test_shapes_convert_to_a_halfplane_intersection(shape):
    k = shape.asHalfplaneIntersection()
    assert isinstance(k, HalfplaneIntersection)
    assert k.contains(shape)


# --- Python container sugar --------------------------------------------------

def test_len_and_iteration_are_over_halfplanes_not_points():
    # These are what pgl gives the shape size()/get()/index() for; its own
    # corners are implicit, and reached through vertices() instead.
    k = _unit_square()
    assert len(k) == 4 == k.size()
    assert all(isinstance(h, Halfplane) for h in k)
    assert k[0] == k.get(0)
    assert k[len(k)] == k[0]  # cyclic, like every other shape


def test_index_finds_a_stored_halfplane():
    k = _unit_square()
    assert k.index(k[2]) == 2
    assert k.index(Halfplane(Point(50, 50), Point(51, 50))) is None


def test_point_in_region_is_point_containment():
    k = _unit_square()
    assert Point(2, 2) in k
    assert Point(0, 0) in k  # closed
    assert Point(5, 5) not in k


def test_renders_inline():
    assert _unit_square()._repr_svg_().startswith("<svg")


# --- interaction with the rest of the library --------------------------------

def test_predicates_against_the_other_shapes():
    k = _unit_square()
    assert k.contains(Point(1, 1))
    assert k.intersects(Segment(Point(-5, 2), Point(5, 2)))
    assert not k.intersects(Rectangle(Point(50, 50), Point(60, 60)))
    assert k.contains(Triangle(Point(1, 1), Point(2, 1), Point(1, 2)))


def test_distances_against_the_other_shapes():
    k = _unit_square()
    assert k.squaredDistance(Point(4, 8)) == 16
    assert k.distanceL1(Point(4, 8)) == 4
    assert k.distanceLInf(Point(4, 8)) == 4


def test_a_bounded_region_is_storable_in_a_shape_tree():
    tree = pypgl.ShapeTree([_unit_square(), Point(50, 50)])
    assert len(tree) == 2
    assert _unit_square() in tree


def test_an_unbounded_region_cannot_be_stored_but_is_a_valid_query():
    # Storing needs a bbox(), which an unbounded region does not have; querying
    # never needs the query's own box, only pruning against a stored subtree's.
    with pytest.raises(Exception):
        pypgl.ShapeTree([HalfplaneIntersection(_upper())])
    tree = pypgl.ShapeTree([Point(1, 1), Point(1, -1)])
    assert len(tree.reportIntersecting(HalfplaneIntersection(_upper()))) == 1


def test_transformations_apply():
    k = _unit_square()
    assert k.rotated90().area() == 16
    assert (k + Point(10, 10)).bbox() == Rectangle(Point(10, 10), Point(14, 14))
