#include "common.h"

using namespace pypgl;

// Triangle, Rectangle, Convex: the bounded 2D primitives. Constructors,
// measures (area / centroid / diameter), vertices/edges, the full predicate
// matrix, and intersection against the 0D/1D shapes (whose clipped results are
// points or segments — all bound types). Intersections that can yield a Convex
// or Polygon region are left for a later milestone.

void bind_polygons(nb::module_ &m) {
    // --- Triangle ---
    {
        nb::class_<Triangle> cls(m, "Triangle");
        cls.def(nb::init<Point, Point, Point>(), nb::arg("a"), nb::arg("b"), nb::arg("c"),
                "Create a triangle from three vertices (normalized: lex-min first, CCW).");
        cls.def(nb::init<Num, Num, Num, Num, Num, Num>(),
                nb::arg("x1"), nb::arg("y1"), nb::arg("x2"), nb::arg("y2"), nb::arg("x3"), nb::arg("y3"),
                "Create a triangle from six coordinates.");

        cls.def("vertices", [](const Triangle &t) { return t.vertices(); }, "The three vertices.");
        cls.def("edges", [](const Triangle &t) { return t.edges(); }, "The three edges as segments.");
        cls.def("area", [](const Triangle &t) { return t.area(); }, "Exact area.");
        cls.def("twiceArea", [](const Triangle &t) { return t.twiceArea(); }, "Exact twice the signed area.");
        cls.def("centroid", [](const Triangle &t) { return t.centroid(); }, "Exact centroid.");
        cls.def("diameter", [](const Triangle &t) { return t.diameter(); }, "Longest distance as a segment between two vertices.");
        cls.def("isDegenerate", [](const Triangle &t) { return t.isDegenerate(); }, "Whether the vertices are collinear.");

        bind_value_semantics<Triangle>(cls);
        PGL_BIND_ALL_PREDICATES(cls, Triangle);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Triangle);

        cls.def("intersection", [](const Triangle &a, const Point &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Triangle &a, const Segment &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Triangle &a, const OrientedSegment &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Triangle &a, const Line &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Triangle &a, const OrientedLine &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Triangle &a, const Ray &b) { return a.intersection(b); }, nb::arg("other"));
    }

    // --- Rectangle ---
    {
        nb::class_<Rectangle> cls(m, "Rectangle");
        cls.def(nb::init<Point, Point>(), nb::arg("first"), nb::arg("second"),
                "Create the axis-aligned bounding rectangle of two points.");
        cls.def(nb::init<Num, Num, Num, Num>(), nb::arg("x1"), nb::arg("y1"), nb::arg("x2"), nb::arg("y2"),
                "Create a rectangle from two opposite corners' coordinates.");

        cls.def("min", [](const Rectangle &r) { return r.min(); }, "Lower-left corner.");
        cls.def("max", [](const Rectangle &r) { return r.max(); }, "Upper-right corner.");
        cls.def("vertices", [](const Rectangle &r) { return r.vertices(); }, "The four corners.");
        cls.def("edges", [](const Rectangle &r) { return r.edges(); }, "The four edges as segments.");
        cls.def("area", [](const Rectangle &r) { return r.area(); }, "Exact area.");
        cls.def("twiceArea", [](const Rectangle &r) { return r.twiceArea(); }, "Exact twice the area.");
        cls.def("centroid", [](const Rectangle &r) { return r.centroid(); }, "Exact centroid.");
        cls.def("midpoint", [](const Rectangle &r) { return r.midpoint(); }, "Exact midpoint of the diagonal.");
        cls.def("diameter", [](const Rectangle &r) { return r.diameter(); }, "Diagonal as a segment.");
        cls.def("isDegenerate", [](const Rectangle &r) { return r.isDegenerate(); }, "Whether the rectangle has zero area.");

        bind_value_semantics<Rectangle>(cls);
        PGL_BIND_ALL_PREDICATES(cls, Rectangle);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Rectangle);

        cls.def("intersection", [](const Rectangle &a, const Point &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Rectangle &a, const Segment &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Rectangle &a, const OrientedSegment &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Rectangle &a, const Line &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Rectangle &a, const OrientedLine &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Rectangle &a, const Ray &b) { return a.intersection(b); }, nb::arg("other"));
    }

    // --- Convex ---
    {
        nb::class_<Convex> cls(m, "Convex");
        cls.def(nb::init<>());
        // The C++ range constructor is a template; bind it via a placement-new
        // factory taking a list of points (Graham-scanned into a convex hull).
        cls.def("__init__",
                [](Convex *self, const std::vector<Point> &points) { new (self) Convex(points); },
                nb::arg("points"),
                "Create the convex hull of the given points.");

        cls.def("vertices", [](const Convex &c) { return c.vertices(); }, "Hull vertices in CCW order from the leftmost.");
        cls.def("edges", [](const Convex &c) { return c.edges(); }, "Hull edges as segments.");
        cls.def("area", [](const Convex &c) { return c.area(); }, "Exact area.");
        cls.def("twiceArea", [](const Convex &c) { return c.twiceArea(); }, "Exact twice the area.");
        cls.def("centroid", [](const Convex &c) { return c.centroid(); }, "Exact centroid.");
        cls.def("diameter", [](const Convex &c) { return c.diameter(); }, "Diameter as a segment between two vertices.");
        cls.def("isDegenerate", [](const Convex &c) { return c.isDegenerate(); }, "Whether the hull is lower-dimensional.");

        bind_value_semantics<Convex>(cls);
        PGL_BIND_ALL_PREDICATES(cls, Convex);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Convex);

        cls.def("intersection", [](const Convex &a, const Point &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Convex &a, const Segment &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Convex &a, const OrientedSegment &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Convex &a, const Line &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Convex &a, const OrientedLine &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Convex &a, const Ray &b) { return a.intersection(b); }, nb::arg("other"));
    }
}
