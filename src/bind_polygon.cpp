#include "common.h"

using namespace pypgl;

// Polygon: an arbitrary (possibly non-convex) simple polygon stored by its
// vertices plus a lazy translation offset, mirroring Convex's storage layout
// but making no convexity assumption. Like Convex it is bound **mutable**: the
// in-place operators (+=, -=, *=, /=) mutate in place to keep pgl's O(1)
// translate, so per the mutable-implies-unhashable rule it is bound with
// hashable = false (__hash__ is None) and can never be a dict key / set
// member, even though pgl itself has a std::hash<Polygon> specialization.
//
// Unlike the other indexable shapes, pgl does not implement
// Polygon::verticesContain(), so the PGL_BIND_VERTEX_QUERIES trio is not used
// here; pointInside() and index() are bound by hand instead. (pgl gained a
// non-convex pointInside() upstream: it cuts a diagonal or an ear at a convex
// vertex and takes an interior point of that, rather than the vertex average a
// convex shape can get away with.)
//
// The predicate and squared-distance matrices reuse the shared
// PGL_BIND_ALL_PREDICATES / PGL_BIND_ALL_SQUARED_DISTANCE macros in
// src/common.h, which now include both Polygon and Disk, so every
// already-bound shape's own matrix picks up a Polygon column and Disk column
// for free, and calling the macros here gives Polygon the reverse rows plus
// its own self-pair. A few pairs pgl has not implemented yet throw at
// runtime, exactly as elsewhere in the matrix.
//
// intersection() results follow pgl's return shape: against a 0D/1D other
// shape (Point/Segment/OrientedSegment/Line/OrientedLine/Ray) the result is a
// *list* of disjoint Point/Segment pieces — a non-convex polygon can meet a
// line in several places, unlike Convex's single optional piece. Against a 2D
// other shape (Polygon/Convex/Triangle/Rectangle/Halfplane) the result is a
// list of Point/Segment/Polygon pieces, plus possibly open chains: pgl's
// `Polyline` is only a documented stub (`std::vector<Point>`, no dedicated
// class yet — see shape/point.hpp), so it surfaces here as a plain
// `list[Point]`, exactly like any other bound std::vector.

