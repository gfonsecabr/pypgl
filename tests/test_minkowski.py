"""The Minkowski sum, A (+) B = {a + b : a in A, b in B}, spelled either
``a.minkowskiSum(b)`` or ``a + b``.

Every summable pair gets the tightest type that can hold its answer, and which
type that is depends on the *pair* rather than on the receiver. Adding a Point
is the translation ``shape + point`` has always meant. Two bounded convex shapes
sum to a Convex (a Rectangle when both are rectangles). An unbounded convex
operand gives a HalfplaneIntersection, or a Halfplane when one operand already
is one. A non-convex operand needs a region, because sliding a shape around the
inside of a C sweeps material that closes over a hole neither operand has -- a
PolygonWithHoles when the answer is guaranteed connected, and a PolygonSet when
it is not.
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
    OrientedSegment,
    Point,
    Polygon,
    PolygonWithHoles,
    PolygonSet,
    Polyline,
    Ray,
    Rectangle,
    Segment,
    Triangle,
)


def _total_area(pieces):
    return sum((piece.area() for piece in pieces), Fraction(0))


def _c_shape():
    """A square annulus cut open through its right wall over y in [3, 5]."""
    return Polygon(
        [
            Point(0, 0), Point(8, 0), Point(8, 3), Point(6, 3),
            Point(6, 2), Point(2, 2), Point(2, 6), Point(6, 6),
            Point(6, 5), Point(8, 5), Point(8, 8), Point(0, 8),
        ]
    )


# --- translation: the Point special case ------------------------------------

@pytest.mark.parametrize(
    "shape",
    [
        Point(1, 2),
        Segment(Point(0, 0), Point(2, 0)),
        Triangle(Point(0, 0), Point(3, 0), Point(0, 3)),
        Rectangle(Point(0, 0), Point(2, 2)),
        Convex([Point(0, 0), Point(2, 0), Point(0, 2)]),
    ],
)
def test_adding_a_point_translates_and_keeps_the_type(shape):
    moved = shape.minkowskiSum(Point(5, 7))
    assert type(moved) is type(shape)
    assert moved == shape + Point(5, 7)


# --- pairs whose sum fits in a single shape ---------------------------------

def test_two_perpendicular_segments_sum_to_a_box():
    box = Segment(Point(0, 0), Point(2, 0)) + Segment(Point(0, 0), Point(0, 3))
    assert box == Convex([Point(0, 0), Point(2, 0), Point(2, 3), Point(0, 3)])


def test_two_rectangles_sum_to_a_rectangle():
    # The one non-trivial pair closed under the sum.
    r = Rectangle(Point(1, 2), Point(4, 6)) + Rectangle(Point(-1, 0), Point(2, 1))
    assert isinstance(r, Rectangle)
    assert r == Rectangle(Point(0, 2), Point(6, 7))


def test_two_triangles_sum_to_a_hexagon():
    a = Triangle(Point(0, 0), Point(3, 0), Point(0, 3))
    b = Triangle(Point(0, 0), Point(-1, 0), Point(0, -1))
    assert len(a + b) == 6


def test_convex_sum_is_exact_on_the_lattice():
    # Every vertex of a convex sum is a sum of two input vertices, so integer
    # coordinates in means integer coordinates out.
    result = Triangle(Point(0, 0), Point(3, 0), Point(0, 3)) + Rectangle(
        Point(0, 0), Point(1, 1)
    )
    for vertex in result:
        assert vertex.x().denominator == 1
        assert vertex.y().denominator == 1


def test_a_flat_sum_reports_itself_through_the_returned_convex():
    # Two parallel segments sum to a longer segment, reported the usual way:
    # a Convex satisfying isSegment().
    flat = Segment(Point(0, 0), Point(2, 0)) + Segment(Point(0, 0), Point(3, 0))
    assert flat.isSegment()
    assert flat.getIfSegment() == Segment(Point(0, 0), Point(5, 0))


def test_the_operator_and_the_method_agree():
    a = Triangle(Point(0, 0), Point(3, 0), Point(0, 3))
    b = Rectangle(Point(0, 0), Point(1, 1))
    assert a + b == a.minkowskiSum(b)


def test_the_convex_sum_is_commutative():
    a = Triangle(Point(0, 0), Point(3, 0), Point(0, 3))
    b = Rectangle(Point(0, 0), Point(1, 1))
    assert a + b == b + a


# --- pairs that need a set of regions ---------------------------------------

def test_a_summand_can_plug_a_concavity_and_strand_a_cavity():
    # Growing the C by two units seals its two-unit cut, which strands the
    # cavity it was holding open as a hole. One operand is a body -- the closure
    # of a connected non-empty interior -- so the answer is guaranteed connected
    # and comes back as a single PolygonWithHoles rather than as a set.
    plugged = _c_shape().minkowskiSum(Rectangle(Point(0, 0), Point(2, 2)))
    assert isinstance(plugged, PolygonWithHoles)
    assert plugged.holeCount() == 1
    assert plugged.outer().bbox() == Rectangle(Point(0, 0), Point(10, 10))
    assert plugged.hole(0).bbox() == Rectangle(Point(4, 4), Point(6, 6))


def test_a_segment_summand_seals_a_cut_just_as_a_wider_one_does():
    # It is the *receiver's* concavity, not the summand's size, that calls for a
    # region: a segment has no area at all and still closes the cut.
    plugged = _c_shape().minkowskiSum(Segment(Point(0, 0), Point(0, 2)))
    assert isinstance(plugged, PolygonWithHoles)
    assert plugged.holeCount() == 1
    assert plugged.outer().bbox() == Rectangle(Point(0, 0), Point(8, 10))
    assert plugged.hole(0).bbox() == Rectangle(Point(2, 4), Point(6, 6))


def test_an_oriented_segment_summand_answers_identically():
    # An orientation is not part of a point set.
    plain = _c_shape().minkowskiSum(Segment(Point(0, 0), Point(0, 2)))
    oriented = _c_shape().minkowskiSum(OrientedSegment(Point(0, 0), Point(0, 2)))
    assert plain == oriented


def test_a_closed_polyline_sweeps_a_frame_around_its_cavity():
    square = Polyline(
        [Point(0, 0), Point(8, 0), Point(8, 8), Point(0, 8), Point(0, 0)]
    )
    frame = square.minkowskiSum(Rectangle(Point(0, 0), Point(1, 1)))
    assert isinstance(frame, PolygonWithHoles)
    assert frame.holeCount() == 1
    assert frame.outer().bbox() == Rectangle(Point(0, 0), Point(9, 9))
    assert frame.hole(0).bbox() == Rectangle(Point(1, 1), Point(8, 8))


def test_a_flat_summand_leaves_a_chain_nothing_to_keep():
    # The sum is regularized, so a summand with no area leaves only material
    # with no area -- which is dropped. `polyline + point` is what translation
    # is for.
    square = Polyline(
        [Point(0, 0), Point(8, 0), Point(8, 8), Point(0, 8), Point(0, 0)]
    )
    assert square.minkowskiSum(Rectangle(Point(3, 3), Point(3, 3))).empty()


def test_a_parallel_segment_summand_can_disconnect_the_result():
    # The chain's own edges are what sweep, and an edge parallel to the segment
    # sweeps a segment, which regularization drops. So the sum of two connected
    # shapes comes back as two pieces: closure((A (+) B) interior) need not be
    # connected, which is the other reason this entry point returns a set.
    square = Polyline(
        [Point(0, 0), Point(8, 0), Point(8, 8), Point(0, 8), Point(0, 0)]
    )
    assert square.minkowskiSum(Segment(Point(0, 0), Point(2, 1))).componentCount() == 1
    bands = square.minkowskiSum(Segment(Point(0, 0), Point(0, 3)))
    assert bands.componentCount() == 2
    assert {piece.bbox() for piece in bands.components()} == {
        Rectangle(Point(0, 0), Point(8, 3)),
        Rectangle(Point(0, 8), Point(8, 11)),
    }


def test_either_operand_may_be_the_concave_one():
    square = Polyline(
        [Point(0, 0), Point(8, 0), Point(8, 8), Point(0, 8), Point(0, 0)]
    )
    u = Polygon(
        [
            Point(0, 0), Point(6, 0), Point(6, 6), Point(4, 6),
            Point(4, 2), Point(2, 2), Point(2, 6), Point(0, 6),
        ]
    )
    assert square.minkowskiSum(u) == u.minkowskiSum(square)


def test_the_region_sum_forwards_from_an_area_shape():
    # Which overload set answers is again about the pair, not the receiver.
    c, r = _c_shape(), Rectangle(Point(0, 0), Point(2, 2))
    assert r.minkowskiSum(c) == c.minkowskiSum(r)


def test_a_convex_receiver_still_takes_the_single_shape_sum():
    # The same Rectangle receiver, against a convex operand, gives one shape.
    assert isinstance(
        Rectangle(Point(0, 0), Point(2, 2)).minkowskiSum(
            Triangle(Point(0, 0), Point(1, 0), Point(0, 1))
        ),
        Convex,
    )


# --- exactness --------------------------------------------------------------

def test_two_integer_operands_can_still_cross_off_the_lattice():
    # Here the crossings are between two *piece sums* rather than between the
    # operands' boundaries, which perfectly ordinary integer operands can
    # produce. The arrangement is built over exact rationals, so the answer is
    # exact rather than truncated.
    u = Polygon(
        [
            Point(0, 0), Point(6, 0), Point(6, 6), Point(4, 6),
            Point(4, 2), Point(2, 2), Point(2, 6), Point(0, 6),
        ]
    )
    corners = u.minkowskiSum(Triangle(Point(-2, -1), Point(2, 0), Point(0, 2))).vertices()
    assert any(
        v.x().denominator != 1 or v.y().denominator != 1 for v in corners
    ), "expected a vertex off the integer lattice"


# --- pairs that are deliberately not bound ----------------------------------

# --- unbounded convex operands: again an intersection of half-planes --------

@pytest.mark.parametrize(
    "other, expected",
    [
        (Line(Point(0, 0), Point(1, 1)), HalfplaneIntersection),
        (Ray(Point(0, 0), Point(1, 1)), HalfplaneIntersection),
        (HalfplaneIntersection(Rectangle(Point(0, 0), Point(1, 1))), HalfplaneIntersection),
        # A half-plane absorbs whatever bounded shape is added to it: the answer
        # is the same half-plane, pushed out to where the summand reaches.
        (Halfplane(Point(0, 0), Point(1, 1)), Halfplane),
    ],
)
def test_an_unbounded_convex_operand_stays_convex(other, expected):
    triangle = Triangle(Point(0, 0), Point(1, 0), Point(0, 1))
    assert isinstance(triangle.minkowskiSum(other), expected)


def test_a_halfplane_is_only_pushed_out():
    up = Halfplane(Point(0, 0), Point(1, 0))                      # y >= 0
    assert up.minkowskiSum(Rectangle(Point(2, 3), Point(5, 7))) == Halfplane(
        Point(0, 3), Point(1, 3)
    )


def test_two_disks_sum_to_a_disk_when_both_carry_a_radius():
    # The one curved sum in the library, and the one pypgl has to ask for
    # explicitly: pgl's default result type there is double, which pypgl does
    # not instantiate, so the binding requests ERational and pgl raises for a
    # disk whose radius is irrational.
    a, b = Disk(Point(0, 0), 3), Disk(Point(4, 1), 2)
    summed = a.minkowskiSum(b)
    assert isinstance(summed, Disk)
    assert summed.center() == Point(4, 1)
    assert summed.radius() == 5
    three_points = Disk(Point(0, 0), Point(3, 1), Point(1, 3))
    with pytest.raises(Exception):
        three_points.minkowskiSum(a)


def test_a_disk_still_has_no_sum_with_a_polygon():
    # Every other Disk pair would need a shape with a curved boundary, so it is
    # not bound at all: a TypeError, the runtime equivalent of pgl's compile
    # error.
    with pytest.raises(TypeError):
        Triangle(Point(0, 0), Point(1, 0), Point(0, 1)).minkowskiSum(Disk(Point(0, 0), 1))
    with pytest.raises(TypeError):
        Disk(Point(0, 0), 1).minkowskiSum(Rectangle(Point(0, 0), Point(1, 1)))


def test_an_unbounded_operand_rejects_a_non_convex_one():
    # The sum would be an unbounded non-convex region, which no pgl shape
    # represents.
    with pytest.raises(TypeError):
        Line(Point(0, 0), Point(1, 1)).minkowskiSum(_c_shape())


def test_a_monotone_chain_sums_into_a_single_polygon():
    # Dragging a convex body along an x-monotone chain sweeps material that
    # cannot close over a hole, so this pair gets the tightest region type of
    # all: a plain Polygon.
    chain = MonotoneChain([Point(0, 0), Point(2, 2), Point(4, 0)])
    assert chain.minkowskiSum(Point(3, 4)) == chain + Point(3, 4)
    swept = chain.minkowskiSum(Rectangle(Point(0, 0), Point(1, 1)))
    assert isinstance(swept, Polygon)
    assert swept.bbox() == Rectangle(Point(0, 0), Point(5, 3))


def test_two_chains_sum_to_a_set_of_regions():
    # Neither operand is a body, so nothing guarantees the answer is connected
    # and it comes back as a PolygonSet.
    a = Polyline([Point(0, 0), Point(2, 2)])
    summed = a.minkowskiSum(Polyline([Point(0, 0), Point(1, 1)]))
    assert isinstance(summed, PolygonSet)
    # Both chains run along the same direction, so the swept material has no
    # area and regularization drops all of it.
    assert summed.empty()
