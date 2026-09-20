#include "common.h"

using namespace pypgl;

// Empty triangles and quadrilaterals of a point set (algorithm/emptypolygons.hpp).
//
// A polygon is *empty* with respect to a point set when its vertices belong to
// the set and no other point of the set lies in the closed polygon -- a point
// on an edge blocks it exactly as much as one inside. Only non-degenerate
// polygons count: three collinear points are no empty triangle, and every
// vertex of an empty quadrilateral is a proper corner rather than a straight
// angle. A quadrilateral must be simple, and is convex only where the function
// says so. The input is read as a *set*: coincident points count once.
//
// Three families, each in three forms -- all of them, those through one given
// vertex, and those through one given edge (a side of a triangle, a diagonal of
// a quadrilateral). The vertex and the edge's endpoints need not belong to the
// point set; each is treated as one of its points.
//
// pgl pairs every find* with a visit* taking an early-stopping callback. Only
// the find* forms are bound, as for every other pypgl traversal
// (Triangulation's visitTriangles, ShapeTree's visitIntersecting): a Python
// caller gets a materialized list, and stops early by not asking for the rest.
//
// The edge forms take a Segment or an OrientedSegment, which is the pair pgl's
// own constraint accepts, so each is bound twice.

namespace {

// Both spellings of one edge-form overload, for the three families.
#define PGL_BIND_EMPTY_EDGE(m, NAME, FN, DOC)                                                   \
    m.def(NAME,                                                                                 \
          [](const std::vector<Point> &points, const Segment &e) { return pgl::FN(points, e); },\
          nb::arg("points"), nb::arg("e"), DOC);                                                \
    m.def(NAME,                                                                                 \
          [](const std::vector<Point> &points, const OrientedSegment &e) {                      \
              return pgl::FN(points, e);                                                        \
          },                                                                                    \
          nb::arg("points"), nb::arg("e"), DOC)

}  // namespace

void bind_emptypolygons(nb::module_ &m) {
    // --- Empty triangles ---
    m.def("findEmptyTriangles",
          [](const std::vector<Point> &points) { return pgl::findEmptyTriangles(points); },
          nb::arg("points"),
          "Return every empty triangle of a point set, in O(n^2 log n + k) time for n "
          "distinct points and k triangles.");
    m.def("findEmptyTriangles",
          [](const std::vector<Point> &points, const Point &p) {
              return pgl::findEmptyTriangles(points, p);
          },
          nb::arg("points"), nb::arg("p"),
          "Return every empty triangle of a point set with p as a vertex, in "
          "O(n log n + k) time. p need not be one of the points; it is treated as one.");
    PGL_BIND_EMPTY_EDGE(m, "findEmptyTriangles", findEmptyTriangles,
                        "Return every empty triangle of a point set with e as a side, in "
                        "O(n log n) time. The endpoints of e need not be points of the set; "
                        "they are treated as such. A point of the set inside e blocks every "
                        "triangle, and a zero-length e has none.");

    // --- Empty quadrilaterals ---
    // Simple, possibly non-convex, and returned as Polygon.
    m.def("findEmptyQuadrilaterals",
          [](const std::vector<Point> &points) { return pgl::findEmptyQuadrilaterals(points); },
          nb::arg("points"),
          "Return every empty quadrilateral of a point set, simple and possibly "
          "non-convex, as polygons. O(n^2 log n + t + k) time for n distinct points, t "
          "empty triangles and k quadrilaterals.");
    m.def("findEmptyQuadrilaterals",
          [](const std::vector<Point> &points, const Point &p) {
              return pgl::findEmptyQuadrilaterals(points, p);
          },
          nb::arg("points"), nb::arg("p"),
          "Return every empty quadrilateral of a point set with p as a vertex, as "
          "polygons. p need not be one of the points; it is treated as one.");
    PGL_BIND_EMPTY_EDGE(m, "findEmptyQuadrilaterals", findEmptyQuadrilaterals,
                        "Return every empty quadrilateral of a point set having e as an "
                        "inside diagonal, as polygons, in O(n log n + k) time. The endpoints "
                        "of e need not be points of the set; they are treated as such. A "
                        "point of the set inside e blocks every quadrilateral, and a "
                        "zero-length e has none.");

    // --- Empty convex quadrilaterals ---
    // Convex by construction, so these come back as Convex rather than Polygon.
    m.def("findEmptyConvexQuadrilaterals",
          [](const std::vector<Point> &points) {
              return pgl::findEmptyConvexQuadrilaterals(points);
          },
          nb::arg("points"),
          "Return every empty convex quadrilateral of a point set. O(n^2 log n + t + k) "
          "time for n distinct points, t empty triangles and k quadrilaterals.");
    m.def("findEmptyConvexQuadrilaterals",
          [](const std::vector<Point> &points, const Point &p) {
              return pgl::findEmptyConvexQuadrilaterals(points, p);
          },
          nb::arg("points"), nb::arg("p"),
          "Return every empty convex quadrilateral of a point set with p as a vertex. p "
          "need not be one of the points; it is treated as one.");
    PGL_BIND_EMPTY_EDGE(m, "findEmptyConvexQuadrilaterals", findEmptyConvexQuadrilaterals,
                        "Return every empty convex quadrilateral of a point set having e as "
                        "a diagonal, in O(n log n + k) time. The endpoints of e need not be "
                        "points of the set; they are treated as such. A point of the set "
                        "inside e blocks every quadrilateral, and a zero-length e has none.");
}

#undef PGL_BIND_EMPTY_EDGE
