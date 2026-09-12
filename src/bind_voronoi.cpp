#include "bind_arrangement.h"

using namespace pypgl;

// The Voronoi diagrams of a point set (algorithm/voronoi.hpp): the ordinary
// diagram, its order-k generalization, and the farthest-point diagram. Each is
// an unbounded Arrangement whose faces are labeled with the sites that own them,
// so point location on the diagram *is* the nearest- (or farthest-) site query.
//
// The ordinary and the farthest-point diagrams label every face with one site,
// which makes them Arrangement<Point, Point> -- the class bind_arrangement.cpp
// already binds, and the one Triangulation.voronoiDiagram returns. The order-k
// diagram labels a face with the k sites nearest to it, in their order in the
// input, which takes a std::vector<Point> label and therefore its own class,
// PointListArrangement, bound here from the shared template. k = 1 still goes
// through the order-k overload and answers a PointListArrangement of one-element
// labels, mirroring C++: which overload is called decides the result type, not
// the value of k.
//
// The power diagrams, over disks, are bind_powerdiagram.cpp.

void bind_voronoi(nb::module_ &m) {
    bindArrangement<std::vector<Point>>(
        m, "PointListArrangement",
        "An arrangement whose edges and faces carry a list of points as their label: "
        "what the order-k voronoiDiagram(sites, k) returns.",
        "The label of a face: for an order-k Voronoi diagram, the k sites nearest to "
        "every point of the face, in their order in the input list.",
        "The label of an edge. A diagram leaves it empty and gives it no meaning; "
        "setLabel() overwrites it.");

    m.def("voronoiDiagram",
          [](const std::vector<Point> &sites) { return pgl::voronoiDiagram(sites); },
          nb::arg("sites"),
          "The Voronoi diagram of the points in sites, as an unbounded Arrangement whose "
          "every face is labeled with the one site nearest to it, so "
          "diagram.label(diagram.locateFace(q)) is the site nearest to q. On a diagram "
          "edge or vertex the query ties, and locateFace() picks one tied face by its "
          "infinitesimal-perturbation rule; locateCell() plus the incident faces "
          "recovers all of them. Repeated sites share a cell, which carries one of them. "
          "Exact: the vertices are rational. O(n log n); raises ValueError for no sites.");
    m.def("voronoiDiagram",
          [](const std::vector<Point> &sites, int k) { return pgl::voronoiDiagram(sites, k); },
          nb::arg("sites"), nb::arg("k"),
          "The order-k Voronoi diagram of the points in sites, as an unbounded "
          "PointListArrangement whose every face is labeled with the k sites nearest to "
          "it, in their order in sites. A face is the region where one set of k sites is "
          "nearer than every other site, and the sites of two neighboring faces differ by "
          "a single swap; empty cells never appear, so there are far fewer faces than "
          "k-element subsets. Built by Lee's refinement, O(k^2 n log n) for sites whose "
          "cells have boundedly many neighbors; repeated or all-collinear sites fall back "
          "to cutting every bisector against every site, O(n^3 log n). Raises ValueError "
          "unless 1 <= k <= len(sites).");
    m.def("farthestVoronoiDiagram",
          [](const std::vector<Point> &sites) { return pgl::farthestVoronoiDiagram(sites); },
          nb::arg("sites"),
          "The farthest-point Voronoi diagram of the points in sites, as an unbounded "
          "Arrangement whose every face is labeled with the one site *farthest* from it. "
          "Only a vertex of the convex hull owns a cell, a site the hull contains being "
          "strictly farthest nowhere; every cell is unbounded, so the diagram is a tree of "
          "segments and rays with no bounded face. Repeated sites share a cell, which "
          "carries the first of them. O(n log n + h^3) for h hull vertices; raises "
          "ValueError for no sites.");
}
