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
        cls.def("bbox", [](const Triangle &t) { return t.bbox(); }, "Exact axis-aligned bounding box (a Rectangle).");

        bind_value_semantics<Triangle>(cls);
        PGL_BIND_OPERATORS(cls, Triangle);
        PGL_BIND_TRANSFORMS(cls, Triangle);
        PGL_BIND_VERTEX_QUERIES(cls, Triangle);
        PGL_BIND_INDEXING(cls, Triangle);
        PGL_BIND_ALL_PREDICATES(cls, Triangle);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Triangle);
        PGL_BIND_ALL_L1LINF_DISTANCE(cls, Triangle);
        PGL_BIND_ALL_HAUSDORFF_DISTANCE(cls, Triangle);

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
        // Bounding box of a list of points (fast path: the range constructor is a
        // template, so bind it through a placement-new factory like Convex's).
        cls.def("__init__",
                [](Rectangle *self, const std::vector<Point> &points) { new (self) Rectangle(points); },
                nb::arg("points"),
                "Create the axis-aligned bounding box of the given points (at least one).");
        // Bounding box enclosing any iterable of bounded shapes (and/or points),
        // even of mixed types — unlike pgl's homogeneous range constructor. Each
        // element's bbox() is unioned; unbounded shapes have no bbox() and so
        // raise, which correctly excludes lines, rays and half-planes.
        cls.def("__init__",
                [](Rectangle *self, nb::iterable shapes) {
                    bool any = false;
                    Num minx, miny, maxx, maxy;
                    for (nb::handle h : shapes) {
                        Rectangle b = nb::cast<Rectangle>(h.attr("bbox")());
                        if (!any) {
                            minx = b.min().x(); miny = b.min().y();
                            maxx = b.max().x(); maxy = b.max().y();
                            any = true;
                        } else {
                            if (b.min().x() < minx) minx = b.min().x();
                            if (b.min().y() < miny) miny = b.min().y();
                            if (maxx < b.max().x()) maxx = b.max().x();
                            if (maxy < b.max().y()) maxy = b.max().y();
                        }
                    }
                    if (!any)
                        throw std::invalid_argument("Rectangle bounding box requires at least one shape");
                    new (self) Rectangle(minx, miny, maxx, maxy);
                },
                nb::arg("shapes"),
                "Create the axis-aligned bounding box enclosing an iterable of bounded "
                "shapes (each must expose bbox(); may mix shape types).");

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
        cls.def("bbox", [](const Rectangle &r) { return r.bbox(); }, "Exact axis-aligned bounding box (the rectangle itself).");

        bind_value_semantics<Rectangle>(cls);
        PGL_BIND_OPERATORS(cls, Rectangle);
        PGL_BIND_TRANSFORMS(cls, Rectangle);
        PGL_BIND_VERTEX_QUERIES(cls, Rectangle);
        PGL_BIND_INDEXING(cls, Rectangle);
        PGL_BIND_ALL_PREDICATES(cls, Rectangle);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Rectangle);
        PGL_BIND_ALL_L1LINF_DISTANCE(cls, Rectangle);
        PGL_BIND_ALL_HAUSDORFF_DISTANCE(cls, Rectangle);

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
        cls.def("bbox", [](const Convex &c) { return c.bbox(); }, "Exact axis-aligned bounding box (a Rectangle).");

        // Convex (and, later, Polygon) is variable-size: pgl stores a lazy
        // translation offset so in-place translation is O(1) regardless of the
        // vertex count. To expose that without the mutable-hashable-key hazard,
        // Convex is mutable and therefore unhashable (Python's list/set rule).
        bind_value_semantics<Convex>(cls, /*hashable=*/false);

        // In-place operators mutate the object (preserving pgl's O(1) translate)
        // and return self, so `c += p` keeps the same object.
        cls.def("__iadd__", [](nb::object self, const Point &p) { nb::cast<Convex &>(self) += p; return self; }, nb::is_operator());
        cls.def("__isub__", [](nb::object self, const Point &p) { nb::cast<Convex &>(self) -= p; return self; }, nb::is_operator());
        cls.def("__imul__", [](nb::object self, const Num &k) { nb::cast<Convex &>(self) *= k; return self; }, nb::is_operator());
        cls.def("__itruediv__", [](nb::object self, const Num &k) { nb::cast<Convex &>(self) /= k; return self; }, nb::is_operator());

        // Value-returning operators copy first (Convex has no free operators, so
        // synthesize them from the compound-assignment members).
        cls.def("__add__",  [](const Convex &c, const Point &p) { Convex r = c; r += p; return r; }, nb::is_operator());
        cls.def("__radd__", [](const Convex &c, const Point &p) { Convex r = c; r += p; return r; }, nb::is_operator());
        cls.def("__sub__",  [](const Convex &c, const Point &p) { Convex r = c; r -= p; return r; }, nb::is_operator());
        cls.def("__mul__",  [](const Convex &c, const Num &k) { Convex r = c; r *= k; return r; }, nb::is_operator());
        cls.def("__rmul__", [](const Convex &c, const Num &k) { Convex r = c; r *= k; return r; }, nb::is_operator());
        cls.def("__truediv__", [](const Convex &c, const Num &k) { Convex r = c; r /= k; return r; }, nb::is_operator());

        // Value-returning transforms (new hull) plus their in-place counterparts
        // (mutate, return None), mirroring pgl.
        PGL_BIND_TRANSFORMS(cls, Convex);
        cls.def("rotate90", [](Convex &c, int k) { c.rotate90(k); }, nb::arg("k") = 1,
                "Rotate the hull in place by 90*k degrees about the origin.");
        cls.def("scaleUpX", [](Convex &c, const Num &k) { c.scaleUpX(k); }, nb::arg("scalar"),
                "Multiply the hull's x-coordinates by scalar in place.");
        cls.def("scaleUpY", [](Convex &c, const Num &k) { c.scaleUpY(k); }, nb::arg("scalar"),
                "Multiply the hull's y-coordinates by scalar in place.");
        cls.def("scaleDownX", [](Convex &c, const Num &k) { c.scaleDownX(k); }, nb::arg("scalar"),
                "Divide the hull's x-coordinates by scalar in place.");
        cls.def("scaleDownY", [](Convex &c, const Num &k) { c.scaleDownY(k); }, nb::arg("scalar"),
                "Divide the hull's y-coordinates by scalar in place.");

        PGL_BIND_VERTEX_QUERIES(cls, Convex);
        PGL_BIND_INDEXING(cls, Convex);
        // Both shared macros now include Disk (see common.h), so these two
        // calls also cover the Convex<->Disk pairing (a float: the gap to a
        // disjoint disk is generally irrational, so there is no exact
        // ResultNumber form to request).
        PGL_BIND_ALL_PREDICATES(cls, Convex);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Convex);
        PGL_BIND_ALL_L1LINF_DISTANCE(cls, Convex);
        PGL_BIND_ALL_HAUSDORFF_DISTANCE(cls, Convex);

        cls.def("intersection", [](const Convex &a, const Point &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Convex &a, const Segment &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Convex &a, const OrientedSegment &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Convex &a, const Line &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Convex &a, const OrientedLine &b) { return a.intersection(b); }, nb::arg("other"));
        cls.def("intersection", [](const Convex &a, const Ray &b) { return a.intersection(b); }, nb::arg("other"));
    }
}
