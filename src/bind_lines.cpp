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

        bind_value_semantics<Line>(cls);
        PGL_BIND_OPERATORS(cls, Line);
        PGL_BIND_TRANSFORMS(cls, Line);
        PGL_BIND_VERTEX_QUERIES(cls, Line);
        PGL_BIND_INDEXING(cls, Line);
        PGL_BIND_LINE_HELPERS(cls, Line);
        cls.def("asHalfplaneIntersection", [](const Line &l) { return l.asHalfplaneIntersection(); },
                "The same line as a (degenerate) HalfplaneIntersection, two opposite constraints.");
        PGL_BIND_IS_UNDEFINED(cls, Line);
        // A line sums with every convex shape, bounded or not: the answer is
        // again an intersection of half-planes (a line, a slab, a half-plane,
        // or the whole plane), so it comes back as a HalfplaneIntersection --
        // except for the Point pair, which is the line translated.
        PGL_BIND_MINKOWSKI_UNBOUNDED(cls, Line);
        PGL_BIND_EROSION_UNBOUNDED(cls, Line);
        PGL_BIND_XY_AT(cls, Line);
        PGL_BIND_HALFPLANES(cls, Line);
        PGL_BIND_COLLINEAR(cls, Line);
        PGL_BIND_PARALLEL(cls, Line);
        PGL_BIND_ALL_PREDICATES(cls, Line);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Line);
        PGL_BIND_ALL_L1LINF_DISTANCE(cls, Line);
        PGL_BIND_ALL_SAME_POINT_SET(cls, Line);

        // Two lines meet in None, a Point or a Line; a bounded shape clips the
        // line to a Point or a Segment, and a chain or a non-convex region to
        // a list of those.
        PGL_BIND_INTERSECTION_LINEAR(cls, Line);
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
        PGL_BIND_IS_UNDEFINED(cls, OrientedLine);
        PGL_BIND_MINKOWSKI_UNBOUNDED(cls, OrientedLine);
        PGL_BIND_EROSION_UNBOUNDED(cls, OrientedLine);
        PGL_BIND_XY_AT(cls, OrientedLine);
        PGL_BIND_HALFPLANES(cls, OrientedLine);
        PGL_BIND_ORIENTED_HELPERS(cls, OrientedLine);
        PGL_BIND_COLLINEAR(cls, OrientedLine);
        PGL_BIND_PARALLEL(cls, OrientedLine);
        PGL_BIND_ALL_PREDICATES(cls, OrientedLine);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, OrientedLine);
        PGL_BIND_ALL_L1LINF_DISTANCE(cls, OrientedLine);
        PGL_BIND_ALL_SAME_POINT_SET(cls, OrientedLine);
        PGL_BIND_INTERSECTION_LINEAR(cls, OrientedLine);
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
        PGL_BIND_IS_UNDEFINED(cls, Ray);
        PGL_BIND_MINKOWSKI_UNBOUNDED(cls, Ray);
        PGL_BIND_EROSION_UNBOUNDED(cls, Ray);
        PGL_BIND_XY_AT(cls, Ray);
        PGL_BIND_HALFPLANES(cls, Ray);
        PGL_BIND_ORIENTED_HELPERS(cls, Ray);
        PGL_BIND_COLLINEAR(cls, Ray);
        PGL_BIND_PARALLEL(cls, Ray);
        PGL_BIND_ALL_PREDICATES(cls, Ray);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Ray);
        PGL_BIND_ALL_L1LINF_DISTANCE(cls, Ray);
        PGL_BIND_ALL_SAME_POINT_SET(cls, Ray);

        // Two rays meet in None, a Point, a Segment or a Ray -- the four ways
        // two half-infinite pieces of a line can overlap.
        PGL_BIND_INTERSECTION_LINEAR(cls, Ray);
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
        cls.def("asHalfplaneIntersection", [](const Halfplane &h) { return h.asHalfplaneIntersection(); },
                "The same half-plane as a one-constraint HalfplaneIntersection.");

        // Intersecting two half-planes gives a HalfplaneIntersection -- exact
        // and division-free, whether the result is a wedge, a strip, a nested
        // half-plane, a line, or the empty set. Against the 0D/1D shapes the
        // result is the usual optional/variant of concrete pieces instead.
        // Intersecting two half-planes gives a HalfplaneIntersection -- exact
        // and division-free, whether the result is a wedge, a strip, a nested
        // half-plane, a line, or the empty set. Against the 0D/1D shapes the
        // result is the usual optional/variant of concrete pieces instead, and
        // against a non-convex region a list of them.
        PGL_BIND_INTERSECTION_AREA(cls, Halfplane);
        cls.def("asOrientedLine", [](const Halfplane &h) { return h.asOrientedLine(); },
                "Boundary line, directed so the half-plane lies to its left.");

        bind_value_semantics<Halfplane>(cls);
        PGL_BIND_INDEXING(cls, Halfplane);
        PGL_BIND_OPERATORS(cls, Halfplane);
        PGL_BIND_TRANSFORMS(cls, Halfplane);
        PGL_BIND_VERTEX_QUERIES(cls, Halfplane);
        // slope/isVertical/isHorizontal/isDegenerate all describe the boundary line.
        PGL_BIND_LINE_HELPERS(cls, Halfplane);
        PGL_BIND_IS_UNDEFINED(cls, Halfplane);
        // The one shape that sums with all seventeen. A half-plane absorbs
        // whatever bounded shape is added to it and comes back a half-plane,
        // just pushed out to where the summand's farthest point reaches; with
        // another unbounded convex shape it gives a HalfplaneIntersection.
        PGL_BIND_MINKOWSKI_CONVEX(cls, Halfplane);
        PGL_BIND_EROSION_CONVEX(cls, Halfplane);
        // The Disk is the seventeenth, and needs the result type spelled out:
        // pgl's default there is `double`, which pypgl does not instantiate.
        // Both directions slide the boundary along its own *unit* normal, and
        // normalizing asks for a square root of the direction vector's length
        // -- so unlike the Disk-with-Disk pair, an exact radius is not enough
        // and pgl refuses the exact type outright, however the disk was built.
        // These stay bound so the refusal names the reason; see bind_disk.cpp
        // for the same pair the other way round.
        cls.def("minkowskiSum",
                [](const Halfplane &h, const Disk &d) { return h.minkowskiSum<Num>(d); },
                nb::arg("other"),
                "The half-plane pushed out by the disk's radius. Always raises for "
                "pypgl's exact coordinates: sliding a boundary by a radius needs its unit "
                "normal, whose length is a square root even when the radius is exact.");
        cls.def("__add__",
                [](const Halfplane &h, const Disk &d) { return h.minkowskiSum<Num>(d); },
                nb::is_operator());
        cls.def("minkowskiErosion",
                [](const Halfplane &h, const Disk &d) { return h.minkowskiErosion<Num>(d); },
                nb::arg("other"),
                "The half-plane pulled in by the disk's radius -- the translations that "
                "keep the whole disk inside it. Raises for the same reason its sum does.");
        PGL_BIND_ALL_PREDICATES(cls, Halfplane);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Halfplane);
        PGL_BIND_ALL_L1LINF_DISTANCE(cls, Halfplane);
        PGL_BIND_ALL_SAME_POINT_SET(cls, Halfplane);
        // The regularized intersection is available exactly when the other
        // operand can hold the answer, which for a half-plane means a region
        // or a set of them. `difference` the other way round (region minus
        // half-plane) lives on the region.
        PGL_BIND_REGULARIZED_INTERSECTION_WITH_SET(cls, Halfplane);
    }
}
