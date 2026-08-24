#include "common.h"

using namespace pypgl;

void bind_segment(nb::module_ &m) {
    nb::class_<Segment> cls(m, "Segment");

    cls.def(nb::init<Point, Point>(), nb::arg("p"), nb::arg("q"),
            "Create a segment from two endpoints (stored sorted).");
    cls.def(nb::init<Num, Num, Num, Num>(), nb::arg("x1"), nb::arg("y1"),
            nb::arg("x2"), nb::arg("y2"),
            "Create a segment from four coordinates.");

    cls.def("min", [](const Segment &s) { return s.min(); }, "Lexicographically smaller endpoint.");
    cls.def("max", [](const Segment &s) { return s.max(); }, "Lexicographically larger endpoint.");
    cls.def("vertices", [](const Segment &s) { return s.vertices(); }, "The two endpoints.");
    cls.def("midpoint", [](const Segment &s) { return s.midpoint(); }, "Exact midpoint.");
    cls.def("length", [](const Segment &s) { return s.length(); }, "Approximate Euclidean (L2) length (float).");
    cls.def("squaredLength", [](const Segment &s) { return s.squaredLength(); }, "Exact squared length.");
    cls.def("lengthL1", [](const Segment &s) { return s.lengthL1(); }, "Exact Manhattan (L1) length.");
    cls.def("lengthLInf", [](const Segment &s) { return s.lengthLInf(); }, "Exact Chebyshev (L-infinity) length.");
    cls.def("asLine", [](const Segment &s) { return s.asLine(); }, "Supporting unoriented line.");
    cls.def("asPolyline", [](const Segment &s) { return s.asPolyline(); },
            "The same segment as a two-vertex Polyline.");
    cls.def("asHalfplaneIntersection", [](const Segment &s) { return s.asHalfplaneIntersection(); },
            "The same segment as a (degenerate) HalfplaneIntersection.");
    cls.def("bbox", [](const Segment &s) { return s.bbox(); }, "Exact axis-aligned bounding box (a Rectangle).");
    cls.def("containsEndpoint", [](const Segment &s, const Point &p) { return s.containsEndpoint(p); },
            nb::arg("point"), "Whether the point is one of the two endpoints.");

    bind_value_semantics<Segment>(cls);

    PGL_BIND_OPERATORS(cls, Segment);
    PGL_BIND_TRANSFORMS(cls, Segment);
    PGL_BIND_MINKOWSKI_CONVEX(cls, Segment);
    PGL_BIND_EROSION_CONVEX(cls, Segment);
    PGL_BIND_CONVEX_HULL(cls, Segment);
    PGL_BIND_VERTEX_QUERIES(cls, Segment);
    PGL_BIND_INDEXING(cls, Segment);
    PGL_BIND_LINE_HELPERS(cls, Segment);
    PGL_BIND_DEGENERACY_POINT(cls, Segment);
    PGL_BIND_XY_AT(cls, Segment);
    PGL_BIND_COLLINEAR(cls, Segment);
    PGL_BIND_PARALLEL(cls, Segment);
    PGL_BIND_ALL_PREDICATES(cls, Segment);
    PGL_BIND_ALL_SQUARED_DISTANCE(cls, Segment);
    PGL_BIND_ALL_L1LINF_DISTANCE(cls, Segment);
    PGL_BIND_ALL_HAUSDORFF_DISTANCE(cls, Segment);
    PGL_BIND_ALL_SAME_POINT_SET(cls, Segment);

    // Against a 0D/1D shape the result is connected (None, a Point or a
    // Segment); against a chain or a non-convex region it can come apart, and
    // is then a list of those same pieces.
    PGL_BIND_INTERSECTION_LINEAR(cls, Segment);
}

