#include "common.h"

using namespace pypgl;

// Triangulation: a mutable mesh over a fixed vertex set (Delaunay from a
// point set, constrained Delaunay from a simple Polygon, or built directly
// from an explicit triangle/edge set -- see algorithm/triangulation.hpp).
// Bound over the module's own Triangle/Segment pair (::pypgl::Triangulation
// in common.h), so it needs no new numeric instantiation.
//
// Unlike every other bound type, a Triangulation is not itself a "shape"
// with a fixed extent -- it has no contains(Point)/pointInside/index/get --
// so it is deliberately left out of the size()/get()/__contains__ sugar
// wired up in pypgl/__init__.py and src/stubgen_patterns.txt for every other
// class (the same way Canvas is excluded there).
//
// It also carries no label support: TriangleLabel/SegmentLabel both resolve
// to pgl::NoLabel for the module's plain Triangle/Segment, so label() and
// labeled construction have nothing to expose.
//
// visitTriangles/visitEdges (the C++ visitor-callback overloads) are not
// bound -- every other traversal in pypgl already returns a materialized
// list rather than taking a Python callback, and triangles()/edges() already
// give the same information without one.
//
// Connectivity queries take mesh-shaped arguments (Triangle/Segment/Point)
// that must actually belong to this triangulation -- pgl returns an empty
// result (or None) rather than throwing when they don't, and that is left
// as-is here.

namespace {

// One query overload (self.METHOD(query)) for a shape type accepted by
// Triangulation's directed (segment/line-like) or region (point/bounded 2D)
// traversal.
#define PGL_TRI_QUERY(cls, METHOD, QueryT)                    \
    cls.def(#METHOD,                                          \
            [](const Triangulation &self, const QueryT &q) {  \
                return self.METHOD(q);                        \
            },                                                \
            nb::arg("query"))

// METHOD bound against every query type pgl's Triangulation traversal
// accepts: the five directed shapes (traced in order along the query) and
// the six region shapes (a connected convex query, reported in an
// unspecified order) -- see detail::TriangulationQuery in
// algorithm/triangulation.hpp. Polygon is deliberately not in this set: pgl
// does not (yet) support a non-convex polygon as a region query here.
#define PGL_BIND_TRIANGULATION_QUERY(cls, METHOD)      \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Segment);       \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::OrientedSegment); \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Line);          \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::OrientedLine);  \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Ray);           \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Point);         \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Triangle);      \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Rectangle);     \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Convex);        \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Disk);          \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Halfplane)

}  // namespace

