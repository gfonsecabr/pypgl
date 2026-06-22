#include "common.h"

using namespace pypgl;

// Line, OrientedLine, Ray, Halfplane: the infinite / half-infinite 1D primitives
// plus the half-plane. Constructors, accessors, the full predicate matrix, and
// intersection against the other 1D shapes (whose results are points/segments/
// lines/rays — all bound types).

void bind_lines(nb::module_ &m) {
    // --- Line ---
    {
        nb::class_<Line> cls(m, "Line");
        cls.def(nb::init<Point, Point>(), nb::arg("p"), nb::arg("q"),
                "Create an infinite line through two points (stored sorted).");
        cls.def(nb::init<Num, Num, Num, Num>(), nb::arg("x1"), nb::arg("y1"),
                nb::arg("x2"), nb::arg("y2"), "Create a line from four coordinates.");

        cls.def("min", [](const Line &l) { return l.min(); }, "Lexicographically smaller defining point.");
        cls.def("max", [](const Line &l) { return l.max(); }, "Lexicographically larger defining point.");
        cls.def("dual", [](const Line &l) { return l.dual(); }, "Dual point (a, b) of the line y = a x - b.");
        cls.def("polar", [](const Line &l) { return l.polar(); }, "Polar point (a, b) of the line a x + b y = 1.");
        cls.def("halfplaneAbove", [](const Line &l) { return l.halfplaneAbove(); }, "Closed half-plane above the line.");
        cls.def("halfplaneBelow", [](const Line &l) { return l.halfplaneBelow(); }, "Closed half-plane below the line.");

        bind_value_semantics<Line>(cls);
        PGL_BIND_OPERATORS(cls, Line);
        PGL_BIND_TRANSFORMS(cls, Line);
        PGL_BIND_VERTEX_QUERIES(cls, Line);
        PGL_BIND_INDEXING(cls, Line);
        PGL_BIND_LINE_HELPERS(cls, Line);
        PGL_BIND_COLLINEAR(cls, Line);
        PGL_BIND_PARALLEL(cls, Line);
        PGL_BIND_ALL_PREDICATES(cls, Line);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Line);

        cls.def("intersection", [](const Line &a, const Point &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Line &a, const Line &b) { return a.intersection(b); }, nb::arg("other"),
                "Intersection of two lines: None, a Point, or a Line.");
        cls.def("intersection", [](const Line &a, const Segment &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Line &a, const OrientedSegment &b) { return a.intersection(b); }, nb::arg("other"));
    }

    // --- OrientedLine ---
    {
        nb::class_<OrientedLine> cls(m, "OrientedLine");
        cls.def(nb::init<Point, Point>(), nb::arg("source"), nb::arg("target"),
                "Create an oriented infinite line from source toward target.");
        cls.def(nb::init<Num, Num, Num, Num>(), nb::arg("x1"), nb::arg("y1"),
                nb::arg("x2"), nb::arg("y2"), "Create an oriented line from four coordinates.");

        cls.def("source", [](const OrientedLine &l) { return l.source(); }, "Source defining point.");
        cls.def("target", [](const OrientedLine &l) { return l.target(); }, "Target defining point.");
        cls.def("min", [](const OrientedLine &l) { return l.min(); }, "Lexicographically smaller defining point.");
        cls.def("max", [](const OrientedLine &l) { return l.max(); }, "Lexicographically larger defining point.");
        cls.def("opposite", [](const OrientedLine &l) { return l.opposite(); }, "Line with the orientation reversed.");
        cls.def("asLine", [](const OrientedLine &l) { return l.asLine(); }, "Unoriented supporting line.");

        bind_value_semantics<OrientedLine>(cls);
        PGL_BIND_OPERATORS(cls, OrientedLine);
        PGL_BIND_TRANSFORMS(cls, OrientedLine);
        PGL_BIND_VERTEX_QUERIES(cls, OrientedLine);
        PGL_BIND_INDEXING(cls, OrientedLine);
        PGL_BIND_LINE_HELPERS(cls, OrientedLine);
        PGL_BIND_COLLINEAR(cls, OrientedLine);
        PGL_BIND_PARALLEL(cls, OrientedLine);
        PGL_BIND_ALL_PREDICATES(cls, OrientedLine);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, OrientedLine);

        cls.def("intersection", [](const OrientedLine &a, const Point &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const OrientedLine &a, const Line &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const OrientedLine &a, const Segment &b) { return a.intersection(b); }, nb::arg("other"));
    }

    // --- Ray ---
    {
        nb::class_<Ray> cls(m, "Ray");
        cls.def(nb::init<Point, Point>(), nb::arg("source"), nb::arg("target"),
                "Create a ray from source through target (order preserved).");
        cls.def(nb::init<Num, Num, Num, Num>(), nb::arg("x1"), nb::arg("y1"),
                nb::arg("x2"), nb::arg("y2"), "Create a ray from four coordinates.");

        cls.def("source", [](const Ray &r) { return r.source(); }, "Source point of the ray.");
        cls.def("target", [](const Ray &r) { return r.target(); }, "A point on the ray giving its direction.");
        cls.def("min", [](const Ray &r) { return r.min(); }, "Lexicographically smaller defining point.");
        cls.def("max", [](const Ray &r) { return r.max(); }, "Lexicographically larger defining point.");
        cls.def("opposite", [](const Ray &r) { return r.opposite(); }, "Ray with source and target swapped.");
        cls.def("asLine", [](const Ray &r) { return r.asLine(); }, "Unoriented supporting line.");
        cls.def("asOrientedLine", [](const Ray &r) { return r.asOrientedLine(); }, "Oriented supporting line.");

        bind_value_semantics<Ray>(cls);
        PGL_BIND_OPERATORS(cls, Ray);
        PGL_BIND_TRANSFORMS(cls, Ray);
        PGL_BIND_VERTEX_QUERIES(cls, Ray);
        PGL_BIND_INDEXING(cls, Ray);
        PGL_BIND_LINE_HELPERS(cls, Ray);
        PGL_BIND_COLLINEAR(cls, Ray);
        PGL_BIND_PARALLEL(cls, Ray);
        PGL_BIND_ALL_PREDICATES(cls, Ray);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Ray);

        cls.def("intersection", [](const Ray &a, const Point &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Ray &a, const Line &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Ray &a, const OrientedLine &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Ray &a, const Segment &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Ray &a, const OrientedSegment &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Ray &a, const Ray &b) { return a.intersection(b); }, nb::arg("other"),
                "Intersection of two rays: None, a Point, a Segment, or a Ray.");
    }

    // --- Halfplane ---
    {
        nb::class_<Halfplane> cls(m, "Halfplane");
        cls.def(nb::init<Point, Point>(), nb::arg("source"), nb::arg("target"),
                "Create the closed half-plane to the left of the directed boundary source->target.");
        cls.def(nb::init<Num, Num, Num, Num>(), nb::arg("x1"), nb::arg("y1"),
                nb::arg("x2"), nb::arg("y2"), "Create a half-plane from four boundary coordinates.");

        cls.def("source", [](const Halfplane &h) { return h.source(); }, "Source point of the boundary.");
        cls.def("target", [](const Halfplane &h) { return h.target(); }, "Target point of the boundary.");
        cls.def("min", [](const Halfplane &h) { return h.min(); }, "Lexicographically smaller boundary point.");
        cls.def("max", [](const Halfplane &h) { return h.max(); }, "Lexicographically larger boundary point.");
        cls.def("opposite", [](const Halfplane &h) { return h.opposite(); }, "The complementary half-plane.");
        cls.def("asLine", [](const Halfplane &h) { return h.asLine(); }, "Boundary line.");
        cls.def("isDegenerate", [](const Halfplane &h) { return h.isDegenerate(); }, "Whether the boundary points coincide.");

        bind_value_semantics<Halfplane>(cls);
        PGL_BIND_INDEXING(cls, Halfplane);
        PGL_BIND_OPERATORS(cls, Halfplane);
        PGL_BIND_TRANSFORMS(cls, Halfplane);
        PGL_BIND_VERTEX_QUERIES(cls, Halfplane);
        PGL_BIND_ALL_PREDICATES(cls, Halfplane);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Halfplane);
    }
}
