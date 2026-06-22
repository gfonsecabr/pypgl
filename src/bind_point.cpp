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

    // Point<->line duality (exact); returns a Line.
    cls.def("dual", [](const Point &p) { return p.dual(); },
            "Dual line of the point: the point (a, b) maps to the line y = a x - b.");
    cls.def("polar", [](const Point &p) { return p.polar(); },
            "Polar line of the point: the point (a, b) maps to the line a x + b y = 1.");

    bind_value_semantics<Point>(cls);

    PGL_BIND_ALL_PREDICATES(cls, Point);

    // A point intersected with any shape is either that point or empty, so the
    // result is always std::optional<Point> — safe to bind against every shape.
    cls.def("intersection", [](const Point &a, const Point &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Point &a, const Segment &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Point &a, const OrientedSegment &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Point &a, const Line &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Point &a, const OrientedLine &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Point &a, const Ray &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Point &a, const Halfplane &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Point &a, const Triangle &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Point &a, const Rectangle &b) { return a.intersection(b); }, nb::arg("other"));
    cls.def("intersection", [](const Point &a, const Convex &b) { return a.intersection(b); }, nb::arg("other"));

    cls.def("distance", [](const Point &a, const Point &b) { return a.distance(b); },
            nb::arg("other"), "Approximate Euclidean (L2) distance (float).");
    // L1 / L-infinity distances are exact (no square root), unlike L2.
    cls.def("distanceL1", [](const Point &a, const Point &b) { return a.distanceL1(b); },
            nb::arg("other"), "Exact Manhattan (L1) distance.");
    cls.def("distanceLInf", [](const Point &a, const Point &b) { return a.distanceLInf(b); },
            nb::arg("other"), "Exact Chebyshev (L-infinity) distance.");

    // Exact squared distance against every shape (Fraction result).
    PGL_BIND_ALL_SQUARED_DISTANCE(cls, Point);
}
