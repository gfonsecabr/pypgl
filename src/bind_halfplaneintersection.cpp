#include "common.h"

using namespace pypgl;

// HalfplaneIntersection: the intersection of finitely many closed half-planes
// (shape/halfplaneintersection.hpp). Convex like Convex, but -- unlike it --
// possibly unbounded (a wedge, a strip, a half-plane, or the whole plane) and
// possibly empty. The type is closed under intersection with a Halfplane,
// Rectangle, Triangle, Convex, or another HalfplaneIntersection, and that
// closure is exact: no coordinate divisions are involved.
//
// Two conventions to keep straight:
//
//   * A default-constructed region is the **whole plane** (the intersection of
//     no half-planes) -- the opposite of Convex(), which is the empty set.
//
//   * The stored elements are *half-planes*, not points. The region's actual
//     corners are implicit, and generally not representable in the coordinate
//     type of the half-planes that bound them: integer half-planes routinely
//     bound regions with rational vertices. pypgl's single ERational
//     instantiation is what makes vertex()/vertices() exact here rather than a
//     rounding step. len()/[]/iteration follow C++ and run over the half-planes
//     (see pypgl/__init__.py); the corners are reached through vertexCount() /
//     vertex(i) / vertices(). `point in region` stays point-in-shape, as on
//     every other pypgl shape.
//
// A degenerate region -- one with empty interior, built from touching
// constraints -- is a line, ray, segment, or point, and stays fully supported by
// the predicates. isUndefined() is always False: insert() ignores undefined
// half-planes, so every region is well defined. The isHalfplane/isLine/isRay/
// isPoint/isSegment family names each of those cases, with getIf* returning the
// shape itself; together with empty and isPlane they name every region except
// a full-dimensional one that is not a single half-plane.

