"""The Minkowski erosion, A (-) B = {x : x + B lies inside A}, spelled
``a.minkowskiErosion(b)``.

It is the morphological dual of the sum in test_minkowski.py and is defined for
exactly the same pairs, but it is *not* commutative and it reads its two
operands quite differently, so the answers differ:

* a Point operand is a translation, as it is for the sum -- the one case that
  mirrors it exactly;
* a convex receiver answers a HalfplaneIntersection, even when it is bounded and
  the sum would have given a Convex, because a convex shape erodes by clamping
  each of its own half-planes and nothing else. Two rectangles are the one pair
  closed under it, as they are under the sum;
* a bounded non-convex receiver answers a PolygonSet and never a single region:
  an erosion disconnects. A dumbbell eroded by anything wider than its handle
  comes apart into two;
* a bounded receiver eroded by an unbounded operand is empty.

There is no operator spelling; ``-`` already means translation by a point.
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
    PolygonSet,
    PolygonWithHoles,
    Polyline,
    Ray,
    Rectangle,
    Segment,
    Triangle,
)


def _square(size=10):
    return Rectangle(Point(0, 0), Point(size, size))


def _dumbbell():
    """Two 4x4 pads joined by a handle two units tall."""
    return Polygon(
        [0, 0, 4, 0, 4, 4, 10, 4, 10, 0, 14, 0, 14, 10, 10, 10, 10, 6, 4, 6, 4, 10, 0, 10]
    )


# --- the translation case ---------------------------------------------------

@pytest.mark.parametrize(
    "shape",
    [
        Point(1, 2),
        Segment(0, 0, 4, 3),
        OrientedSegment(Point(0, 0), Point(4, 3)),
        Triangle(0, 0, 4, 0, 0, 3),
        Rectangle(Point(0, 0), Point(4, 3)),
        Convex([0, 0, 4, 0, 4, 3]),
        MonotoneChain([0, 0, 2, 2, 4, 0]),
        Polyline([0, 0, 2, 2, 4, 0]),
        Polygon([0, 0, 4, 0, 4, 4, 2, 2]),
        Disk(Point(0, 0), 2),
    ],
)
def test_eroding_by_a_point_is_the_opposite_translation(shape):
    # x + p is inside A exactly when x is inside A - p, so this is the one case
    # that gives the receiver's own type back, just as the sum does.
    assert shape.minkowskiErosion(Point(1, 2)) == shape - Point(1, 2)


# --- convex receivers -------------------------------------------------------

def test_a_bounded_convex_receiver_answers_a_halfplane_intersection():
    # Not a Convex, which is what the *sum* of two bounded convex shapes gives:
    # an erosion clamps the receiver's own half-planes and never leaves that
    # form, so the type follows the construction rather than the boundedness.
    eroded = Triangle(0, 0, 12, 0, 0, 12).minkowskiErosion(
        Triangle(0, 0, 2, 0, 0, 2)
    )
    assert isinstance(eroded, HalfplaneIntersection)
    assert not eroded.empty()
    # Every translation it reports really does keep the operand inside.
    big, small = Triangle(0, 0, 12, 0, 0, 12), Triangle(0, 0, 2, 0, 0, 2)
    for corner in eroded.vertices():
        assert big.contains(small + corner)


def test_two_rectangles_are_closed_under_the_erosion():
    # The one pair that stays a Rectangle, exactly as it is the one pair that
    # stays a Rectangle under the sum.
    eroded = _square(10).minkowskiErosion(Rectangle(Point(0, 0), Point(2, 3)))
    assert isinstance(eroded, Rectangle)
    assert eroded == Rectangle(Point(0, 0), Point(8, 7))


def test_eroding_by_something_too_large_is_empty():
    eroded = _square(4).minkowskiErosion(Rectangle(Point(0, 0), Point(9, 9)))
    assert eroded.empty()


def test_a_halfplane_is_pulled_in_where_the_sum_pushes_it_out():
    up = Halfplane(Point(0, 0), Point(1, 0))                      # y >= 0
    box = Rectangle(Point(2, 3), Point(5, 7))
    assert up.minkowskiErosion(box) == Halfplane(Point(0, -3), Point(1, -3))
    # ... which is the sum's mirror image: one moves by the operand's lowest
    # point, the other by its highest.
    assert up.minkowskiSum(box) == Halfplane(Point(0, 3), Point(1, 3))


def test_an_unbounded_operand_leaves_a_bounded_receiver_empty():
    # No translate of a line or a ray fits inside a triangle, so the set of
    # translations that would keep it there is empty.
    triangle = Triangle(0, 0, 10, 0, 0, 10)
    for other in (Line(Point(0, 0), Point(1, 0)), Ray(Point(0, 0), Point(1, 0))):
        assert triangle.minkowskiErosion(other).empty()


def test_a_halfplane_absorbs_only_a_bounded_operand():
    # Eroding a half-plane by another unbounded convex shape needs the general
    # form, so the answer is a HalfplaneIntersection rather than a Halfplane.
    up = Halfplane(Point(0, 0), Point(1, 0))
    assert isinstance(up.minkowskiErosion(Rectangle(Point(0, 0), Point(1, 1))), Halfplane)
    assert isinstance(up.minkowskiErosion(up), HalfplaneIntersection)


def test_the_operand_only_counts_through_its_hull():
    # A convex receiver reads the operand through its support function, which
    # sees nothing but the convex hull -- so a non-convex operand and its hull
    # erode it identically.
    receiver = Rectangle(Point(0, 0), Point(20, 20))
    c = Polygon([0, 0, 6, 0, 6, 2, 2, 2, 2, 4, 6, 4, 6, 6, 0, 6])
    assert receiver.minkowskiErosion(c) == receiver.minkowskiErosion(c.convexHull())


# --- non-convex receivers ---------------------------------------------------

def test_a_non_convex_receiver_answers_a_set_of_regions():
    eroded = _dumbbell().minkowskiErosion(Rectangle(Point(0, 0), Point(1, 1)))
    assert isinstance(eroded, PolygonSet)
    assert not eroded.empty()


def test_an_erosion_disconnects_where_a_sum_never_would():
    # The one structural difference from the sum: eroding the dumbbell by
    # something taller than its two-unit handle severs it into its two pads.
    eroded = _dumbbell().minkowskiErosion(Rectangle(Point(0, 0), Point(1, 3)))
    assert isinstance(eroded, PolygonSet)
    assert eroded.componentCount() == 2
    assert not eroded.isConnected()


def test_a_region_erodes_component_wise_and_stays_inside():
    room = PolygonWithHoles(
        Polygon([0, 0, 20, 0, 20, 20, 0, 20]), [Polygon([8, 8, 12, 8, 12, 12, 8, 12])]
    )
    robot = Convex([0, 0, 2, 0, 2, 2, 0, 2])
    free = room.minkowskiErosion(robot)
    assert isinstance(free, PolygonSet)
    # The defining property: every reported translation keeps the robot inside.
    for component in free.components():
        for vertex in component.outer().vertices():
            assert room.contains(robot + vertex)
    # And the free space is strictly smaller than the room it came from.
    assert free.area() < room.area()


def test_a_chain_erodes_to_nothing_but_still_answers_a_set():
    chain = MonotoneChain([0, 0, 2, 2, 4, 0])
    eroded = chain.minkowskiErosion(Rectangle(Point(0, 0), Point(1, 1)))
    assert isinstance(eroded, PolygonSet)
    assert eroded.empty()


# --- the disk pairs ---------------------------------------------------------

def test_two_disks_erode_to_a_disk_when_both_carry_a_radius():
    eroded = Disk(Point(0, 0), 5).minkowskiErosion(Disk(Point(1, 0), 2))
    assert isinstance(eroded, Disk)
    assert eroded.center() == Point(-1, 0)
    assert eroded.radius() == 3
    three_points = Disk(Point(0, 0), Point(3, 1), Point(1, 3))
    with pytest.raises(Exception):
        three_points.minkowskiErosion(Disk(Point(0, 0), 1))


def test_eroding_a_disk_by_a_larger_one_is_none():
    # The one asymmetry with the sum, which always answers: no translate of the
    # bigger disk fits inside the smaller.
    assert Disk(Point(0, 0), 2).minkowskiErosion(Disk(Point(0, 0), 5)) is None


def test_eroding_a_disk_by_a_halfplane_is_none():
    # A half-plane is unbounded and a disk is not, so nothing fits. pgl models
    # that with a shape for the empty set which pypgl does not bind, and None
    # is how every other empty result reaches Python.
    half = Halfplane(Point(0, 0), Point(1, 0))
    assert Disk(Point(0, 0), 5).minkowskiErosion(half) is None


def test_a_point_erodes_by_a_disk_and_comes_back_empty():
    # A Point is the one shape that takes a Disk operand exactly: eroding it by
    # anything with area leaves nothing, and "nothing" needs no square root.
    eroded = Point(3, 4).minkowskiErosion(Disk(Point(0, 0), 2))
    assert isinstance(eroded, HalfplaneIntersection)
    assert eroded.empty()


def test_the_halfplane_disk_pair_has_no_exact_answer():
    # Sliding a boundary by a radius needs its *unit* normal, whose length is a
    # square root even when the radius is exact -- so this pair raises for
    # pypgl's exact coordinates however the disk was built, in both directions
    # and for the sum just the same.
    half, disk = Halfplane(Point(0, 0), Point(1, 0)), Disk(Point(0, 0), 5)
    with pytest.raises(Exception):
        half.minkowskiErosion(disk)
    with pytest.raises(Exception):
        half.minkowskiSum(disk)
    with pytest.raises(Exception):
        disk.minkowskiSum(half)


def test_the_unbound_disk_pairs_are_still_a_type_error():
    # Every other Disk pair would need a curved boundary, so it is not bound at
    # all -- the runtime equivalent of pgl's compile error, as for the sum.
    with pytest.raises(TypeError):
        Triangle(0, 0, 1, 0, 0, 1).minkowskiErosion(Disk(Point(0, 0), 1))
    with pytest.raises(TypeError):
        Disk(Point(0, 0), 1).minkowskiErosion(Rectangle(Point(0, 0), Point(1, 1)))


# --- the defining property --------------------------------------------------

def test_the_erosion_is_exactly_the_translations_that_fit():
    # x is in A (-) B exactly when B + x is inside A. Checked over a grid, which
    # is the whole contract in one test.
    room = Polygon([0, 0, 12, 0, 12, 8, 6, 8, 6, 4, 0, 4])
    brick = Rectangle(Point(0, 0), Point(2, 2))
    free = room.minkowskiErosion(brick)
    for x in range(-2, 14):
        for y in range(-2, 10):
            here = Point(x, y)
            assert free.contains(here) == room.contains(brick + here)


def test_erosion_undoes_a_sum_of_convex_shapes():
    # (A (+) B) (-) B is A again when both are convex, the opening identity.
    a = Convex([0, 0, 10, 0, 10, 6, 4, 9])
    b = Triangle(0, 0, 2, 0, 0, 2)
    assert a.minkowskiSum(b).minkowskiErosion(b).samePointSet(a)


def test_eroding_by_a_larger_shape_gives_back_less():
    # Monotone in the operand: a bigger eroding shape can only leave less room.
    room = _square(10)
    small = room.minkowskiErosion(Rectangle(Point(0, 0), Point(1, 1)))
    large = room.minkowskiErosion(Rectangle(Point(0, 0), Point(3, 3)))
    assert small.contains(large)
    assert small.area() > large.area()


def test_an_empty_operand_answers_the_whole_plane_or_is_refused():
    # Eroding by the empty set is the whole plane, since every translation of
    # nothing fits. A convex receiver can say so -- the whole plane is what a
    # HalfplaneIntersection with no half-planes is -- while a region-valued
    # receiver has no way to represent it and raises instead.
    assert _square(10).minkowskiErosion(Polygon([])).isPlane()
    with pytest.raises(Exception):
        Polygon([0, 0, 10, 0, 10, 10, 0, 10]).minkowskiErosion(Polygon([]))


def test_the_answer_stays_exact():
    # A third of a unit is representable, so the eroded rectangle's corner is
    # the exact rational it should be -- no rounding anywhere.
    eroded = _square(10).minkowskiErosion(
        Rectangle(Point(0, 0), Point(Fraction(1, 3), Fraction(1, 7)))
    )
    assert eroded.max() == Point(Fraction(29, 3), Fraction(69, 7))
