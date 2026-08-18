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
//
// insert()/insertDelaunay() add a single vertex incrementally. For a
// triangulation built from a polygon, pgl documents inserting a point outside
// the closed polygon (the carved-away region, or beyond the hull) as
// undefined behavior rather than a checked rejection -- pypgl does not add
// its own guard, matching the C++ contract exactly.
//
// The Triangulation(points, segments) constructor below needs no ordering
// workaround unlike the Polygon/point-list pitfall further down: nanobind
// tries every overload without implicit conversions before it tries any with
// them, and points/segments already have the exact vector<Point>/
// vector<Segment> types the C++ overload wants, so it wins outright over the
// polygon constructor's (polygon, points, segments) overload, which would
// need an implicit list->Polygon conversion for the first argument -- even
// when segments is passed empty (verified: Triangulation(points, []) builds
// the plain unconstrained Delaunay triangulation, not a polygon boundary).

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
// accepts: the five directed shapes (traced in order along the query), the
// two chains (traced edge by edge, in chain order -- a chain is neither
// straight nor convex, so it gets its own walk), and the six region shapes (a
// connected convex query, reported in an unspecified order) -- see
// detail::TriangulationQuery in algorithm/triangulation.hpp. Polygon is
// deliberately not in this set: pgl does not (yet) support a non-convex
// polygon as a region query here.
#define PGL_BIND_TRIANGULATION_QUERY(cls, METHOD)      \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Segment);       \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::OrientedSegment); \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Line);          \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::OrientedLine);  \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Ray);           \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::MonotoneChain); \
    PGL_TRI_QUERY(cls, METHOD, ::pypgl::Polyline);      \
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

    // Same reasoning, and the same registration-order requirement, for the
    // region: a PolygonWithHoles is iterable in the Python layer too. Every
    // ring becomes constrained edges and the hole interiors are left out of the
    // domain, so the in-domain triangles cover exactly the part of the region
    // that has area -- a slit, having none, carries no triangle.
    cls.def("__init__",
            [](Triangulation *self, const PolygonWithHoles &region,
               const std::vector<Point> &points,
               const std::vector<Segment> &segments) {
                new (self) Triangulation(region, points, segments);
            },
            nb::arg("region"), nb::arg("points") = std::vector<Point>{},
            nb::arg("segments") = std::vector<Segment>{},
            "Build the constrained Delaunay triangulation of a region with holes, "
            "optionally adding interior points as extra vertices and/or interior "
            "segments as constrained edges (both assumed, not checked, to lie in "
            "the region).");

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

    // Registered after the plain points-only constructor above so a 1-arg
    // Triangulation(points) call keeps matching that one exactly (this ctor
    // has no default for segments, so it only matches 2-arg calls and
    // introduces no ambiguity).
    cls.def("__init__",
            [](Triangulation *self, const std::vector<Point> &points,
               const std::vector<Segment> &segments) {
                new (self) Triangulation(points, segments);
            },
            nb::arg("points"), nb::arg("segments"),
            "Build the conforming constrained Delaunay triangulation of a "
            "point set with constraint segments: every vertex is the union "
            "of points and the segments' endpoints, every segment is present "
            "as a constrained edge, and (unlike the polygon constructors) "
            "nothing is carved away -- the domain is the whole convex hull. "
            "The segments must be non-degenerate and pairwise non-crossing "
            "(sharing endpoints is fine), with no vertex in a segment's "
            "relative interior (assumed, not checked).");

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
    // Named `has` to mirror pgl, which renamed it from contains() so that a
    // mesh's "is this one of my triangles/edges" never reads like a shape's
    // geometric contains(); ShapeTree got the same rename.
    cls.def("has", [](const Triangulation &t, const Triangle &tri) { return t.has(tri); },
            nb::arg("triangle"), "Whether triangle is one of this triangulation's triangles.");
    cls.def("has", [](const Triangulation &t, const Segment &edge) { return t.has(edge); },
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

    // ---- incremental vertex insertion --------------------------------------
    cls.def("insert", [](Triangulation &t, const Point &p) { return t.insert(p); }, nb::arg("point"),
            "Insert point as a new vertex, subdividing the containing triangle "
            "or edge (or growing the hull, if point lies outside it); returns "
            "False only if point is already a vertex or the triangulation is "
            "empty. Split faces inherit their parent's constrained/domain "
            "flags. For a triangulation built from a polygon, point must lie "
            "in the closed polygon -- inserting one outside it (in the carved-"
            "away region between polygon and hull, or beyond the hull) is "
            "undefined behavior (not checked). Does not restore the Delaunay "
            "property; see insertDelaunay for that.");
    cls.def("insertDelaunay", [](Triangulation &t, const Point &p) { return t.insertDelaunay(p); }, nb::arg("point"),
            "Like insert, but also legalizes outward from the new vertex via "
            "Lawson flips (never flipping a constrained edge), preserving the "
            "constrained-Delaunay property. Same return convention and "
            "preconditions as insert.");

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
    // --- the domain: what the mesh covers, as a shape would answer ---
    //
    // The domain is the polygon for the polygon constructors and the convex
    // hull otherwise. These give exactly the answers the shape predicates of
    // the same name give for that region as a Polygon, boundary and all -- a
    // segment running along a boundary edge is contained and met, but neither
    // interior-contained nor interior-intersecting. They work on the mesh, so
    // the cost follows the triangles the query meets rather than the size of
    // the boundary. They ask a different question from has(), which is about
    // being a *cell* of the mesh rather than about how the domain covers a
    // shape geometrically.
    PGL_BIND_ALL_DOMAIN_PREDICATES(cls, Triangulation);

    // --- derived structures ---
    cls.def("asGraph", [](const Triangulation &t) { return t.asGraph(); },
            "The 1-skeleton as a Graph: its vertices are the numVertices() stored points "
            "and its edges the numEdges() edges of the visible mesh. A point identifies a "
            "vertex here, so the graph is keyed by the points themselves. A vertex with "
            "no in-domain edge -- one duplicated or collinear with every other point -- "
            "comes back isolated; the ghost vertex closing the mesh at infinity is "
            "internal and is not one of them.");
    cls.def("voronoiDiagram", [](const Triangulation &t) { return t.voronoiDiagram(); },
            "The unbounded Arrangement dual to this triangulation. The triangulation must "
            "be non-empty and its real triangles must form the Delaunay triangulation of "
            "all its vertices. Each face is labelled with the point that generated its "
            "Voronoi cell, so diagram.label(diagram.locateFace(q)) is the site nearest to "
            "q; on a Voronoi edge or vertex locateFace() picks one tied site by its "
            "infinitesimal-perturbation rule, and locateCell() plus the incident faces "
            "recovers all of them. Exact: the vertices are rational.");
    cls.def("convexPartition", [](const Triangulation &t) { return t.convexPartition(); },
            "Cut the domain into Convex pieces with pairwise disjoint interiors, each the "
            "union of one or more triangles, using at most four times the fewest pieces "
            "possible. A constrained edge is never deleted, so the constraints the "
            "triangulation was built with shape the partition.");
    cls.def("convexCovering", [](const Triangulation &t) { return t.convexCovering(); },
            "Cover the domain with Convex pieces grown one per triangle and then greedily "
            "selected and thinned. The pieces may overlap, are not guaranteed minimum, "
            "and never cross a constrained edge.");

    // --- visibility ---
    //
    // Sight is stopped by the boundary of the domain *and by every constrained
    // edge*, which is what makes `polygon.triangulation(walls).visibilityGraph()`
    // visibility inside the polygon among the segment obstacles `walls`. All of
    // these run a triangular expansion over the mesh, at a cost proportional to
    // the part of the domain a vertex actually sees.
    cls.def("visibilityGraph", [](const Triangulation &t) { return t.visibilityGraph(); },
            "The graph on the mesh's vertices joining two of them when the segment "
            "between them stays in the domain and crosses no constrained edge, even if "
            "it touches the boundary along the way.");
    cls.def("clearVisibilityGraph", [](const Triangulation &t) { return t.clearVisibilityGraph(); },
            "The strict reading: the segment must meet no boundary and no constrained "
            "edge except at its two ends. Always a subgraph of visibilityGraph().");
    cls.def("reducedVisibilityGraph", [](const Triangulation &t) { return t.reducedVisibilityGraph(); },
            "The subgraph of visibilityGraph() a shortest path can bend along: the "
            "boundary and wall edges plus the bitangents between reflex corners. Route "
            "between arbitrary points by adding them joined to visibleVertices().");
    cls.def("visibleVertices", [](const Triangulation &t, const Point &q) { return t.visibleVertices(q); },
            nb::arg("query"),
            "The mesh's vertices visible from the query point, counterclockwise around it "
            "from the lexicographically smallest -- sortAround()'s order.");
    cls.def("clearlyVisibleVertices", [](const Triangulation &t, const Point &q) { return t.clearlyVisibleVertices(q); },
            nb::arg("query"), "The strict counterpart of visibleVertices(): a subset of it.");
    cls.def("regularizedVisiblePolygon", [](const Triangulation &t, const Point &q) { return t.regularizedVisiblePolygon(q); },
            nb::arg("query"),
            "The region visible from the query point, as a Polygon: star-shaped about it "
            "and hence simply connected, however many holes or walls the domain has. "
            "Regularized, so a sightline grazing along a wall or slipping through a "
            "vertex contributes nothing -- what comes back always bounds area.");

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
