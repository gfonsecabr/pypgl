#include "common.h"

using namespace pypgl;

// DynamicConvexHull: a *mutable* set of points that keeps its convex hull as
// points are inserted and erased (algorithm/dynamicconvexhull.hpp). Updates
// take O(log^2 n) and most queries O(log n); the hull is listed in O(h log n).
//
// It is a container, not a shape -- like ShapeTree and IntervalTree, and
// unlike Convex -- so it takes their side of the Python sugar: `len` is the
// number of stored points, iteration yields them in lexicographic order, and
// `point in hull` is exact membership (has), not geometric containment, which
// is contains(point). It is not a Shape alternative either (casters.h is
// untouched): it is no ShapeTree element and no other shape's predicate
// operand, since pgl gives it the seven predicates as a *receiver* only.
//
// Two departures from C++, both the standing pypgl conventions:
//   * vertex(i) goes through cyclicIndex, so an empty set raises IndexError
//     (pgl asserts non-emptiness, which would surface as PreconditionError);
//   * index(p) answers None rather than -1, as PGL_BIND_VERTEX_QUERIES does.
//
// __iter__ walks a materialized copy rather than pgl's const_iterator: that
// iterator holds a node index into storage that clear() and erase() recycle, so
// a loop that mutates the set while iterating it (the peeling loop is exactly
// that shape) would read freed nodes. A copy costs O(n) once and cannot.

void bind_dynamicconvexhull(nb::module_ &m) {
    nb::class_<DynamicConvexHull> cls(m, "DynamicConvexHull");

    // The copy constructor goes before the point-list one, so a set handed to
    // the constructor is copied rather than converted through its iteration
    // (the milestone 6 Triangulation/Polygon ordering rule).
    cls.def(nb::init<>(), "Create an empty set.");
    cls.def(nb::init<const DynamicConvexHull &>(), nb::arg("other"), "A copy of another set.");
    cls.def(nb::init<const std::vector<Point> &>(), nb::arg("points"),
            "Store the given points, in O(n log n); repeated points are stored once.");

    // ---- the stored points --------------------------------------------------
    cls.def("size", &DynamicConvexHull::size, "Number of stored points.");
    cls.def("empty", &DynamicConvexHull::empty, "Whether no point is stored.");
    cls.def("has", [](const DynamicConvexHull &h, const Point &p) { return h.has(p); }, nb::arg("point"),
            "Whether a point equal to point is stored, in O(log n) -- exact membership, "
            "not containment in the hull (that is contains).");
    cls.def("insert", [](DynamicConvexHull &h, const Point &p) { return h.insert(p); }, nb::arg("point"),
            "Store a point, in O(log^2 n); returns False if an equal point was already stored.");
    cls.def("erase", [](DynamicConvexHull &h, const Point &p) { return h.erase(p); }, nb::arg("point"),
            "Remove the stored point equal to point, in O(log^2 n); returns whether there was one.");
    cls.def("clear", &DynamicConvexHull::clear, "Remove every point.");
    cls.def("__len__", &DynamicConvexHull::size);
    cls.def("__contains__", [](const DynamicConvexHull &h, const Point &p) { return h.has(p); });
    cls.def("__iter__",
            [](const DynamicConvexHull &h) {
                std::vector<Point> points(h.begin(), h.end());
                return nb::iter(nb::cast(std::move(points)));
            },
            nb::sig("def __iter__(self) -> collections.abc.Iterator[Point]"),
            "The stored points, in lexicographic order.");

    // ---- the hull -----------------------------------------------------------
    cls.def("hullSize", &DynamicConvexHull::hullSize,
            "Number of hull vertices, in O(1). The hull is strictly convex, so a point "
            "inside a hull edge is not a vertex.");
    cls.def("vertex",
            [](const DynamicConvexHull &h, std::ptrdiff_t i) {
                return h.vertex(static_cast<std::ptrdiff_t>(cyclicIndex(i, h.hullSize(), "DynamicConvexHull")));
            },
            nb::arg("index"),
            "The i-th hull vertex counterclockwise from the lexicographically smallest, in "
            "O(log n). Cyclic like Convex.get: i is taken modulo hullSize(), so a negative "
            "index counts from the end. Raises IndexError when the set is empty.");
    cls.def("index",
            [](const DynamicConvexHull &h, const Point &p) -> std::optional<std::ptrdiff_t> {
                auto i = h.index(p);
                if (i < 0) return std::nullopt;
                return i;
            },
            nb::arg("point"), "Index of the hull vertex equal to point, as vertex() numbers them, "
                              "or None if point is not a hull vertex. O(log n).");
    cls.def("verticesContain", [](const DynamicConvexHull &h, const Point &p) { return h.verticesContain(p); },
            nb::arg("point"), "Whether point is a hull vertex, in O(log n).");
    cls.def("extremeVertex", [](const DynamicConvexHull &h, const Point &d) { return h.extremeVertex(d); },
            nb::arg("direction"),
            "The hull vertex maximizing the dot product with direction, the lexicographically "
            "smallest among ties, in O(log n). The set must not be empty and direction must "
            "not be zero.");
    cls.def("bbox", &DynamicConvexHull::bbox,
            "Bounding box of the stored points, in O(log n). The set must not be empty.");
    cls.def("vertices", &DynamicConvexHull::vertices,
            "The hull vertices counterclockwise from the lexicographically smallest, in O(h log n).");
    cls.def("lowerHull", &DynamicConvexHull::lowerHull,
            "The lower hull as a MonotoneChain, from the lexicographically smallest point to the "
            "largest, in O(h log n).");
    cls.def("upperHull", &DynamicConvexHull::upperHull,
            "The upper hull as a MonotoneChain, from the lexicographically smallest point to the "
            "largest, in O(h log n).");
    cls.def("convexHull", &DynamicConvexHull::convexHull, "The hull as a Convex, in O(h log n).");

    // ---- predicates: each answers as the same predicate on convexHull() ------
    // O(log n) against the constant-size shapes, O(k log n) against a Convex
    // (and containment of the polygonal ones), the hull built first otherwise.
    PGL_BIND_ALL_PREDICATES(cls, DynamicConvexHull);

    cls.def("__repr__", [](const DynamicConvexHull &h) {
        std::ostringstream out;
        out << "DynamicConvexHull(size=" << h.size() << ", hullSize=" << h.hullSize() << ")";
        return out.str();
    });
}