void bind_triangulation(nb::module_ &m) {
    nb::class_<Triangulation> cls(m, "Triangulation");

    cls.def(nb::init<>(), "Create an empty triangulation (no vertices).");

    // Registered before the vector<Point>/vector<Segment>/vector<Triangle>
    // overloads below, and this order matters: pypgl/__init__.py makes every
    // shape (Polygon included) iterable/sized for its own `in`/indexing
    // sugar, which means a bare Polygon also satisfies nanobind's generic
    // "sequence of Point" conversion for the vector<Point> overload. nanobind
    // tries __init__ overloads in registration order and takes the first
    // that matches, so this one -- an exact Polygon match, no conversion
    // needed -- must come first, or a positional Triangulation(polygon) call
    // would silently build the *unconstrained* Delaunay triangulation of the
    // polygon's vertices instead (same triangle count for a convex polygon,
    // so the mistake is not even obviously wrong -- just missing every
    // constrained boundary edge).
    cls.def("__init__",
            [](Triangulation *self, const Polygon &polygon,
               const std::vector<Point> &points,
               const std::vector<Segment> &segments) {
                new (self) Triangulation(polygon, points, segments);
            },
            nb::arg("polygon"), nb::arg("points") = std::vector<Point>{},
            nb::arg("segments") = std::vector<Segment>{},
            "Build the constrained Delaunay triangulation of a simple "
            "polygon (convex or not), optionally adding interior points as "
            "extra vertices and/or interior segments as constrained edges "
            "(both assumed, not checked, to lie inside polygon).");

    cls.def("__init__",
            [](Triangulation *self, const std::vector<Triangle> &triangles) {
                new (self) Triangulation(triangles);
            },
            nb::arg("triangles"),
            "Build a triangulation from a set of triangles tiling a region "
            "without overlaps; adjacency, the boundary, and the "
            "segment-to-edge map are computed automatically.");

    cls.def("__init__",
            [](Triangulation *self, const std::vector<Segment> &edges) {
                new (self) Triangulation(edges);
            },
            nb::arg("edges"),
            "Build a triangulation from its set of edges; the triangular "
            "faces are recovered from the connectivity (every bounded face "
            "must be a triangle).");

    cls.def("__init__",
            [](Triangulation *self, const std::vector<Point> &points) {
                new (self) Triangulation(points);
            },
            nb::arg("points"),
            "Build the Delaunay triangulation of a set of points (points "
            "collinear with all others, or duplicated, simply carry no "
            "incident triangle).");

    // ---- sizes -------------------------------------------------------
    cls.def("numVertices", [](const Triangulation &t) { return t.numVertices(); },
            "Number of real vertices.");
    cls.def("numTriangles", [](const Triangulation &t) { return t.numTriangles(); },
            "Number of triangles (excludes ghost and out-of-domain fill triangles).");
    cls.def("numEdges", [](const Triangulation &t) { return t.numEdges(); },
            "Number of undirected edges incident to the visible triangulation.");
    cls.def("empty", [](const Triangulation &t) { return t.empty(); },
            "Whether the triangulation stores no in-domain triangles.");

    // ---- membership --------------------------------------------------
    cls.def("contains", [](const Triangulation &t, const Triangle &tri) { return t.contains(tri); },
            nb::arg("triangle"), "Whether triangle is one of this triangulation's triangles.");
    cls.def("contains", [](const Triangulation &t, const Segment &edge) { return t.contains(edge); },
            nb::arg("edge"), "Whether edge is an edge incident to the visible triangulation.");

    // ---- navigation ----------------------------------------------------
    cls.def("otherTriangle",
            [](const Triangulation &t, const Triangle &triangle, const Segment &shared) {
                return t.otherTriangle(triangle, shared);
            },
            nb::arg("triangle"), nb::arg("shared"),
            "The triangle on the other side of shared from triangle, or None if "
            "that edge is on the boundary (or the arguments are not part of the mesh).");
    cls.def("edgeAdjacentTriangles",
            [](const Triangulation &t, const Triangle &triangle) { return t.edgeAdjacentTriangles(triangle); },
            nb::arg("triangle"), "The (up to three) triangles sharing an edge with triangle.");
    cls.def("vertexAdjacentTriangles",
            [](const Triangulation &t, const Triangle &triangle) { return t.vertexAdjacentTriangles(triangle); },
            nb::arg("triangle"),
            "The triangles sharing at least one vertex with triangle (excluding "
            "it); a superset of edgeAdjacentTriangles.");
    cls.def("incidentTriangles",
            [](const Triangulation &t, const Segment &edge) { return t.incidentTriangles(edge); },
            nb::arg("edge"), "The (up to two) triangles incident to edge.");
    cls.def("incidentTriangles",
            [](const Triangulation &t, const Point &vertex) { return t.incidentTriangles(vertex); },
            nb::arg("vertex"),
            "The triangles incident to vertex, in rotational order (empty if "
            "vertex is not a vertex of the triangulation).");

    cls.def("triangles", [](const Triangulation &t) { return t.triangles(); }, "All triangles, sorted.");
    cls.def("edges", [](const Triangulation &t) { return t.edges(); }, "All edges, sorted.");

    // ---- traversal along a query, or over a region --------------------
    PGL_BIND_TRIANGULATION_QUERY(cls, trianglesIntersecting);
    PGL_BIND_TRIANGULATION_QUERY(cls, trianglesInteriorIntersecting);
    PGL_BIND_TRIANGULATION_QUERY(cls, edgesIntersecting);
    PGL_BIND_TRIANGULATION_QUERY(cls, edgesInteriorIntersecting);

    // ---- point location -------------------------------------------------
    cls.def("locate", [](const Triangulation &t, const Point &point) { return t.locate(point); },
            nb::arg("point"),
            "The (closed) triangle containing point, or None if it lies outside "
            "the triangulated region (or the triangulation is empty).");

    // ---- constrained edges ----------------------------------------------
    cls.def("isConstrained", [](const Triangulation &t, const Segment &edge) { return t.isConstrained(edge); },
            nb::arg("edge"), "Whether edge is flagged as constrained.");
    cls.def("setConstrained",
            [](Triangulation &t, const Segment &edge, bool value) { t.setConstrained(edge, value); },
            nb::arg("edge"), nb::arg("value") = true,
            "Flag (or clear) edge as constrained on both incident sides.");

    // ---- mutation ---------------------------------------------------------
    cls.def("flippable", [](const Triangulation &t, const Segment &edge) { return t.flippable(edge); },
            nb::arg("edge"), "Whether edge can be flipped (unconstrained, interior, convex quad).");
    cls.def("flip", [](Triangulation &t, const Segment &edge) { return t.flip(edge); },
            nb::arg("edge"),
            "Flip edge, replacing it by the opposite diagonal; returns the new "
            "diagonal, or None if edge is not flippable.");
    cls.def("flippable",
            [](const Triangulation &t, const std::vector<Segment> &edges) { return t.flippable(edges); },
            nb::arg("edges"),
            "Whether every edge in edges can be flipped simultaneously (each "
            "individually flippable, and their quads pairwise disjoint).");
    cls.def("flip",
            [](Triangulation &t, const std::vector<Segment> &edges) { return t.flip(edges); },
            nb::arg("edges"),
            "Flip every edge in edges at once if the whole set allows it "
            "(all-or-nothing); returns the new diagonals in edges' order, or "
            "None if the set is not simultaneously flippable.");

    // ---- validation ------------------------------------------------------
    cls.def("checkInvariants", [](const Triangulation &t) { return t.checkInvariants(); },
            "Check the structural invariants (orientation + neighbor symmetry); "
            "intended for debugging/assertions.");

    cls.def("__repr__", [](const Triangulation &t) {
        std::ostringstream out;
        out << "Triangulation(numVertices=" << t.numVertices()
            << ", numTriangles=" << t.numTriangles() << ")";
        return out.str();
    });
}
