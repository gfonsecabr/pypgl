#pragma once

// The Graph binding, written once as a template because pgl instantiates
// Graph<Vertex> over two different vertex types that pypgl exposes: the points
// of a visibility graph or a triangulation's 1-skeleton (bind_graph.cpp), and
// an arrangement's vertex handles, which include the symbolic one at infinity
// and so cannot be points at all (bind_arrangement.cpp).
//
// Everything below is spelled the same for both; only the class name and the
// docstrings' noun differ.

#include <nanobind/make_iterator.h>
#include <nanobind/stl/pair.h>

#include <algorithm>
#include <vector>

#include "common.h"

namespace pypgl {

// An edge weight computed by a Python callable.
//
// pgl's spanningTree/shortestPath take the weight type from whatever the
// callable returns, requiring only `<` (and `+` for the path), which is exactly
// what a Python number already offers -- int, float and Fraction alike. So
// rather than fixing one C++ number type here (and forcing every exact weight
// through a float, or every float through a Fraction), the weight *is* the
// Python object, compared and added through the Python protocols. An exact
// weight therefore stays exact, and a caller who wants floating-point Euclidean
// lengths gets those.
struct PyWeight {
    nb::object value;

    bool operator<(const PyWeight &other) const {
        int result = PyObject_RichCompareBool(value.ptr(), other.value.ptr(), Py_LT);
        if (result < 0)
            throw nb::python_error();
        return result == 1;
    }