void bind_halfplane_intersection(nb::module_ &m) {
    nb::class_<HalfplaneIntersection> cls(m, "HalfplaneIntersection");

    // --- construction ---
    cls.def(nb::init<>(),
            "Create the whole plane -- the intersection of no half-planes. Note this is "
            "the opposite convention from Convex(), which is the empty set.");
    cls.def("__init__",
            [](HalfplaneIntersection *self, const std::vector<Halfplane> &halfplanes) {
                new (self) HalfplaneIntersection(halfplanes);
            },
            nb::arg("halfplanes"),
            "Create the intersection of the given half-planes. They are stored sorted "
            "counterclockwise by boundary direction, with redundant half-planes dropped "
            "and at most one kept per direction.");
    cls.def(nb::init<Halfplane>(), nb::arg("halfplane"),
            "Create the region bounded by a single half-plane.");
    cls.def(nb::init<Rectangle>(), nb::arg("rectangle"),
            "Create the region equal to the given rectangle, as four half-planes.");
    cls.def(nb::init<Triangle>(), nb::arg("triangle"),
            "Create the region equal to the given triangle, as three half-planes.");
    cls.def(nb::init<Convex>(), nb::arg("convex"),
            "Create the region equal to the given convex polygon, one half-plane per edge.");

    // --- the stored half-planes ---
    cls.def("insert", [](HalfplaneIntersection &k, const Halfplane &h) { return k.insert(h); },
            nb::arg("halfplane"),
            "Intersect the region with one more half-plane, in place. Returns False when "
            "the half-plane is discarded -- because it is redundant, or undefined (a "
            "degenerate half-plane bounds no side, so it carries no constraint). When it "
            "empties the region, the region switches to a sticky empty state; otherwise "
            "it is stored and the stored half-planes it makes redundant are removed.");
    cls.def("size", [](const HalfplaneIntersection &k) { return k.size(); },
            "Number of stored half-planes. Note these, not the vertices, are this "
            "shape's indexable elements.");
    cls.def("get", [](const HalfplaneIntersection &k, std::ptrdiff_t i) { return k.get(i); },
            nb::arg("index"),
            "The i-th stored half-plane, with i taken modulo size() (cyclic).");
    cls.def("index",
            [](const HalfplaneIntersection &k, const Halfplane &h) -> std::optional<std::ptrdiff_t> {
                auto i = k.index(h);
                if (i < 0) return std::nullopt;
                return i;
            },
            nb::arg("halfplane"),
            "Index of the stored half-plane equal to the given one, or None if none.");
    cls.def("halfplanes", [](const HalfplaneIntersection &k) { return k.halfplanes(); },
            "The stored half-planes, in boundary order.");

    // --- what kind of region this is ---
    cls.def("empty", [](const HalfplaneIntersection &k) { return k.empty(); },
            "Whether the region is the empty set. (Upstream renamed this from "
            "isEmpty(): every shape with an empty state now spells the test empty().)");
    cls.def("isPlane", [](const HalfplaneIntersection &k) { return k.isPlane(); },
            "Whether the region is the whole plane (no constraint at all).");
    cls.def("isBounded", [](const HalfplaneIntersection &k) { return k.isBounded(); },
            "Whether the region is bounded. O(n) in the number of half-planes.");
    cls.def("isDegenerate", [](const HalfplaneIntersection &k) { return k.isDegenerate(); },
            "Whether the region has empty interior -- a line, ray, segment, or point "
            "built from touching constraints. Such a region is still fully supported by "
            "the predicates.");
    // isUndefined is always False here (insert ignores undefined half-planes),
    // but it is bound for uniformity with every other shape.
    PGL_BIND_IS_UNDEFINED(cls, HalfplaneIntersection);
    cls.def("isHalfplane", [](const HalfplaneIntersection &k) { return k.isHalfplane(); },
            "Whether the region is exactly one closed half-plane. Exact, no division.");
    cls.def("getIfHalfplane", [](const HalfplaneIntersection &k) { return k.getIfHalfplane(); },
            "The single half-plane the region is, or None. Exact, no division.");
    cls.def("isLine", [](const HalfplaneIntersection &k) { return k.isLine(); },
            "Whether the region is exactly one line. Needs no coordinate arithmetic: a "
            "degenerate region is a point, segment, ray, or line, and only the line has "
            "no vertex.");
    cls.def("getIfLine", [](const HalfplaneIntersection &k) { return k.getIfLine(); },
            "The single line the region is, or None. Exact, no division.");
    cls.def("isRay", [](const HalfplaneIntersection &k) { return k.isRay(); },
            "Whether the region is a ray -- the only unbounded degenerate region with a "
            "vertex, so the test needs no coordinate arithmetic.");
    cls.def("getIfRay", [](const HalfplaneIntersection &k) { return k.getIfRay(); },
            "The ray the region is, or None. Divides, but exactly: the source is a Fraction.");
    // isPoint/getIfPoint/isSegment/getIfSegment/isUndefined. The tests run on
    // rational coordinates whatever the region's own type, so a point whose
    // coordinates are not representable in it is still recognized; the getIf*
    // pair divides, which stays exact here since pypgl is all ERational.
    PGL_BIND_DEGENERACY(cls, HalfplaneIntersection);
    // Every sum of two convex shapes is convex, and one with an unbounded
    // operand is again an intersection of half-planes -- so this region sums
    // with all of them and gives back its own type. A non-convex operand is
    // refused: its sum would be an unbounded non-convex region, which no pgl
    // shape represents.
    PGL_BIND_MINKOWSKI_UNBOUNDED(cls, HalfplaneIntersection);
    PGL_BIND_EROSION_UNBOUNDED(cls, HalfplaneIntersection);
    PGL_BIND_CONVEX_HULL(cls, HalfplaneIntersection);

    // --- the implicit corners ---
    cls.def("vertexCount", [](const HalfplaneIntersection &k) { return k.vertexCount(); },
            "Number of implicit vertices. O(n) in the number of half-planes.");
    cls.def("vertex", [](const HalfplaneIntersection &k, std::size_t i) { return k.vertex(i); },
            nb::arg("index"),
            "The i-th implicit vertex, counterclockwise for a bounded region. Exact: the "
            "coordinates are Fractions, which is generally what they have to be.");
    cls.def("vertices", [](const HalfplaneIntersection &k) { return k.vertices(); },
            "The implicit vertices, counterclockwise for a bounded region. Exact.");
    cls.def("edge", [](const HalfplaneIntersection &k, std::size_t i) { return k.edge(i); },
            nb::arg("index"),
            "The boundary contribution of half-plane i: a Segment when both neighbouring "
            "vertices exist, a Ray when only one does, and the whole boundary Line "
            "otherwise. A degenerate region may give a zero-length segment.");

    // --- measures ---
    cls.def("bbox", [](const HalfplaneIntersection &k) { return k.bbox(); },
            "Exact axis-aligned bounding box (a Rectangle). Raises when the region is "
            "empty or unbounded -- neither has one.");
    cls.def("asConvex", [](const HalfplaneIntersection &k) { return k.asConvex(); },
            "The region as a Convex, with exact (Fraction) vertices. Raises when the "
            "region is unbounded.");
    cls.def("twiceArea", [](const HalfplaneIntersection &k) { return k.twiceArea(); },
            "Exactly twice the area, without division. Raises when unbounded.");
    cls.def("area", [](const HalfplaneIntersection &k) { return k.area(); },
            "Exact area (a Fraction). Raises when unbounded.");
    cls.def("centroid", [](const HalfplaneIntersection &k) { return k.centroid(); },
            "Exact centroid. Raises when unbounded.");
    cls.def("pointInside", [](const HalfplaneIntersection &k) { return k.pointInside(); },
            "An exact point strictly inside the region.");

    // --- intersection ---
    // Against a convex shape the result is again a HalfplaneIntersection --
    // the type is closed under these, and exactly so, with no coordinate
    // divisions. Against the 0D/1D shapes it is the usual optional/variant of
    // concrete pieces, and against a non-convex region a list of them. The two
    // chains are the pair pgl does not implement in either direction.
    PGL_BIND_INTERSECTION_HALFPLANES(cls, HalfplaneIntersection);
    // The regularized intersection needs a shape that can hold an answer with
    // a hole on one side, which a convex region never is.
    PGL_BIND_REGULARIZED_INTERSECTION_WITH_SET(cls, HalfplaneIntersection);

    // --- the shared matrices ---
    PGL_BIND_ALL_PREDICATES(cls, HalfplaneIntersection);
    PGL_BIND_ALL_SQUARED_DISTANCE(cls, HalfplaneIntersection);
    PGL_BIND_ALL_L1LINF_DISTANCE(cls, HalfplaneIntersection);
    PGL_BIND_ALL_SAME_POINT_SET(cls, HalfplaneIntersection);
    // No Hausdorff family: the region may be unbounded, so the distance to or
    // from it is generally infinite. pgl defines it only for the six bounded
    // convex shapes.

    PGL_BIND_TRANSFORMS(cls, HalfplaneIntersection);
    // In-place transforms (mutate, return None), as on every other mutable
    // shape. PGL_BIND_TRANSFORMS above binds only the value-returning forms,
    // which every shape has; these are the counterpart the mutable ones add.
    cls.def("rotate90", [](HalfplaneIntersection &a, int k) { a.rotate90(k); }, nb::arg("k") = 1,
            "Rotate the region in place by 90*k degrees about the origin.");
    cls.def("scaleUpX", [](HalfplaneIntersection &a, const Num &k) { a.scaleUpX(k); }, nb::arg("scalar"),
            "Multiply the region's x-coordinates by scalar in place.");
    cls.def("scaleUpY", [](HalfplaneIntersection &a, const Num &k) { a.scaleUpY(k); }, nb::arg("scalar"),
            "Multiply the region's y-coordinates by scalar in place.");
    cls.def("scaleDownX", [](HalfplaneIntersection &a, const Num &k) { a.scaleDownX(k); }, nb::arg("scalar"),
            "Divide the region's x-coordinates by scalar in place.");
    cls.def("scaleDownY", [](HalfplaneIntersection &a, const Num &k) { a.scaleDownY(k); }, nb::arg("scalar"),
            "Divide the region's y-coordinates by scalar in place.");

    // Mutable (insert mutates), hence unhashable, following Convex/Polygon.
    // Equality compares the stored half-planes: geometric for full-dimensional
    // regions, whose non-redundant half-planes are a canonical function of the
    // point set, but merely representational for degenerate ones.
    bind_value_semantics<HalfplaneIntersection>(cls, /*hashable=*/false);

    cls.def("__iadd__", [](HalfplaneIntersection &k, const Point &p) { k += p; return &k; },
            nb::rv_policy::none, nb::is_operator());
    cls.def("__isub__", [](HalfplaneIntersection &k, const Point &p) { k -= p; return &k; },
            nb::rv_policy::none, nb::is_operator());
    cls.def("__add__", [](const HalfplaneIntersection &k, const Point &p) { return k + p; },
            nb::is_operator());
    cls.def("__radd__", [](const HalfplaneIntersection &k, const Point &p) { return p + k; },
            nb::is_operator());
    cls.def("__sub__", [](const HalfplaneIntersection &k, const Point &p) { return k - p; },
            nb::is_operator());
}