void bind_oriented_segment(nb::module_ &m) {
    nb::class_<OrientedSegment> cls(m, "OrientedSegment");

    cls.def(nb::init<Point, Point>(), nb::arg("source"), nb::arg("target"),
            "Create an oriented segment from source to target (order preserved).");
    cls.def(nb::init<Num, Num, Num, Num>(), nb::arg("x1"), nb::arg("y1"),
            nb::arg("x2"), nb::arg("y2"),
            "Create an oriented segment from four coordinates.");

    cls.def("source", [](const OrientedSegment &s) { return s.source(); }, "Source endpoint.");
    cls.def("target", [](const OrientedSegment &s) { return s.target(); }, "Target endpoint.");
    cls.def("min", [](const OrientedSegment &s) { return s.min(); }, "Lexicographically smaller endpoint.");
    cls.def("max", [](const OrientedSegment &s) { return s.max(); }, "Lexicographically larger endpoint.");
    cls.def("opposite", [](const OrientedSegment &s) { return s.opposite(); }, "Segment with source and target swapped.");
    cls.def("vertices", [](const OrientedSegment &s) { return s.vertices(); }, "The two endpoints.");
    cls.def("midpoint", [](const OrientedSegment &s) { return s.midpoint(); }, "Exact midpoint.");
    cls.def("length", [](const OrientedSegment &s) { return s.length(); }, "Approximate Euclidean (L2) length (float).");
    cls.def("squaredLength", [](const OrientedSegment &s) { return s.squaredLength(); }, "Exact squared length.");
    cls.def("lengthL1", [](const OrientedSegment &s) { return s.lengthL1(); }, "Exact Manhattan (L1) length.");
    cls.def("lengthLInf", [](const OrientedSegment &s) { return s.lengthLInf(); }, "Exact Chebyshev (L-infinity) length.");
    cls.def("asSegment", [](const OrientedSegment &s) { return s.asSegment(); }, "Unoriented segment with the same endpoints.");
    cls.def("asLine", [](const OrientedSegment &s) { return s.asLine(); }, "Supporting unoriented line.");
    cls.def("asOrientedLine", [](const OrientedSegment &s) { return s.asOrientedLine(); },
            "Supporting line, with the same orientation.");
    cls.def("asRay", [](const OrientedSegment &s) { return s.asRay(); },
            "Ray from the same source, through the target.");
    cls.def("bbox", [](const OrientedSegment &s) { return s.bbox(); }, "Exact axis-aligned bounding box (a Rectangle).");
    cls.def("containsEndpoint", [](const OrientedSegment &s, const Point &p) { return s.containsEndpoint(p); },
            nb::arg("point"), "Whether the point is one of the two endpoints.");

    bind_value_semantics<OrientedSegment>(cls);

    PGL_BIND_OPERATORS(cls, OrientedSegment);
    PGL_BIND_TRANSFORMS(cls, OrientedSegment);
    PGL_BIND_MINKOWSKI_CONVEX(cls, OrientedSegment);
    PGL_BIND_EROSION_CONVEX(cls, OrientedSegment);
    PGL_BIND_CONVEX_HULL(cls, OrientedSegment);
    PGL_BIND_VERTEX_QUERIES(cls, OrientedSegment);
    PGL_BIND_INDEXING(cls, OrientedSegment);
    PGL_BIND_LINE_HELPERS(cls, OrientedSegment);
    PGL_BIND_DEGENERACY_POINT(cls, OrientedSegment);
    PGL_BIND_XY_AT(cls, OrientedSegment);
    PGL_BIND_ORIENTED_HELPERS(cls, OrientedSegment);
    PGL_BIND_COLLINEAR(cls, OrientedSegment);
    PGL_BIND_PARALLEL(cls, OrientedSegment);
    PGL_BIND_ALL_PREDICATES(cls, OrientedSegment);
    PGL_BIND_ALL_SQUARED_DISTANCE(cls, OrientedSegment);
    PGL_BIND_ALL_L1LINF_DISTANCE(cls, OrientedSegment);
    PGL_BIND_ALL_HAUSDORFF_DISTANCE(cls, OrientedSegment);
    PGL_BIND_ALL_SAME_POINT_SET(cls, OrientedSegment);

    // An intersection is a point set, so an orientation plays no part in it:
    // these give exactly what the same unoriented segment would.
    PGL_BIND_INTERSECTION_LINEAR(cls, OrientedSegment);
}
