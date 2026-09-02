"""The uniform predicate surface and the ``in`` sugar."""

import pypgl


def test_point_contains_point():
    p = pypgl.Point(1, 2)
    assert p.contains(pypgl.Point(1, 2))
    assert not p.contains(pypgl.Point(1, 3))


def test_segment_contains_point():
    s = pypgl.Segment(0, 0, 4, 4)
    assert s.contains(pypgl.Point(2, 2))
    assert not s.contains(pypgl.Point(2, 3))


def test_in_operator_point_in_shape():
    s = pypgl.Segment(0, 0, 4, 4)
    assert pypgl.Point(2, 2) in s
    assert pypgl.Point(2, 3) not in s
    assert pypgl.Point(1, 1) in pypgl.Point(1, 1)


def test_boundary_vs_interior_contains():
    s = pypgl.Segment(0, 0, 4, 0)
    endpoint = pypgl.Point(0, 0)
    middle = pypgl.Point(2, 0)
    assert s.boundaryContains(endpoint)
    assert not s.interiorContains(endpoint)
    assert s.interiorContains(middle)


def test_intersects_and_crosses():
    a = pypgl.Segment(0, 0, 4, 0)
    b = pypgl.Segment(2, -2, 2, 2)
    assert a.intersects(b)
    assert a.crosses(b)
    parallel = pypgl.Segment(0, 1, 4, 1)
    assert not a.intersects(parallel)


# --- interiorContainsInterior: the open-segment predicate ---------------------
#
# The one predicate `interiorContains` cannot express: the segment's endpoints
# may sit on the boundary as long as everything strictly between them stays
# strictly inside. Bound on the three region shapes pgl defines it for.

def _l_shape():
    """A non-convex L, so a segment can leave and re-enter through the notch."""
    return pypgl.Polygon([0, 0, 6, 0, 6, 2, 2, 2, 2, 6, 0, 6])


def test_endpoints_on_the_boundary_are_allowed():
    square = pypgl.Polygon([0, 0, 4, 0, 4, 4, 0, 4])
    diagonal = pypgl.Segment(pypgl.Point(0, 0), pypgl.Point(4, 4))
    assert square.interiorContainsInterior(diagonal)
    # The closed predicate refuses the very same segment: its endpoints are on
    # the boundary, so the closed segment is not inside the open set.
    assert not square.interiorContains(diagonal)


def test_a_segment_lying_along_an_edge_is_refused():
    square = pypgl.Polygon([0, 0, 4, 0, 4, 4, 0, 4])
    assert not square.interiorContainsInterior(
        pypgl.Segment(pypgl.Point(0, 0), pypgl.Point(4, 0)))


def test_a_segment_touching_the_boundary_in_its_middle_is_refused():
    notched = _l_shape()
    # Runs corner to corner across the notch, grazing the reflex vertex (2, 2).
    grazing = pypgl.Segment(pypgl.Point(0, 4), pypgl.Point(4, 0))
    assert notched.contains(grazing)   # it never leaves the closed shape
    assert not notched.interiorContainsInterior(grazing)


def test_a_segment_leaving_the_shape_is_refused():
    notched = _l_shape()
    assert not notched.interiorContainsInterior(
        pypgl.Segment(pypgl.Point(1, 5), pypgl.Point(5, 1)))


def test_a_degenerate_segment_asks_about_its_sole_point():
    square = pypgl.Polygon([0, 0, 4, 0, 4, 4, 0, 4])
    inside = pypgl.Point(2, 2)
    on_edge = pypgl.Point(0, 2)
    outside = pypgl.Point(9, 9)
    assert square.interiorContainsInterior(pypgl.Segment(inside, inside))
    assert square.interiorContainsInterior(pypgl.Segment(on_edge, on_edge))
    assert not square.interiorContainsInterior(pypgl.Segment(outside, outside))


def test_a_region_refuses_a_segment_touching_a_hole():
    outer = pypgl.Polygon([0, 0, 6, 0, 6, 6, 0, 6])
    hole = pypgl.Polygon([2, 2, 4, 2, 4, 4, 2, 4])
    region = pypgl.PolygonWithHoles(outer, [hole])
    assert region.interiorContainsInterior(
        pypgl.Segment(pypgl.Point(0, 0), pypgl.Point(2, 1)))
    # Endpoints on the outer ring, but the middle grazes the hole's corner.
    grazing = pypgl.Segment(pypgl.Point(0, 4), pypgl.Point(4, 0))
    assert region.contains(grazing)
    assert not region.interiorContainsInterior(grazing)
    # And straight through the hole.
    assert not region.interiorContainsInterior(
        pypgl.Segment(pypgl.Point(0, 3), pypgl.Point(6, 3)))


def test_a_set_asks_about_one_component_at_a_time():
    left = pypgl.Polygon([0, 0, 2, 0, 2, 2, 0, 2]).asPolygonWithHoles()
    right = pypgl.Polygon([4, 0, 6, 0, 6, 2, 4, 2]).asPolygonWithHoles()
    both = pypgl.PolygonSet([left, right])
    assert both.interiorContainsInterior(
        pypgl.Segment(pypgl.Point(0, 0), pypgl.Point(2, 2)))
    assert both.interiorContainsInterior(
        pypgl.Segment(pypgl.Point(4, 0), pypgl.Point(6, 2)))
    # Spanning the gap lies in neither component.
    assert not both.interiorContainsInterior(
        pypgl.Segment(pypgl.Point(1, 1), pypgl.Point(5, 1)))


def test_a_degenerate_shape_separates_like_the_segment_it_spans():
    # A flattened Convex/Triangle/Polygon stands for the segment it spans, so
    # `separates` (and `crosses`, its conjunction) must answer as that segment
    # does -- in both directions.
    triangle = pypgl.Triangle(pypgl.Point(0, 0), pypgl.Point(10, 0),
                              pypgl.Point(5, 10))
    ends = [pypgl.Point(5, -5), pypgl.Point(5, 15)]
    segment = pypgl.Segment(*ends)
    assert segment.separates(triangle) and triangle.separates(segment)

    flat = [
        pypgl.Convex(ends),
        pypgl.Triangle(ends[0], pypgl.Point(5, 2), ends[1]),
        pypgl.Polygon([ends[0], pypgl.Point(5, 2), ends[1]]),
    ]
    for shape in flat:
        assert shape.separates(triangle)
        assert triangle.separates(shape)
        assert shape.crosses(triangle)
        assert triangle.crosses(shape)

    # A degenerate shape that stops short of the far side disconnects nothing,
    # again exactly as the segment does.
    short = [pypgl.Point(5, -5), pypgl.Point(5, 8)]
    assert not pypgl.Segment(*short).separates(triangle)
    assert not pypgl.Convex(short).separates(triangle)
    assert not triangle.separates(pypgl.Convex(short))
