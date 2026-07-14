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

    // Unlike the other shapes, a Point's `index` searches its two coordinates:
    // returns 0 if x == value, 1 if y == value, else -1.
    cls.def("index", [](const Point &p, const Num &value) -> std::optional<std::ptrdiff_t> {
                auto i = p.index(value);
                if (i < 0) return std::nullopt;
                return i;
            }, nb::arg("value"), "Index (0 or 1) of the coordinate equal to value, or None if neither.");

    cls.def("swapped", [](const Point &p) { return p.swapped(); },
            "The point with its x and y coordinates swapped.");

    // Point<->line duality (exact); returns a Line.
    cls.def("dual", [](const Point &p) { return p.dual(); },
            "Dual line of the point: the point (a, b) maps to the line y = a x - b.");
    cls.def("polar", [](const Point &p) { return p.polar(); },
            "Polar line of the point: the point (a, b) maps to the line a x + b y = 1.");

    cls.def("bbox", [](const Point &p) { return p.bbox(); },
            "Exact axis-aligned bounding box (a degenerate Rectangle at the point).");

    // Immutable arithmetic: points add/subtract componentwise, negate, and scale
    // by an exact scalar. Each returns a new Point (Point is hashable, so it is
    // never mutated in place).
    cls.def("__add__", [](const Point &a, const Point &b) { return a + b; }, nb::is_operator());
    cls.def("__sub__", [](const Point &a, const Point &b) { return a - b; }, nb::is_operator());
    cls.def("__neg__", [](const Point &a) { return -a; }, nb::is_operator());
    cls.def("__mul__", [](const Point &a, const Num &k) { return a * k; }, nb::is_operator());
    cls.def("__rmul__", [](const Point &a, const Num &k) { return k * a; }, nb::is_operator());
    cls.def("__truediv__", [](const Point &a, const Num &k) { return a / k; }, nb::is_operator());
    PGL_BIND_TRANSFORMS(cls, Point);

    // A Point indexes over its two coordinates (so get(i) yields a coordinate,
    // not a Point). size() is 2.
    PGL_BIND_INDEXING(cls, Point);

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
    cls.def("intersection", [](const Point &a, const Polygon &b) { return a.intersection(b); }, nb::arg("other"));

    cls.def("distance", [](const Point &a, const Point &b) { return a.distance(b); },
            nb::arg("other"), "Approximate Euclidean (L2) distance (float).");
    // L1 / L-infinity distances are exact (no square root), unlike L2.
    cls.def("distanceL1", [](const Point &a, const Point &b) { return a.distanceL1(b); },
            nb::arg("other"), "Exact Manhattan (L1) distance.");
    cls.def("distanceLInf", [](const Point &a, const Point &b) { return a.distanceLInf(b); },
            nb::arg("other"), "Exact Chebyshev (L-infinity) distance.");

    // Exact squared distance against every shape (Fraction result).
    PGL_BIND_ALL_SQUARED_DISTANCE(cls, Point);

    // distanceL1/distanceLInf against every other non-Disk shape (Point's own
    // Point-Point pair above is exact/untemplated; every other pair here goes
    // through the templated ResultNumber overload, still exact).
    PGL_BIND_ALL_L1LINF_DISTANCE(cls, Point);
    // Point<->Disk is the one L1/LInf pair Disk supports at all (see
    // PGL_BIND_ALL_L1LINF_DISTANCE's comment in common.h); it always returns a
    // float, since Disk::distanceL1/distanceLInf are not templated on
    // ResultNumber.
    cls.def("distanceL1", [](const Point &a, const Disk &b) { return a.distanceL1(b); }, nb::arg("other"));
    cls.def("distanceLInf", [](const Point &a, const Disk &b) { return a.distanceLInf(b); }, nb::arg("other"));

    // Hausdorff (squared, L1, L-infinity) distance against the five other
    // shapes pgl implements it for (Segment, OrientedSegment, Rectangle,
    // Triangle, Convex), plus Point's own Point-Point pair.
    PGL_BIND_ALL_HAUSDORFF_DISTANCE(cls, Point);
}
