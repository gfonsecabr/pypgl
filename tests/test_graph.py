"""Graph: pgl's undirected simple graph over points, the combinatorial companion
of the geometric structures.

It is what the visibility methods and Triangulation.asGraph() hand back, so most
of what matters here is that it is a usable graph in its own right: weighted
algorithms taking a Python callable, and deterministic (sorted) iteration, where
C++ leaves the hash table's order unspecified.
"""

from fractions import Fraction

import pytest

from pypgl import Graph, Point, Polygon, Triangulation


def _square():
    return Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])


def _path_graph():
    g = Graph()
    g.addEdge(Point(0, 0), Point(1, 0))
    g.addEdge(Point(1, 0), Point(2, 0))
    return g


# --- building and inspecting ------------------------------------------------

def test_an_empty_graph_has_nothing_in_it():
    g = Graph()
    assert g.vertexCount() == 0 and g.edgeCount() == 0
    assert len(g) == 0
    assert list(g) == []


def test_adding_an_edge_adds_its_endpoints():
    g = Graph()
    g.addEdge(Point(0, 0), Point(1, 1))
    assert g.vertexCount() == 2
    assert g.containsEdge(Point(1, 1), Point(0, 0))    # undirected
    assert Point(0, 0) in g


def test_construction_from_a_list_of_pairs():
    g = Graph([(Point(0, 0), Point(1, 0)), (Point(1, 0), Point(2, 0))])
    assert g == _path_graph()


def test_removing_a_vertex_takes_its_edges_with_it():
    g = _path_graph()
    g.removeVertex(Point(1, 0))
    assert g.vertexCount() == 2 and g.edgeCount() == 0


def test_removing_an_edge_leaves_the_endpoints():
    g = _path_graph()
    g.removeEdge(Point(0, 0), Point(1, 0))
    assert g.vertexCount() == 3 and g.edgeCount() == 1


def test_degree_of_an_absent_vertex_is_none():
    # C++ answers -1 there; None is the Python spelling of the same thing.
    g = _path_graph()
    assert g.degree(Point(1, 0)) == 2
    assert g.degree(Point(9, 9)) is None
    assert g.maxDegree() == 2


def test_vertices_edges_and_neighbors_come_back_sorted():
    # C++ hands back lazy views over a hash table, in unspecified order; pypgl
    # materializes and sorts them so a program's output cannot depend on
    # hashing.
    g = _path_graph()
    assert g.vertices() == [Point(0, 0), Point(1, 0), Point(2, 0)]
    assert g.edges() == [
        (Point(0, 0), Point(1, 0)),
        (Point(1, 0), Point(2, 0)),
    ]
    assert g.neighbors(Point(1, 0)) == [Point(0, 0), Point(2, 0)]
    assert g.closedNeighbors(Point(0, 0)) == [Point(0, 0), Point(1, 0)]
    assert list(g) == g.vertices()


def test_asking_about_an_absent_vertex_raises():
    with pytest.raises(Exception):
        _path_graph().neighbors(Point(9, 9))


# --- traversal --------------------------------------------------------------

def test_components_separate_what_no_path_joins():
    g = _path_graph()
    g.addVertex(Point(9, 9))
    components = g.components()
    assert [len(c) for c in components] == [3, 1]
    assert g.bfs(Point(0, 0)) == [Point(0, 0), Point(1, 0), Point(2, 0)]
    assert g.bfs(Point(0, 0), 2) == [Point(0, 0), Point(1, 0)]
    assert g.bfs(Point(9, 9)) == [Point(9, 9)]


def test_biconnected_components_split_at_an_articulation_vertex():
    g = _path_graph()
    blocks = g.biconnectedComponents()
    assert len(blocks) == 2                       # each edge is a bridge
    assert all(len(block) == 2 for block in blocks)


def test_a_clique_cover_partitions_the_vertices():
    g = _square().visibilityGraph()               # a complete graph on 4 vertices
    cover = g.cliqueCover()
    assert sum(len(clique) for clique in cover) == g.vertexCount()
    assert len(cover) == 1                        # the whole thing is one clique


# --- weighted algorithms: the weight is a Python callable -------------------

