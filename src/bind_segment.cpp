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
    cls.def("length", [](const Segment &s) { return s.length(); }, "Approximate length (float).");
    cls.def("squaredLength", [](const Segment &s) { return s.squaredLength(); }, "Exact squared length.");

    bind_value_semantics<Segment>(cls);

    PGL_BIND_PREDICATES(cls, Segment, Point);
    PGL_BIND_PREDICATES(cls, Segment, Segment);

    cls.def("intersection", [](const Segment &a, const Point &b) { return a.intersection(b); },
            nb::arg("other"));
    cls.def("intersection", [](const Segment &a, const Segment &b) { return a.intersection(b); },
            nb::arg("other"),
            "Intersection of two segments: None, a Point, or a Segment.");
}
