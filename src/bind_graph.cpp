#include "bind_graph.h"

using namespace pypgl;

// Graph: pgl's undirected simple graph over points (algorithm/graph.hpp), the
// combinatorial companion of the geometric structures. It is what the
// visibility methods of Polygon / PolygonWithHoles / Triangulation return, and
// what a triangulation's 1-skeleton (Triangulation.asGraph) comes back as, so
// binding it is what makes those results usable rather than opaque.
//
// A vertex is a Point, which is hashable and totally ordered -- both of which
// pgl's Graph requires (the second only for edges()). The vertex type is a
// template parameter there, and pypgl instantiates it a second time in
// bind_arrangement.cpp over an arrangement's vertex handles, which is why the
// whole binding lives in the header bind_graph.h.
//
// Two deliberate departures from the C++ API, both about determinism:
// vertices(), edges(), neighbors() and closedNeighbors() are materialized and
// *sorted* copies rather than lazy views over a hash table, so a Python
// program's output does not depend on hashing; and degree() answers None for an
// absent vertex where C++ answers -1.

void bind_graph(nb::module_ &m) {
    bindGraph<Point>(m, "Graph");
}
