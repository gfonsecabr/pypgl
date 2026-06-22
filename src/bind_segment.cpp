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
    cls.def("bbox", [](const Segment &s) { return s.bbox(); }, "Exact axis-aligned bounding box (a Rectangle).");

    bind_value_semantics<Segment>(cls);

    PGL_BIND_OPERATORS(cls, Segment);
    PGL_BIND_TRANSFORMS(cls, Segment);
    PGL_BIND_VERTEX_QUERIES(cls, Segment);
    PGL_BIND_INDEXING(cls, Segment);
    PGL_BIND_LINE_HELPERS(cls, Segment);
    PGL_BIND_COLLINEAR(cls, Segment);
    PGL_BIND_PARALLEL(cls, Segment);
    PGL_BIND_ALL_PREDICATES(cls, Segment);
    PGL_BIND_ALL_SQUARED_DISTANCE(cls, Segment);

    cls.def("intersection", [](const Segment &a, const Point &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Segment &a, const Segment &b) { return a.intersection(b); }, nb::arg("other"),
            "Intersection of two segments: None, a Point, or a Segment.");
    cls.def("intersection", [](const Segment &a, const OrientedSegment &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Segment &a, const Line &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Segment &a, const OrientedLine &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Segment &a, const Ray &b) { return a.intersection(b); }, nb::arg("other"));
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
    cls.def("bbox", [](const OrientedSegment &s) { return s.bbox(); }, "Exact axis-aligned bounding box (a Rectangle).");

    bind_value_semantics<OrientedSegment>(cls);

    PGL_BIND_OPERATORS(cls, OrientedSegment);
    PGL_BIND_TRANSFORMS(cls, OrientedSegment);
    PGL_BIND_VERTEX_QUERIES(cls, OrientedSegment);
    PGL_BIND_INDEXING(cls, OrientedSegment);
    PGL_BIND_LINE_HELPERS(cls, OrientedSegment);
    PGL_BIND_COLLINEAR(cls, OrientedSegment);
    PGL_BIND_PARALLEL(cls, OrientedSegment);
    PGL_BIND_ALL_PREDICATES(cls, OrientedSegment);
    PGL_BIND_ALL_SQUARED_DISTANCE(cls, OrientedSegment);

    cls.def("intersection", [](const OrientedSegment &a, const Point &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const OrientedSegment &a, const Segment &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const OrientedSegment &a, const OrientedSegment &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const OrientedSegment &a, const Line &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const OrientedSegment &a, const OrientedLine &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const OrientedSegment &a, const Ray &b) { return a.intersection(b); }, nb::arg("other"));
}
