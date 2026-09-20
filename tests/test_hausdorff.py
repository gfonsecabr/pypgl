"""The widened Hausdorff grids.

`squaredHausdorffDistance` covers the seven bounded convex shapes; the two
polyhedral norms cover every pair of bounded polygonal shapes, and a
`HalfplaneIntersection` against the convex ones. All three are the standard
*symmetric* Hausdorff distance, max(h(A, B), h(B, A)).

The three tiers themselves are pinned in test_distances.py. What is checked here
is that the answers are right where no vertex gives them away, and that the two
preconditions -- a non-empty operand, and a bounded region -- are enforced as
exceptions rather than left undefined.
"""

from fractions import Fraction

import pytest

from pypgl import (
    Convex,
    Halfplane,
    HalfplaneIntersection,
    MonotoneChain,
    Point,
    Polygon,
    PolygonSet,
    PolygonWithHoles,
    Polyline,
    Rectangle,
    Segment,
    Triangle,
)

L1 = "hausdorffDistanceL1"
LINF = "hausdorffDistanceLInf"
SQUARED = "squaredHausdorffDistance"


def c_shape():
    """A C: non-convex, and its own convex hull is much larger."""
    return Polygon([0, 0, 10, 0, 10, 3, 3, 3, 3, 7, 10, 7, 10, 10, 0, 10])


def two_boxes():
    """A PolygonSet of two boxes under the segment y = 0, x in [0, 10], one at
    each end. Between them the nearest box recedes, so the distance from that
    segment peaks strictly inside it."""
    return PolygonSet(
        [
            Polygon([-1, -2, 1, -2, 1, -1, -1, -1]).asPolygonWithHoles(),
            Polygon([9, -2, 11, -2, 11, -1, 9, -1]).asPolygonWithHoles(),
        ]
    )


# --- The maximum is not always at a vertex ----------------------------------


@pytest.mark.parametrize(
    "method, expected, vertices_only",
    # Along the segment the L1 distance to the nearer box is min(x, 10 - x),
    # which peaks at x = 5 with 5 -- on no vertex of either shape. A vertex-only
    # computation, which is what the Euclidean form may do and these two may
    # not, reports the boxes' far corners instead: 3 in L1 and 2 in LInf.
    [(L1, 5, 3), (LINF, 4, 2)],
)
def test_the_polyhedral_norms_find_a_maximum_strictly_inside_an_edge(
    method, expected, vertices_only
):
    chain = Polyline([Point(0, 0), Point(10, 0)])
    boxes = two_boxes()
    assert getattr(chain, method)(boxes) == expected
    assert getattr(boxes, method)(chain) == expected

    naive = max(
        max(getattr(v, method.replace("hausdorffDistance", "distance"))(boxes)
            for v in chain.vertices()),
        max(getattr(v, method.replace("hausdorffDistance", "distance"))(chain)
            for v in boxes.vertices()),
    )
    assert naive == vertices_only < expected


@pytest.mark.parametrize("method", [L1, LINF])
def test_a_dense_sampling_of_both_shapes_never_beats_the_answer(method):
    """Every sampled point's distance to the other shape is a lower bound on the
    directed distance, so the answer must dominate all of them -- and here the
    sampling actually attains it, which pins the value from both sides."""
    chain = Polyline([Point(0, 0), Point(10, 0)])
    boxes = two_boxes()
    point_metric = method.replace("hausdorffDistance", "distance")
    answer = getattr(chain, method)(boxes)
    sampled = max(
        getattr(Point(Fraction(j, 20), 0), point_metric)(boxes) for j in range(0, 201)
    )
    assert sampled == answer


# --- Non-convex operands ----------------------------------------------------


@pytest.mark.parametrize("method, expected", [(L1, 2), (LINF, 2)])
def test_a_non_convex_shape_is_measured_as_itself_not_as_its_hull(method, expected):
    # Measuring the C against its own hull isolates exactly what the hull adds:
    # the C is inside it, so one direction is zero, and the other is the notch's
    # deepest point. At y = 5 the notch reaches x = 10, two units from the arms
    # at y = 3 and y = 7 -- the nearest material either way.
    c = c_shape()
    hull = c.convexHull()
    assert hull.contains(c)
    assert getattr(c, method)(hull) == expected
    assert getattr(hull, method)(c) == expected
    assert getattr(hull, method)(hull) == 0


@pytest.mark.parametrize("method", [L1, LINF])
def test_a_shape_against_itself_is_zero_for_every_bounded_polygonal_kind(method):
    for shape in (
        Point(3, 4),
        Segment(Point(0, 0), Point(4, 0)),
        Triangle(Point(0, 0), Point(3, 0), Point(0, 3)),
        Rectangle(Point(0, 0), Point(2, 5)),
        Convex([Point(0, 0), Point(4, 0), Point(4, 4)]),
        MonotoneChain([Point(0, 0), Point(2, 3), Point(5, 1)]),
        Polyline([Point(0, 0), Point(2, 3), Point(1, 1)]),
        c_shape(),
        c_shape().asPolygonWithHoles(),
        two_boxes(),
    ):
        assert getattr(shape, method)(shape) == 0, shape


@pytest.mark.parametrize("method", [L1, LINF])
def test_the_grid_is_symmetric_across_every_kind_of_operand(method):
    shapes = [
        Point(1, 1),
        Segment(Point(0, 0), Point(4, 0)),
        Triangle(Point(0, 0), Point(3, 0), Point(0, 3)),
        Rectangle(Point(-1, -1), Point(2, 5)),
        Convex([Point(0, 0), Point(4, 0), Point(4, 4)]),
        MonotoneChain([Point(0, 0), Point(2, 3), Point(5, 1)]),
        Polyline([Point(0, 0), Point(2, 3), Point(1, 1)]),
        c_shape(),
        c_shape().asPolygonWithHoles(),
        two_boxes(),
    ]
    for a in shapes:
        for b in shapes:
            forward = getattr(a, method)(b)
            assert forward >= 0
            assert forward == getattr(b, method)(a)


