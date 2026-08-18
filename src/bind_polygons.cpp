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
        cls.def("orientedEdges", [](const Triangle &t) { return t.orientedEdges(); },
                "The three edges as oriented segments, wound counterclockwise.");
        cls.def("edges", [](const Triangle &t) { return t.edges(); }, "The three edges as segments.");
        cls.def("area", [](const Triangle &t) { return t.area(); }, "Exact area.");
        cls.def("twiceArea", [](const Triangle &t) { return t.twiceArea(); }, "Exact twice the signed area.");
        cls.def("a", [](const Triangle &t) { return t.a(); },
                "First vertex (lexicographically smallest); same as t[0].");
        cls.def("b", [](const Triangle &t) { return t.b(); },
                "Second vertex in canonical order; same as t[1].");
        cls.def("c", [](const Triangle &t) { return t.c(); },
                "Third vertex (a, b, c wind counterclockwise); same as t[2].");
        cls.def("centroid", [](const Triangle &t) { return t.centroid(); }, "Exact centroid.");
        cls.def("diameter", [](const Triangle &t) { return t.diameter(); }, "Longest distance as a segment between two vertices.");
        cls.def("isDegenerate", [](const Triangle &t) { return t.isDegenerate(); }, "Whether the vertices are collinear.");
        cls.def("isRectangle", [](const Triangle &t) { return t.isRectangle(); }, "Whether the triangle has a right angle.");
        cls.def("isObtuse", [](const Triangle &t) { return t.isObtuse(); }, "Whether the triangle has an obtuse angle.");
        cls.def("isIsosceles", [](const Triangle &t) { return t.isIsosceles(); }, "Whether two sides have equal length.");
        cls.def("bbox", [](const Triangle &t) { return t.bbox(); }, "Exact axis-aligned bounding box (a Rectangle).");
        cls.def("circumcircle", [](const Triangle &t) { return t.circumcircle(); },
                "The Disk through the three vertices.");
        cls.def("asPolygonWithHoles", [](const Triangle &t) { return t.asPolygonWithHoles(); },
                "The same shape as a hole-free PolygonWithHoles region.");
        cls.def("asHalfplaneIntersection", [](const Triangle &t) { return t.asHalfplaneIntersection(); },
                "The same shape as a HalfplaneIntersection, one half-plane per edge.");
        cls.def("asConvex", [](const Triangle &t) { return t.asConvex(); }, "The same triangle as a Convex.");
        cls.def("asPolygonSet", [](const Triangle &t) { return t.asPolygonSet(); },
                "The same shape as a one-component PolygonSet.");
        cls.def("asPolygon", [](const Triangle &t) { return t.asPolygon(); }, "The same triangle as a Polygon.");

        bind_value_semantics<Triangle>(cls);
        PGL_BIND_OPERATORS(cls, Triangle);
        PGL_BIND_TRANSFORMS(cls, Triangle);
        // The three symmetric booleans over the six bounded region types, plus
        // the difference, whose argument may also be unbounded. Every one of
        // them answers with a PolygonSet, so a triangle takes part in the
        // same closed algebra the regions do -- only the regularized
        // *intersection* needs a region or a set on one side (bound just
        // below), since a triangle cannot hold an answer with a hole.
        PGL_BIND_BOOLEANS(cls, Triangle);
        PGL_BIND_REGULARIZED_INTERSECTION_WITH_SET(cls, Triangle);
        PGL_BIND_MINKOWSKI_CONVEX(cls, Triangle);
        PGL_BIND_DEGENERACY(cls, Triangle);
        PGL_BIND_VERTEX_QUERIES(cls, Triangle);
        PGL_BIND_INDEXING(cls, Triangle);
        PGL_BIND_ALL_PREDICATES(cls, Triangle);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Triangle);
        PGL_BIND_ALL_L1LINF_DISTANCE(cls, Triangle);
        PGL_BIND_ALL_HAUSDORFF_DISTANCE(cls, Triangle);
        PGL_BIND_ALL_SAME_POINT_SET(cls, Triangle);

        // The literal intersection, against every shape but a Disk: a Point or
        // a Segment where the operand is lower-dimensional, a Convex where two
        // convex bodies overlap, and a list of pieces where the operand is a
        // chain or a non-convex region.
        PGL_BIND_INTERSECTION_AREA(cls, Triangle);
    }

    // --- Rectangle ---
    {
        nb::class_<Rectangle> cls(m, "Rectangle");
        cls.def(nb::init<>(),
                "Create the empty rectangle, which covers no point. Growing it with "
                "insert() gives the bounding box of whatever is inserted.");
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
        cls.def("orientedEdges", [](const Rectangle &r) { return r.orientedEdges(); },
                "The four edges as oriented segments, wound counterclockwise.");
        cls.def("edges", [](const Rectangle &r) { return r.edges(); }, "The four edges as segments.");
        cls.def("area", [](const Rectangle &r) { return r.area(); }, "Exact area.");
        cls.def("twiceArea", [](const Rectangle &r) { return r.twiceArea(); }, "Exact twice the area.");
        cls.def("centroid", [](const Rectangle &r) { return r.centroid(); }, "Exact centroid.");
        cls.def("midpoint", [](const Rectangle &r) { return r.midpoint(); }, "Exact midpoint of the diagonal.");
        cls.def("diameter", [](const Rectangle &r) { return r.diameter(); }, "Diagonal as a segment.");
        cls.def("isDegenerate", [](const Rectangle &r) { return r.isDegenerate(); }, "Whether the rectangle has zero area.");
        cls.def("empty", [](const Rectangle &r) { return r.empty(); },
                "Whether the rectangle covers no point at all: its stored maximum corner "
                "falls below its minimum one on an axis, which is the state a "
                "default-constructed Rectangle is in. Distinct from isDegenerate(), which "
                "is a rectangle collapsed to a segment or a point and still covers those.");
        cls.def("bbox", [](const Rectangle &r) { return r.bbox(); }, "Exact axis-aligned bounding box (the rectangle itself).");
        cls.def("circumcircle", [](const Rectangle &r) { return r.circumcircle(); },
                "The Disk through the four corners.");
        cls.def("center", [](const Rectangle &r) { return r.center(); },
                "Exact center point. Equal to centroid() for a rectangle, but named "
                "for the box rather than for the mass distribution.");
        cls.def("width", [](const Rectangle &r) { return r.width(); },
                "Exact width: max().x() - min().x().");
        cls.def("height", [](const Rectangle &r) { return r.height(); },
                "Exact height: max().y() - min().y().");

        // Growing the box in place. Unlike Convex::insert, which needs the other
        // shape's vertices, this needs only its bbox() -- so a Disk is accepted
        // here and only the unbounded shapes are refused. The same registration
        // order applies for the same reason (every shape is iterable over its
        // defining points, so the list overload would otherwise swallow them):
        // refusals, then exact shapes, then point, then list.
        {
            auto refuse = [](const char *what) {
                throw nb::type_error(
                    (std::string("Rectangle.insert: ") + what +
                     " is unbounded and has no bounding box to grow to")
                        .c_str());
            };
            cls.def("insert", [refuse](Rectangle &, const Line &) { refuse("a Line"); },
                    nb::arg("shape"));
            cls.def("insert", [refuse](Rectangle &, const OrientedLine &) { refuse("an OrientedLine"); },
                    nb::arg("shape"));
            cls.def("insert", [refuse](Rectangle &, const Ray &) { refuse("a Ray"); },
                    nb::arg("shape"));
            cls.def("insert", [refuse](Rectangle &, const Halfplane &) { refuse("a Halfplane"); },
                    nb::arg("shape"));
        }
        cls.def("insert", [](Rectangle &r, const Rectangle &o) { r.insert(o); }, nb::arg("shape"),
                "Enlarge the rectangle in place so that it contains the given shape.");
        cls.def("insert", [](Rectangle &r, const Segment &o) { r.insert(o); }, nb::arg("shape"),
                "Enlarge the rectangle in place so that it contains the given shape.");
        cls.def("insert", [](Rectangle &r, const OrientedSegment &o) { r.insert(o); }, nb::arg("shape"),
                "Enlarge the rectangle in place so that it contains the given shape.");
        cls.def("insert", [](Rectangle &r, const Triangle &o) { r.insert(o); }, nb::arg("shape"),
                "Enlarge the rectangle in place so that it contains the given shape.");
        cls.def("insert", [](Rectangle &r, const Convex &o) { r.insert(o); }, nb::arg("shape"),
                "Enlarge the rectangle in place so that it contains the given shape.");
        cls.def("insert", [](Rectangle &r, const Polygon &o) { r.insert(o); }, nb::arg("shape"),
                "Enlarge the rectangle in place so that it contains the given shape.");
        cls.def("insert", [](Rectangle &r, const Disk &o) { r.insert(o); }, nb::arg("shape"),
                "Enlarge the rectangle in place so that it contains the given shape.");
        cls.def("insert", [](Rectangle &r, const Point &p) { r.insert(p); }, nb::arg("point"),
                "Enlarge the rectangle in place so that it contains the given point.");
        cls.def("insert", [](Rectangle &r, const std::vector<Point> &points) {
                    for (const auto &p : points) r.insert(p);
                }, nb::arg("points"),
                "Enlarge the rectangle in place so that it contains every given point.");

        cls.def("asPolygonWithHoles", [](const Rectangle &r) { return r.asPolygonWithHoles(); },
                "The same shape as a hole-free PolygonWithHoles region.");
        cls.def("asHalfplaneIntersection", [](const Rectangle &r) { return r.asHalfplaneIntersection(); },
                "The same shape as a HalfplaneIntersection, one half-plane per edge.");
        cls.def("asConvex", [](const Rectangle &r) { return r.asConvex(); }, "The same rectangle as a Convex.");
        cls.def("asPolygonSet", [](const Rectangle &r) { return r.asPolygonSet(); },
                "The same shape as a one-component PolygonSet.");
        cls.def("asPolygon", [](const Rectangle &r) { return r.asPolygon(); }, "The same rectangle as a Polygon.");

        bind_value_semantics<Rectangle>(cls);
        PGL_BIND_OPERATORS(cls, Rectangle);
        PGL_BIND_TRANSFORMS(cls, Rectangle);
        // The three symmetric booleans over the six bounded region types, plus
        // the difference, whose argument may also be unbounded. Every one of
        // them answers with a PolygonSet, so a rectangle takes part in the
        // same closed algebra the regions do -- only the regularized
        // *intersection* needs a region or a set on one side (bound just
        // below), since a rectangle cannot hold an answer with a hole.
        PGL_BIND_BOOLEANS(cls, Rectangle);
        PGL_BIND_REGULARIZED_INTERSECTION_WITH_SET(cls, Rectangle);
        PGL_BIND_MINKOWSKI_CONVEX(cls, Rectangle);
        PGL_BIND_DEGENERACY(cls, Rectangle);
        PGL_BIND_VERTEX_QUERIES(cls, Rectangle);
        PGL_BIND_INDEXING(cls, Rectangle);
        PGL_BIND_ALL_PREDICATES(cls, Rectangle);
        PGL_BIND_ALL_SQUARED_DISTANCE(cls, Rectangle);
        PGL_BIND_ALL_L1LINF_DISTANCE(cls, Rectangle);
        PGL_BIND_ALL_HAUSDORFF_DISTANCE(cls, Rectangle);
        PGL_BIND_ALL_SAME_POINT_SET(cls, Rectangle);

        // The literal intersection, against every shape but a Disk: a Point or
        // a Segment where the operand is lower-dimensional, a Convex where two
        // convex bodies overlap, and a list of pieces where the operand is a
        // chain or a non-convex region.
        PGL_BIND_INTERSECTION_AREA(cls, Rectangle);
    }

    // --- Convex ---
    {
        nb::class_<Convex> cls(m, "Convex");
        cls.def(nb::init<>());
        // The C++ range constructor is a template; bind it via a placement-new
        // factory taking a list of points (Graham-scanned into a convex hull).
        cls.def("__init__",
                [](Convex *self, const std::vector<Point> &points, bool trusted) {
                    new (self) Convex(points, trusted);
                },
                nb::arg("points"), nb::arg("trusted") = false,
                "Create the convex hull of the given points. Set trusted only if "
                "they already are the hull vertices in counterclockwise order from "
                "the leftmost one, in which case they are stored as given.");
        // The same constructor spelled as a flat coordinate list, mirroring
        // pgl's initializer_list<Number> one: Convex([0,0, 8,0, 4,6]) instead of
        // Convex([Point(0,0), Point(8,0), Point(4,6)]). Registered after the
        // point overload, which is what disambiguates the empty list (both match
        // it; either builds the same empty hull). The two never collide
        // otherwise: a Point has no numerator/denominator so it is not a
        // coordinate, and a number is not a Point.
        cls.def("__init__",
                [](Convex *self, const std::vector<Num> &coords, bool trusted) {
                    new (self) Convex(pointsFromCoords(coords), trusted);
                },
                nb::arg("coords"), nb::arg("trusted") = false,
                "Create the convex hull of the points spelled by a flat coordinate "
                "list, read in (x, y) pairs: Convex([0,0, 8,0, 4,6]).");

        cls.def("vertices", [](const Convex &c) { return c.vertices(); }, "Hull vertices in CCW order from the leftmost.");
        cls.def("orientedEdges", [](const Convex &c) { return c.orientedEdges(); },
                "The hull edges as oriented segments, wound counterclockwise.");
        cls.def("edges", [](const Convex &c) { return c.edges(); }, "Hull edges as segments.");
        cls.def("area", [](const Convex &c) { return c.area(); }, "Exact area.");
        cls.def("twiceArea", [](const Convex &c) { return c.twiceArea(); }, "Exact twice the area.");
        cls.def("centroid", [](const Convex &c) { return c.centroid(); }, "Exact area-weighted centroid.");
        cls.def("verticesCentroid", [](const Convex &c) { return c.verticesCentroid(); },
                "Exact centroid of the vertex set, which for a non-regular polygon "
                "differs from the area-weighted centroid.");
        cls.def("diameter", [](const Convex &c) { return c.diameter(); }, "Diameter as a segment between two vertices.");
        cls.def("isDegenerate", [](const Convex &c) { return c.isDegenerate(); }, "Whether the hull is lower-dimensional.");
        cls.def("empty", [](const Convex &c) { return c.empty(); },
                "Whether the hull covers no point at all -- the empty set, which is what a "
                "vertexless Convex is: the default-constructed one, the hull of no points, "
                "and every convex-valued result that comes back empty.");
        cls.def("bbox", [](const Convex &c) { return c.bbox(); }, "Exact axis-aligned bounding box (a Rectangle).");
        cls.def("asPolygon", [](const Convex &c) { return c.asPolygon(); }, "The same hull as a Polygon.");
        cls.def("asPolygonSet", [](const Convex &c) { return c.asPolygonSet(); },
                "The same hull as a one-component PolygonSet.");
        cls.def("asPolygonWithHoles", [](const Convex &c) { return c.asPolygonWithHoles(); },
                "The same hull as a hole-free PolygonWithHoles region.");
        cls.def("asHalfplaneIntersection", [](const Convex &c) { return c.asHalfplaneIntersection(); },
                "The same hull as a HalfplaneIntersection, one half-plane per edge.");

        // The two monotone chains the hull splits into at its leftmost and
        // rightmost vertices. Together they cover the boundary.
        cls.def("upperHull", [](const Convex &c) { return c.upperHull(); },
                "The upper boundary chain, as a MonotoneChain.");
        cls.def("lowerHull", [](const Convex &c) { return c.lowerHull(); },
                "The lower boundary chain, as a MonotoneChain.");

        // Growing the hull in place.
        //
        // **Registration order is load-bearing here.** Every pypgl shape is
        // iterable over its defining points (pypgl/__init__.py), so *any* shape
        // also satisfies the list-of-points overload by conversion, and
        // nanobind takes the first overload that matches. So:
        //
        //   1. the refusals, for the shapes C++ rejects at compile time --
        //      those with no vertices() to take a hull of. Without these,
        //      `c.insert(disk)` would quietly insert the disk's three
        //      *boundary* points, whose hull the disk bulges straight past, so
        //      the answer would be wrong rather than merely surprising;
        //   2. the shapes that C++ does accept, matched exactly;
        //   3. the single point;
        //   4. the list of points, last, since it is the one that converts.
        auto refuse = [](const char *what) {
            throw nb::type_error(
                (std::string("Convex.insert: ") + what +
                 " has no vertices to take the hull of; insert its points "
                 "explicitly if that is what you meant")
                    .c_str());
        };
        cls.def("insert", [refuse](Convex &, const Disk &) { refuse("a Disk"); },
                nb::arg("shape"));
        cls.def("insert", [refuse](Convex &, const Line &) { refuse("a Line"); },
                nb::arg("shape"));
        cls.def("insert", [refuse](Convex &, const OrientedLine &) { refuse("an OrientedLine"); },
                nb::arg("shape"));
        cls.def("insert", [refuse](Convex &, const Ray &) { refuse("a Ray"); },
                nb::arg("shape"));
        cls.def("insert", [refuse](Convex &, const Halfplane &) { refuse("a Halfplane"); },
                nb::arg("shape"));

        cls.def("insert", [](Convex &c, const Segment &s) { c.insert(s); }, nb::arg("shape"),
                "Enlarge the hull in place so that it contains the given shape.");
        cls.def("insert", [](Convex &c, const OrientedSegment &s) { c.insert(s); }, nb::arg("shape"),
                "Enlarge the hull in place so that it contains the given shape.");
        cls.def("insert", [](Convex &c, const Triangle &t) { c.insert(t); }, nb::arg("shape"),
                "Enlarge the hull in place so that it contains the given shape.");
        cls.def("insert", [](Convex &c, const Rectangle &r) { c.insert(r); }, nb::arg("shape"),
                "Enlarge the hull in place so that it contains the given shape.");
        cls.def("insert", [](Convex &c, const Convex &o) { c.insert(o); }, nb::arg("shape"),
                "Enlarge the hull in place so that it contains the given shape.");
        cls.def("insert", [](Convex &c, const Polygon &o) { c.insert(o); }, nb::arg("shape"),
                "Enlarge the hull in place so that it contains the given shape.");

        cls.def("insert", [](Convex &c, const Point &p) { c.insert(p); }, nb::arg("point"),
                "Enlarge the hull in place so that it contains the given point.");
        cls.def("insert", [](Convex &c, const std::vector<Point> &points) { c.insert(points); },
                nb::arg("points"),
                "Enlarge the hull in place so that it contains every given point.");

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
        // The three symmetric booleans over the six bounded region types, plus
        // the difference, whose argument may also be unbounded. Every one of
        // them answers with a PolygonSet, so a convex takes part in the
        // same closed algebra the regions do -- only the regularized
        // *intersection* needs a region or a set on one side (bound just
        // below), since a convex cannot hold an answer with a hole.
        PGL_BIND_BOOLEANS(cls, Convex);
        PGL_BIND_REGULARIZED_INTERSECTION_WITH_SET(cls, Convex);
        PGL_BIND_MINKOWSKI_CONVEX(cls, Convex);
        PGL_BIND_DEGENERACY(cls, Convex);
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
        PGL_BIND_ALL_SAME_POINT_SET(cls, Convex);

        // The literal intersection, against every shape but a Disk: a Point or
        // a Segment where the operand is lower-dimensional, a Convex where two
        // convex bodies overlap, and a list of pieces where the operand is a
        // chain or a non-convex region.
        PGL_BIND_INTERSECTION_AREA(cls, Convex);
    }
}