void bind_polygon(nb::module_ &m) {
    nb::class_<Polygon> cls(m, "Polygon");
    cls.def(nb::init<>(), "Create an empty polygon (no vertices).");
    // The C++ range constructor is a template; bind it via a placement-new
    // factory like Convex's. Unlike Convex (which always hull-scans), Polygon's
    // normalization only reorders to canonical form (CCW, lexicographically
    // smallest vertex first) — it does not check simplicity — so `trusted` is
    // exposed too, matching the C++ default.
    cls.def("__init__",
            [](Polygon *self, const std::vector<Point> &points, bool trusted) {
                new (self) Polygon(points, trusted);
            },
            nb::arg("points"), nb::arg("trusted") = false,
            "Create a polygon from vertices given in boundary order. Unless "
            "trusted is set, the vertices are normalized to canonical form (CCW, "
            "lexicographically smallest vertex first); normalization does not "
            "check simplicity -- use isSimple() to verify.");

    cls.def("vertices", [](const Polygon &p) { return p.vertices(); }, "Vertices in canonical boundary order.");
    cls.def("edges", [](const Polygon &p) { return p.edges(); }, "Boundary edges as segments.");
    cls.def("orientedEdges", [](const Polygon &p) { return p.orientedEdges(); }, "Boundary edges as oriented segments.");
    cls.def("twiceArea", [](const Polygon &p) { return p.twiceArea(); }, "Exact twice the unsigned area (shoelace formula).");
    cls.def("area", [](const Polygon &p) { return p.area(); }, "Exact area.");
    cls.def("centroid", [](const Polygon &p) { return p.centroid(); }, "Exact area-weighted centroid.");
    cls.def("verticesCentroid", [](const Polygon &p) { return p.verticesCentroid(); },
            "Exact centroid of the vertex set (the average of the vertices, not area-weighted).");
    cls.def("isDegenerate", [](const Polygon &p) { return p.isDegenerate(); }, "Whether the polygon has zero area.");
    cls.def("isSimple", [](const Polygon &p) { return p.isSimple(); },
            "Whether the boundary does not touch or cross itself.");
    cls.def("isConvex", [](const Polygon &p) { return p.isConvex(); },
            "Whether every boundary turn has the same orientation (meaningful only for a simple polygon).");
    cls.def("diameter", [](const Polygon &p) { return p.diameter(); }, "Longest distance as a segment between two vertices.");
    cls.def("bbox", [](const Polygon &p) { return p.bbox(); }, "Exact axis-aligned bounding box (a Rectangle).");

    // Polygon has pointInside() and index() (an O(n) vertex scan) but not
    // verticesContain() (see file comment), so these are bound by hand instead
    // of via PGL_BIND_VERTEX_QUERIES, the same way bind_disk.cpp does it.
    cls.def("pointInside", [](const Polygon &p) { return p.pointInside(); },
            "An exact point strictly inside the polygon (the polygon must be "
            "simple and non-degenerate).");
    cls.def("index", [](const Polygon &p, const Point &pt) -> std::optional<std::ptrdiff_t> {
                auto i = p.index(pt);
                if (i < 0) return std::nullopt;
                return i;
            }, nb::arg("point"), "Index of the vertex equal to point, or None if none.");

    // Mutable, variable-size like Convex (see file comment): bound unhashable.
    bind_value_semantics<Polygon>(cls, /*hashable=*/false);

    // Unlike Convex, Polygon has free operators (operator+/-/*//), so the
    // value-returning forms reuse the shared macro directly instead of being
    // synthesized from the compound-assignment members.
    PGL_BIND_OPERATORS(cls, Polygon);
    // In-place operators mutate the object (preserving pgl's O(1) translate)
    // and return self, mirroring Convex.
    cls.def("__iadd__", [](nb::object self, const Point &p) { nb::cast<Polygon &>(self) += p; return self; }, nb::is_operator());
    cls.def("__isub__", [](nb::object self, const Point &p) { nb::cast<Polygon &>(self) -= p; return self; }, nb::is_operator());
    cls.def("__imul__", [](nb::object self, const Num &k) { nb::cast<Polygon &>(self) *= k; return self; }, nb::is_operator());
    cls.def("__itruediv__", [](nb::object self, const Num &k) { nb::cast<Polygon &>(self) /= k; return self; }, nb::is_operator());

    // Value-returning transforms (new polygon) plus their in-place
    // counterparts (mutate, return None), mirroring Convex.
    PGL_BIND_TRANSFORMS(cls, Polygon);
    cls.def("rotate90", [](Polygon &p, int k) { p.rotate90(k); }, nb::arg("k") = 1,
            "Rotate the polygon in place by 90*k degrees about the origin.");
    cls.def("scaleUpX", [](Polygon &p, const Num &k) { p.scaleUpX(k); }, nb::arg("scalar"),
            "Multiply the polygon's x-coordinates by scalar in place.");
    cls.def("scaleUpY", [](Polygon &p, const Num &k) { p.scaleUpY(k); }, nb::arg("scalar"),
            "Multiply the polygon's y-coordinates by scalar in place.");
    cls.def("scaleDownX", [](Polygon &p, const Num &k) { p.scaleDownX(k); }, nb::arg("scalar"),
            "Divide the polygon's x-coordinates by scalar in place.");
    cls.def("scaleDownY", [](Polygon &p, const Num &k) { p.scaleDownY(k); }, nb::arg("scalar"),
            "Divide the polygon's y-coordinates by scalar in place.");

    // Shortcuts for Triangulation(polygon) / Triangulation(polygon, segments)
    // -- see src/bind_triangulation.cpp, which binds the general constructor.
    cls.def("triangulation", [](const Polygon &p) { return p.triangulation(); },
            "Constrained Delaunay triangulation of this polygon (must be simple "
            "and non-degenerate). Equivalent to Triangulation(self).");
    cls.def("triangulation",
            [](const Polygon &p, const std::vector<Segment> &segments) { return p.triangulation(segments); },
            nb::arg("segments"),
            "Constrained Delaunay triangulation of this polygon with the given "
            "interior constraint segments (assumed, not checked, to lie inside "
            "self). Equivalent to Triangulation(self, segments=segments).");

    cls.def("untangle", [](Polygon &p) { p.untangle(); },
            "Make the polygon simple in place by flipping crossing edges and "
            "removing redundant vertices. Relies on exact orientation "
            "predicates; termination is not guaranteed for float coordinates "
            "(not a concern here, since pypgl only binds exact ERational).");

    PGL_BIND_INDEXING(cls, Polygon);
    // Both shared macros now include Disk (see common.h), so these two calls
    // also cover the Polygon<->Disk pairing.
    PGL_BIND_ALL_PREDICATES(cls, Polygon);
    PGL_BIND_ALL_SQUARED_DISTANCE(cls, Polygon);
    // Polygon has no squaredHausdorffDistance/hausdorffDistanceL1/LInf (pgl
    // excludes it from that family -- a non-convex polygon would need a
    // Voronoi-based approach; see PGL_BIND_ALL_HAUSDORFF_DISTANCE in
    // common.h), but it does get the full distanceL1/distanceLInf cross
    // product like every other non-Disk shape.
    PGL_BIND_ALL_L1LINF_DISTANCE(cls, Polygon);

    cls.def("intersection", [](const Polygon &a, const Point &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Polygon &a, const Segment &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Polygon &a, const OrientedSegment &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Polygon &a, const Line &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Polygon &a, const OrientedLine &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Polygon &a, const Ray &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Polygon &a, const Halfplane &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Polygon &a, const Triangle &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Polygon &a, const Rectangle &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Polygon &a, const Convex &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Polygon &a, const Polygon &b) { return a.intersection(b); }, nb::arg("other"));
}
