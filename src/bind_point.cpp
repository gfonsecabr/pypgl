#include "common.h"

using namespace pypgl;

void bind_point(nb::module_ &m) {
    nb::class_<Point> cls(m, "Point");

    cls.def(nb::init<>());
    cls.def(nb::init<Num, Num>(), nb::arg("x"), nb::arg("y"),
            "Create a point. Coordinates accept int, fractions.Fraction, or "
            "\"a/b\" strings; float is rejected.");

    cls.def("x", [](const Point &p) { return p.x(); }, "X coordinate.");
    cls.def("y", [](const Point &p) { return p.y(); }, "Y coordinate.");

    bind_value_semantics<Point>(cls);

    PGL_BIND_PREDICATES(cls, Point, Point);
    PGL_BIND_PREDICATES(cls, Point, Segment);

    cls.def("intersection", [](const Point &a, const Point &b) { return a.intersection(b); },
            nb::arg("other"));
    cls.def("intersection", [](const Point &a, const Segment &b) { return a.intersection(b); },
            nb::arg("other"));

    cls.def("distance", [](const Point &a, const Point &b) { return a.distance(b); },
            nb::arg("other"), "Approximate Euclidean distance (float).");
    cls.def("squaredDistance", [](const Point &a, const Point &b) { return a.squaredDistance(b); },
            nb::arg("other"), "Exact squared Euclidean distance.");
}