def test_a_hole_is_boundary_like_any_other_edge():
    # The hole's rim is material, so the one-sided distance from a point in the
    # hole is positive where the solid square gives zero -- but the symmetric
    # answer is the far corner either way, which is the point worth pinning:
    # a hole changes which edges the search may land on, not the maximum here.
    ring = PolygonWithHoles(
        Polygon([0, 0, 10, 0, 10, 10, 0, 10]), [Polygon([4, 4, 6, 4, 6, 6, 4, 6])]
    )
    solid = Polygon([0, 0, 10, 0, 10, 10, 0, 10])
    in_the_hole = Point(5, 5)
    assert ring.contains(in_the_hole) is False and solid.contains(in_the_hole) is True
    assert in_the_hole.distanceL1(ring) == 1 and in_the_hole.distanceL1(solid) == 0
    assert ring.hausdorffDistanceL1(in_the_hole) == 10
    assert ring.hausdorffDistanceLInf(in_the_hole) == 5
    assert solid.hausdorffDistanceL1(in_the_hole) == 10


# --- A HalfplaneIntersection operand ----------------------------------------


def test_a_bounded_halfplane_intersection_joins_all_three_grids():
    region = Rectangle(Point(0, 0), Point(2, 2)).asHalfplaneIntersection()
    triangle = Triangle(Point(0, 0), Point(1, 0), Point(0, 1))
    for method in (SQUARED, L1, LINF):
        assert getattr(region, method)(triangle) == getattr(triangle, method)(region)
    # It answers exactly as the equal Rectangle does.
    rectangle = Rectangle(Point(0, 0), Point(2, 2))
    for method in (SQUARED, L1, LINF):
        assert getattr(region, method)(triangle) == getattr(rectangle, method)(triangle)


def test_a_halfplane_intersection_takes_only_convex_operands_in_l1_and_linf():
    region = Rectangle(Point(0, 0), Point(2, 2)).asHalfplaneIntersection()
    for method in (L1, LINF):
        with pytest.raises(TypeError):
            getattr(region, method)(c_shape())
        with pytest.raises(TypeError):
            getattr(c_shape(), method)(region)


@pytest.mark.parametrize("method", [SQUARED, L1, LINF])
def test_an_unbounded_region_has_no_hausdorff_distance(method):
    unbounded = HalfplaneIntersection([Halfplane(Point(0, 0), Point(1, 0))])
    assert not unbounded.isBounded()
    with pytest.raises(RuntimeError):
        getattr(unbounded, method)(Point(0, 5))
    with pytest.raises(RuntimeError):
        getattr(Point(0, 5), method)(unbounded)
    # The default-constructed one is the whole plane, unbounded likewise.
    with pytest.raises(RuntimeError):
        getattr(HalfplaneIntersection(), method)(Point(0, 0))


# --- The empty operand, which pgl does not check ----------------------------


def empty_shapes():
    """Every bound shape whose point set can be empty. A non-empty operand is a
    precondition -- the distance is a supremum over each shape's points, and
    there are none -- which pgl states as an assert and so does not enforce in a
    release build. pypgl raises instead, uniformly, rather than leaving the call
    undefined (which, depending on the shape, read past the end of a vertex list
    or quietly answered 0)."""
    return {
        "Rectangle": Rectangle(),
        "Convex": Convex(),
        "MonotoneChain": MonotoneChain(),
        "Polyline": Polyline(),
        "Polygon": Polygon(),
        "PolygonWithHoles": PolygonWithHoles(),
        "PolygonSet": PolygonSet(),
        "HalfplaneIntersection": HalfplaneIntersection(
            [Halfplane(Point(0, 0), Point(1, 0)), Halfplane(Point(0, -1), Point(-1, -1))]
        ),
    }


@pytest.mark.parametrize("name", sorted(empty_shapes()))
@pytest.mark.parametrize("method", [SQUARED, L1, LINF])
def test_an_empty_operand_is_refused_on_either_side(name, method):
    empty = empty_shapes()[name]
    assert empty.empty()
    # A Triangle is in every one of the three grids, so the only reason a call
    # below can be a TypeError is that the *empty* shape's kind is not.
    other = Triangle(Point(0, 0), Point(1, 0), Point(0, 1))
    if hasattr(empty, method):
        with pytest.raises(ValueError, match="empty"):
            getattr(empty, method)(other)
    try:
        result = getattr(other, method)(empty)
    except ValueError as exc:
        assert "empty" in str(exc)
    except TypeError:
        assert not hasattr(empty, method), f"{name} takes {method} but the reverse does not"
    else:  # pragma: no cover
        pytest.fail(f"an empty {name} answered {result} for {method}")


def test_two_empty_shapes_are_refused_too():
    with pytest.raises(ValueError, match="empty"):
        Convex().hausdorffDistanceL1(Polygon())


def test_a_degenerate_shape_is_not_an_empty_one():
    # empty() is about the point set, not about dimension: a zero-area rectangle
    # and a one-vertex Convex both hold points and are measured normally.
    flat = Rectangle(Point(2, 3), Point(2, 3))
    single = Convex([Point(2, 3)])
    assert not flat.empty() and not single.empty()
    assert flat.squaredHausdorffDistance(single) == 0
    assert flat.hausdorffDistanceL1(Point(2, 5)) == 2
