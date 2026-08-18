"""Visibility: the graphs and the visible region of a polygon, a region, or a
triangulation.

All of them are triangular expansion over one triangulation, and all of them
answer the same question under three conventions worth keeping apart:
``visibilityGraph`` lets a sightline graze the boundary, ``clearVisibilityGraph``
does not, and ``reducedVisibilityGraph`` keeps only the edges a taut path can
bend along. On a triangulation, a constrained edge blocks sight too -- which is
what makes ``polygon.triangulation(walls).visibilityGraph()`` visibility among
obstacles.
"""

import pytest

from pypgl import (
    Graph,
    Point,
    Polygon,
    PolygonWithHoles,
    Rectangle,
    Segment,
)


def _square(side=6):
    return Polygon([Point(0, 0), Point(side, 0), Point(side, side), Point(0, side)])


def _u_shape():
    """A U with two reflex corners at (4, 2) and (2, 2)."""
    return Polygon(
        [
            Point(0, 0), Point(6, 0), Point(6, 6), Point(4, 6),
            Point(4, 2), Point(2, 2), Point(2, 6), Point(0, 6),
        ]
    )


# --- the three conventions --------------------------------------------------

def test_a_convex_polygon_sees_all_of_itself():
    graph = _square().visibilityGraph()
    assert isinstance(graph, Graph)
    assert graph.vertexCount() == 4
    assert graph.edgeCount() == 6                     # the complete graph
    assert graph.containsEdge(Point(0, 0), Point(6, 6))


def test_a_reflex_corner_hides_part_of_the_polygon():
    u = _u_shape()
    full = u.visibilityGraph()
    assert full.vertexCount() == 8
    # The two arms cannot see across the notch.
    assert not full.containsEdge(Point(0, 6), Point(6, 6))


def test_the_clear_convention_forbids_grazing_the_boundary():
    u = _u_shape()
    clear = u.clearVisibilityGraph()
    full = u.visibilityGraph()
    assert clear.edgeCount() < full.edgeCount()
    # Every clearly visible pair is visible.
    assert all(full.containsEdge(a, b) for a, b in clear.edges())


def test_the_reduced_graph_is_what_a_shortest_path_can_bend_along():
    u = _u_shape()
    reduced = u.reducedVisibilityGraph()
    full = u.visibilityGraph()
    assert reduced.vertexCount() == full.vertexCount()
    assert all(full.containsEdge(a, b) for a, b in reduced.edges())
    # The boundary edges survive, since a wall is tangent to itself.
    assert reduced.containsEdge(Point(0, 0), Point(6, 0))


def test_a_shortest_path_around_a_notch_bends_at_a_reflex_corner():
    u = _u_shape()
    graph = u.reducedVisibilityGraph()
    source, target = Point(0, 6), Point(6, 6)
    for w in u.visibleVertices(source):
        graph.addEdge(source, w)
    for w in u.visibleVertices(target):
        graph.addEdge(target, w)
    path = graph.shortestPath(source, target, lambda a, b: a.distance(b))
    assert path[0] == source and path[-1] == target
    # It cannot go straight across, so it turns at the two reflex corners.
    assert Point(2, 2) in path and Point(4, 2) in path


# --- from a query point -----------------------------------------------------

def test_visible_vertices_are_ordered_around_the_query_point():
    u = _u_shape()
    seen = u.visibleVertices(Point(1, 1))
    assert seen                                        # something is visible
    assert seen == sorted(set(seen), key=seen.index)   # no repetition
    assert all(v in u.vertices() for v in seen)
    # The strict reading is a subset.
    assert set(u.clearlyVisibleVertices(Point(1, 1))) <= set(seen)


def test_the_visible_region_is_star_shaped_about_the_query_point():
    u = _u_shape()
    query = Point(1, 1)
    visible = u.regularizedVisiblePolygon(query)
    assert isinstance(visible, Polygon)
    assert query in visible
    assert visible.area() < u.area()                   # the notch hides some
    assert u.contains(visible)


def test_the_visible_region_of_a_convex_polygon_is_the_whole_of_it():
    square = _square()
    assert square.regularizedVisiblePolygon(Point(1, 1)).area() == square.area()


def test_the_visible_region_is_regularized():
    # A sightline grazing along a wall adds a spike with no area, which
    # regularization drops -- so what comes back always bounds area.
    u = _u_shape()
    visible = u.regularizedVisiblePolygon(Point(3, 1))
    assert visible.area() > 0
    assert not visible.isDegenerate()


# --- a region with a hole ---------------------------------------------------

def test_a_hole_blocks_sight_across_it():
    region = PolygonWithHoles(
        Polygon([Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]),
        [Polygon([Point(4, 4), Point(6, 4), Point(6, 6), Point(4, 6)])],
    )
    graph = region.visibilityGraph()
    assert graph.vertexCount() == 8                    # four outer, four hole
    assert not graph.containsEdge(Point(0, 0), Point(10, 10))
    # The visible region is still one simply connected polygon, however many
    # holes the domain has.
    visible = region.regularizedVisiblePolygon(Point(1, 1))
    assert isinstance(visible, Polygon)
    assert visible.area() < region.area()


# --- walls: a triangulation's constrained edges block sight -----------------

def test_a_constrained_edge_is_an_obstacle():
    room = _square(10)
    # Strictly inside the room: a constraint segment is assumed to lie in the
    # polygon's interior, which is where an obstacle belongs anyway.
    wall = Segment(4, 1, 4, 9)
    open_room = room.triangulation().visibilityGraph()
    walled = room.triangulation([wall]).visibilityGraph()
    assert open_room.containsEdge(Point(0, 0), Point(10, 10))
    assert not walled.containsEdge(Point(0, 0), Point(10, 10))
    # The wall's own endpoints joined the mesh as vertices.
    assert Point(4, 1) in walled and Point(4, 9) in walled


def test_a_triangulation_answers_the_same_three_conventions():
    mesh = _u_shape().triangulation()
    assert mesh.visibilityGraph().edgeCount() >= mesh.clearVisibilityGraph().edgeCount()
    assert mesh.reducedVisibilityGraph().vertexCount() == mesh.numVertices()
    assert mesh.visibleVertices(Point(1, 1))
    assert mesh.regularizedVisiblePolygon(Point(1, 1)).area() > 0


def test_a_polygon_and_its_triangulation_agree():
    u = _u_shape()
    assert u.visibilityGraph() == u.triangulation().visibilityGraph()
