"""The Minkowski sum, A (+) B = {a + b : a in A, b in B}, spelled either
``a.minkowskiSum(b)`` or ``a + b``.

Two overload sets answer, and which one does is a question about the *pair*
rather than about the receiver. A pair of bounded convex shapes sums to a single
shape (a Convex, or a Rectangle when both are rectangles), and adding a Point is
the translation that ``shape + point`` has always meant. A non-convex operand
needs a set of regions, because sliding a shape around the inside of a C sweeps
material that closes over a hole neither operand has.
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
    # cavity it was holding open as a hole.
    plugged = _c_shape().minkowskiSum(Rectangle(Point(0, 0), Point(2, 2)))
    assert len(plugged) == 1
    assert plugged[0].holeCount() == 1
    assert plugged[0].outer().bbox() == Rectangle(Point(0, 0), Point(10, 10))
    assert plugged[0].hole(0).bbox() == Rectangle(Point(4, 4), Point(6, 6))


def test_a_segment_summand_seals_a_cut_just_as_a_wider_one_does():
    # It is the *receiver's* concavity, not the summand's size, that calls for a
    # region: a segment has no area at all and still closes the cut.
    plugged = _c_shape().minkowskiSum(Segment(Point(0, 0), Point(0, 2)))
    assert len(plugged) == 1
    assert plugged[0].holeCount() == 1
    assert plugged[0].outer().bbox() == Rectangle(Point(0, 0), Point(8, 10))
    assert plugged[0].hole(0).bbox() == Rectangle(Point(2, 4), Point(6, 6))


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
    assert len(frame) == 1
    assert frame[0].holeCount() == 1
    assert frame[0].outer().bbox() == Rectangle(Point(0, 0), Point(9, 9))
    assert frame[0].hole(0).bbox() == Rectangle(Point(1, 1), Point(8, 8))


def test_a_flat_summand_leaves_a_chain_nothing_to_keep():
    # The sum is regularized, so a summand with no area leaves only material
    # with no area -- which is dropped. `polyline + point` is what translation
    # is for.
    square = Polyline(
        [Point(0, 0), Point(8, 0), Point(8, 8), Point(0, 8), Point(0, 0)]
    )
    assert square.minkowskiSum(Rectangle(Point(3, 3), Point(3, 3))) == []


def test_a_parallel_segment_summand_can_disconnect_the_result():
    # The chain's own edges are what sweep, and an edge parallel to the segment
    # sweeps a segment, which regularization drops. So the sum of two connected
    # shapes comes back as two pieces: closure((A (+) B) interior) need not be
    # connected, which is the other reason this entry point returns a set.
    square = Polyline(
        [Point(0, 0), Point(8, 0), Point(8, 8), Point(0, 8), Point(0, 0)]
    )
    assert len(square.minkowskiSum(Segment(Point(0, 0), Point(2, 1)))) == 1
    bands = square.minkowskiSum(Segment(Point(0, 0), Point(0, 3)))
    assert len(bands) == 2
    assert {piece.bbox() for piece in bands} == {
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
    pieces = u.minkowskiSum(Triangle(Point(-2, -1), Point(2, 0), Point(0, 2)))
    corners = [v for piece in pieces for v in piece.vertices()]
    assert any(
        v.x().denominator != 1 or v.y().denominator != 1 for v in corners
    ), "expected a vertex off the integer lattice"


# --- pairs that are deliberately not bound ----------------------------------

@pytest.mark.parametrize(
    "other",
    [
        Disk(Point(0, 0), 1),
        Line(Point(0, 0), Point(1, 1)),
        Ray(Point(0, 0), Point(1, 1)),
        Halfplane(Point(0, 0), Point(1, 1)),
        HalfplaneIntersection(Rectangle(Point(0, 0), Point(1, 1))),
    ],
)
def test_unsupported_pairs_raise_rather_than_approximate(other):
    # A Disk sums to a rounded shape and an unbounded operand to an unbounded
    # region, and no pgl type represents either. In C++ that is a compile error;
    # here it is a TypeError, which is the runtime equivalent.
    with pytest.raises(TypeError):
        Triangle(Point(0, 0), Point(1, 0), Point(0, 1)).minkowskiSum(other)


def test_a_monotone_chain_sums_only_with_a_point():
    # A chain's one summable pair is the translation. Anything wider needs
    # asPolyline(), rather than giving the chain an overload set that would lose
    # its defining sorted structure.
    chain = MonotoneChain([Point(0, 0), Point(2, 2), Point(4, 0)])
    assert chain.minkowskiSum(Point(3, 4)) == chain + Point(3, 4)
    with pytest.raises(TypeError):
        chain.minkowskiSum(Rectangle(Point(0, 0), Point(1, 1)))
    assert isinstance(chain.asPolyline(), Polyline)
    assert chain.asPolyline().minkowskiSum(Rectangle(Point(0, 0), Point(1, 1)))


def test_polyline_plus_polyline_is_not_a_pair():
    a = Polyline([Point(0, 0), Point(2, 2)])
    with pytest.raises(TypeError):
        a.minkowskiSum(Polyline([Point(0, 0), Point(1, 1)]))