    PyWeight operator+(const PyWeight &other) const {
        PyObject *sum = PyNumber_Add(value.ptr(), other.value.ptr());
        if (!sum)
            throw nb::python_error();
        return PyWeight{nb::steal(sum)};
    }
};

// Bind pgl::Graph<Vertex> as `name`. `noun` names a vertex in the docstrings
// ("point", "vertex handle").
template <class Vertex>
void bindGraph(nb::module_ &m, const char *name) {
    using Graph = pgl::Graph<Vertex>;
    using Edge = std::pair<Vertex, Vertex>;

    // Materialized, sorted copies of the lazy C++ views. pgl leaves the order
    // of both unspecified (they walk a hash table), which would make a Python
    // program's output depend on hashing; sorting costs one pass and makes
    // every result reproducible. Every vertex type here is totally ordered, so
    // this always applies.
    auto sortedVertices = [](const Graph &g) {
        std::vector<Vertex> result(g.begin(), g.end());
        std::sort(result.begin(), result.end());
        return result;
    };

    nb::class_<Graph> cls(m, name);

    cls.def(nb::init<>(), "Create an empty graph.");
    cls.def("__init__",
            [](Graph *self, const std::vector<Edge> &edges) {
                new (self) Graph();
                for (const auto &[u, v] : edges)
                    self->addEdge(u, v);
            },
            nb::arg("edges"),
            "Create a graph from a list of endpoint pairs, adding every endpoint. "
            "Self-loops are ignored: the graph is simple and undirected.");

    // --- building ---
    cls.def("addVertex", [](Graph &g, const Vertex &v) { g.addVertex(v); }, nb::arg("vertex"),
            "Add an isolated vertex, if it is not already present.");
    cls.def("addEdge", [](Graph &g, const Vertex &u, const Vertex &v) { g.addEdge(u, v); },
            nb::arg("u"), nb::arg("v"),
            "Add an undirected edge, adding either endpoint that is missing. A self-loop "
            "is ignored.");
    cls.def("removeEdge", [](Graph &g, const Vertex &u, const Vertex &v) { g.removeEdge(u, v); },
            nb::arg("u"), nb::arg("v"), "Remove an edge, leaving both endpoints in place.");
    cls.def("removeVertex", [](Graph &g, const Vertex &v) { g.removeVertex(v); }, nb::arg("vertex"),
            "Remove a vertex together with every edge incident to it.");
    cls.def("clear", [](Graph &g) { g.clear(); }, "Remove every vertex and edge.");

    // --- inspection ---
    cls.def("containsVertex", [](const Graph &g, const Vertex &v) { return g.containsVertex(v); },
            nb::arg("vertex"), "Whether the vertex is in the graph.");
    cls.def("containsEdge", [](const Graph &g, const Vertex &u, const Vertex &v) { return g.containsEdge(u, v); },
            nb::arg("u"), nb::arg("v"), "Whether the two vertices are adjacent.");
    cls.def("vertexCount", [](const Graph &g) { return g.vertexCount(); }, "Number of vertices.");
    cls.def("edgeCount", [](const Graph &g) { return g.edgeCount(); }, "Number of undirected edges.");
    cls.def("maxDegree", [](const Graph &g) { return g.maxDegree(); },
            "Largest number of neighbors of any vertex (0 for an empty graph).");
    cls.def("degree", [](const Graph &g, const Vertex &v) -> std::optional<int> {
                int d = g.degree(v);
                if (d < 0) return std::nullopt;
                return d;
            }, nb::arg("vertex"),
            "Number of neighbors of the vertex, or None when it is not in the graph. "
            "(C++ answers -1 there; None is the Python spelling of the same thing.)");
    cls.def("vertices", [sortedVertices](const Graph &g) { return sortedVertices(g); },
            "The vertices, sorted. C++ hands back a lazy view in unspecified (hash) "
            "order; this is a sorted copy, so a program's output does not depend on "
            "hashing.");
    cls.def("edges",
            [](const Graph &g) {
                std::vector<Edge> result;
                result.reserve(static_cast<std::size_t>(g.edgeCount()));
                for (const auto &e : g.edges())
                    result.emplace_back(e[0], e[1]);
                std::sort(result.begin(), result.end());
                return result;
            },
            "The undirected edges as sorted (u, v) pairs, each with its endpoints in "
            "increasing order and each appearing once.");
    cls.def("neighbors",
            [](const Graph &g, const Vertex &v) {
                std::vector<Vertex> result(g.neighbors(v).begin(), g.neighbors(v).end());
                std::sort(result.begin(), result.end());
                return result;
            },
            nb::arg("vertex"),
            "The neighbors of the vertex, sorted. Raises IndexError (C++ "
            "std::out_of_range) when the vertex is absent.");
    cls.def("closedNeighbors",
            [](const Graph &g, const Vertex &v) {
                auto set = g.closedNeighbors(v);
                std::vector<Vertex> result(set.begin(), set.end());
                std::sort(result.begin(), result.end());
                return result;
            },
            nb::arg("vertex"),
            "The neighbors of the vertex together with the vertex itself, sorted. "
            "Raises when the vertex is absent.");

    // --- traversal and structure ---
    cls.def("bfs", [](const Graph &g, const Vertex &v, int maxVertices) { return g.bfs(v, maxVertices); },
            nb::arg("vertex"), nb::arg("max_vertices") = 0,
            "The connected component of the vertex in breadth-first order, stopping "
            "after max_vertices when that is positive. Empty when the vertex is absent.");
    cls.def("components", [](const Graph &g) { return g.components(); },
            "The connected components, largest first. An isolated vertex forms a "
            "one-vertex component.");
    cls.def("biconnectedComponents", [](const Graph &g) { return g.biconnectedComponents(); },
            "The vertex sets of the vertex-biconnected blocks, largest first. A bridge "
            "comes back as a two-vertex block, an articulation vertex belongs to more "
            "than one block, and an isolated vertex belongs to none.");
    cls.def("cliqueCover", [](const Graph &g) { return g.cliqueCover(); },
            "A partition of the vertices into cliques, largest first, by DSATUR coloring "
            "of the complement graph. Every vertex appears in exactly one clique, but "
            "the number of cliques is not guaranteed minimum.");
    // Sorted like vertices()/edges(), for the same reason: C++ returns the
    // vertices in the order the greedy selected them, which is degree order
    // broken by the hash-table walk. Sorting fixes the *order* of the answer;
    // it cannot fix which vertices are in it, since equal-degree ties are
    // resolved inside pgl by that same walk. The docstring says so rather than
    // promising a stability the binding cannot deliver.
    cls.def("independentSet",
            [](const Graph &g) {
                std::vector<Vertex> result = g.independentSet();
                std::sort(result.begin(), result.end());
                return result;
            },
            "A maximal set of pairwise non-adjacent vertices, sorted, chosen greedily "
            "from the lowest-degree vertex up. Maximal, not maximum: every vertex "
            "outside it is adjacent to one inside, but a larger independent set may "
            "exist. Vertices of equal degree are considered in an unspecified order, so "
            "which of several equally good sets comes back may vary between runs -- only "
            "the ordering of the answer is fixed.");

    // --- weighted algorithms ---
    //
    // The weight callable is what pgl asks for, and it decides its own number
    // type: return Fractions (or ints) to stay exact, floats for Euclidean
    // lengths. It must be symmetric -- w(u, v) == w(v, u) -- since which of the
    // two values is used for an edge is otherwise unspecified.
    cls.def("spanningTree",
            [](const Graph &g, nb::callable weight) {
                return g.spanningTree([&](const Vertex &u, const Vertex &v) {
                    return PyWeight{weight(u, v)};
                });
            },
            nb::arg("weight"),
            "A minimum spanning tree, as another graph, under the given edge weight "
            "function w(u, v). A disconnected graph gives one minimum spanning tree per "
            "component, so the result always has the same vertices and the same "
            "components as this graph, isolated vertices included. Prim's algorithm, "
            "O(m log m) with one weight evaluation per edge.");
    cls.def("shortestPath",
            [](const Graph &g, const Vertex &source, const Vertex &target, nb::callable weight) {
                return g.shortestPath(source, target, [&](const Vertex &u, const Vertex &v) {
                    return PyWeight{weight(u, v)};
                });
            },
            nb::arg("source"), nb::arg("target"), nb::arg("weight"),
            "The vertices of a shortest path from source to target, both included, under "
            "the given edge weight function. Weights must be non-negative and add up "
            "with +, neither of which is checked. The path from a vertex to itself is "
            "that vertex alone, and an empty result means there is none -- the two lie "
            "in different components, or one of them is absent. Dijkstra's algorithm, "
            "O(m log m).");
    // A* is the same search with a second callable steering it: the lower bound
    // is added to the distance so far to order the frontier, so a bound that
    // knows where the target is expands far fewer vertices than Dijkstra. Both
    // callables answer in the same weight type -- PyWeight compares and adds
    // through the Python protocols either way -- so an exact Fraction bound
    // stays exact. The extra argument is what tells the two overloads apart.
    cls.def("shortestPath",
            [](const Graph &g, const Vertex &source, const Vertex &target,
               nb::callable weight, nb::callable lowerBound) {
                return g.shortestPath(
                    source, target,
                    [&](const Vertex &u, const Vertex &v) { return PyWeight{weight(u, v)}; },
                    [&](const Vertex &u, const Vertex &v) { return PyWeight{lowerBound(u, v)}; });
            },
            nb::arg("source"), nb::arg("target"), nb::arg("weight"), nb::arg("lowerBound"),
            "The same shortest path, found by A* instead: lowerBound(v, target) estimates "
            "what is left to travel and prioritizes the vertices that look closest. The "
            "estimate must be non-negative, must never exceed the true remaining "
            "distance, and must be zero at the target -- none of which is checked, and an "
            "overestimate simply returns a path that need not be shortest. It need not be "
            "consistent: a vertex is reopened whenever a shorter route to it turns up.");

    // --- container sugar (bound here rather than in __init__.py: a Graph is
    // not a shape, so it takes part in none of that file's loops) ---
    cls.def("__len__", [](const Graph &g) { return g.vertexCount(); });
    cls.def("__contains__", [](const Graph &g, const Vertex &v) { return g.containsVertex(v); });
    // Iteration goes through the materialized sorted list rather than a
    // make_iterator over the adjacency map: the order would otherwise be the
    // hash table's, and an iterator into it would be invalidated by any
    // mutation of the graph while a Python loop is running.
    cls.def("__iter__",
            [sortedVertices](const Graph &g) { return nb::iter(nb::cast(sortedVertices(g))); },
            "Iterate the vertices, sorted.");
    cls.def("__repr__", [name](const Graph &g) {
        return std::string(name) + "(" + std::to_string(g.vertexCount()) + " vertices, " +
               std::to_string(g.edgeCount()) + " edges)";
    });
    cls.def("__eq__", [](const Graph &a, const Graph &b) {
        if (a.vertexCount() != b.vertexCount() || a.edgeCount() != b.edgeCount())
            return false;
        for (const Vertex &v : a) {
            if (!b.containsVertex(v))
                return false;
            for (const Vertex &w : a.neighbors(v))
                if (!b.containsEdge(v, w))
                    return false;
        }
        return true;
    }, nb::is_operator());
    // Mutable, hence unhashable, following every other mutable pypgl class.
    cls.attr("__hash__") = nb::none();
}

}  // namespace pypgl