def test_a_spanning_tree_keeps_every_vertex_and_component():
    g = _square().visibilityGraph()
    tree = g.spanningTree(lambda a, b: a.squaredDistance(b))
    assert tree.vertexCount() == g.vertexCount()
    assert tree.edgeCount() == g.vertexCount() - 1
    # Exact weights stay exact: the sides (16) beat the diagonals (32).
    assert all(a.squaredDistance(b) == 16 for a, b in tree.edges())


def test_a_spanning_tree_of_a_disconnected_graph_is_a_forest():
    g = _path_graph()
    g.addVertex(Point(9, 9))
    tree = g.spanningTree(lambda a, b: a.squaredDistance(b))
    assert tree.vertexCount() == 4
    assert tree.edgeCount() == 2                  # one tree per component
    assert len(tree.components()) == len(g.components())


def test_the_weight_may_be_exact_or_floating():
    g = _square().visibilityGraph()
    exact = g.spanningTree(lambda a, b: a.squaredDistance(b))
    inexact = g.spanningTree(lambda a, b: a.distance(b))
    assert exact.edgeCount() == inexact.edgeCount()
    # A Fraction weight is compared as a Fraction, not through a float.
    assert isinstance(Point(0, 0).squaredDistance(Point(1, 2)), Fraction)


def test_a_shortest_path_walks_the_graph():
    g = _path_graph()
    assert g.shortestPath(Point(0, 0), Point(2, 0), lambda a, b: a.distance(b)) == [
        Point(0, 0), Point(1, 0), Point(2, 0),
    ]
    # A vertex to itself is that vertex alone.
    assert g.shortestPath(Point(0, 0), Point(0, 0), lambda a, b: 1) == [Point(0, 0)]


def test_no_path_gives_an_empty_result():
    g = _path_graph()
    g.addVertex(Point(9, 9))
    assert g.shortestPath(Point(0, 0), Point(9, 9), lambda a, b: 1) == []
    assert g.shortestPath(Point(0, 0), Point(7, 7), lambda a, b: 1) == []


def test_a_lower_bound_turns_the_search_into_a_star():
    # The fifth argument is what tells the two overloads apart: an estimate of
    # what is left to travel, which steers the frontier toward the target
    # without changing the answer.
    g = _path_graph()
    length = lambda a, b: a.distance(b)
    assert g.shortestPath(Point(0, 0), Point(2, 0), length, length) == \
           g.shortestPath(Point(0, 0), Point(2, 0), length)
    # Straight-line distance is admissible here, since no edge is shorter than
    # the gap it spans. A bound of zero is admissible too and degenerates to
    # plain Dijkstra.
    assert g.shortestPath(Point(0, 0), Point(2, 0), length, lambda a, b: 0.0) == [
        Point(0, 0), Point(1, 0), Point(2, 0),
    ]


def test_a_star_keeps_the_endpoint_conventions():
    g = _path_graph()
    g.addVertex(Point(9, 9))
    weight = lambda a, b: a.distance(b)
    assert g.shortestPath(Point(0, 0), Point(0, 0), weight, weight) == [Point(0, 0)]
    assert g.shortestPath(Point(0, 0), Point(9, 9), weight, weight) == []
    assert g.shortestPath(Point(0, 0), Point(7, 7), weight, weight) == []


def test_a_star_weights_may_be_exact_too():
    # Both callables answer in the same weight type, and PyWeight compares and
    # adds through the Python protocols -- so an exact bound stays exact.
    g = _path_graph()
    path = g.shortestPath(
        Point(0, 0), Point(2, 0),
        lambda a, b: abs(a.x() - b.x()) + abs(a.y() - b.y()),
        lambda a, b: abs(a.x() - b.x()) + abs(a.y() - b.y()),
    )
    assert path == [Point(0, 0), Point(1, 0), Point(2, 0)]


# --- where graphs come from -------------------------------------------------

def test_a_triangulation_hands_back_its_1_skeleton():
    points = [Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4), Point(2, 2)]
    mesh = Triangulation(points)
    g = mesh.asGraph()
    assert g.vertexCount() == mesh.numVertices()
    assert g.edgeCount() == mesh.numEdges()
    assert all(p in g for p in points)


def test_a_graph_is_mutable_and_therefore_unhashable():
    with pytest.raises(TypeError):
        hash(_path_graph())
