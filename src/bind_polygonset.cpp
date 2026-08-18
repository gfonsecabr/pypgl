#include "common.h"

using namespace pypgl;

// PolygonSet: a set of PolygonWithHoles components with pairwise disjoint
// interiors (shape/polygonset.hpp), whose point set is simply their union.
//
//     A = A_0 u A_1 u ...
//
// This is the shape that **closes the regularized boolean operations**. A
// difference, a union or a symmetric difference of two regions can come apart
// into several pieces, and an island stranded inside a hole of the answer is a
// piece like any other -- so before this shape existed those operations had to
// answer with a bare list, which could not be fed back in, compared, hashed,
// drawn or measured. Now they all answer with one of these, and the algebra is
// closed (see the boolean-operation section of src/common.h).
//
// Two things set it apart from every other pypgl shape:
//
//   * it is the one shape whose point set **need not be connected**
//     (isConnected() asks), and hence the one whose components can be handed
//     back separately -- componentCount() / component(i) / components();
//   * its components are deliberately **not nested**: a component stranded
//     inside another's hole is stored beside it, not within it, which is what
//     the cell engine emits and what a flat list can say.
//
// Storage mirrors PolygonWithHoles: the components are kept in canonical
// (sorted) order, so equality, ordering and hashing do not depend on the order
// they were supplied in; zero-area components cover nothing that survives and
// are dropped, and duplicates are erased. Structural validity -- every
// component valid, interiors pairwise disjoint, no two components sharing a
// stretch of edge -- is a documented precondition rather than an enforced
// invariant, exactly as for Polygon and PolygonWithHoles; isValid() tests it on
// demand.
//
// Like the other variable-size shapes it is bound **mutable** (addComponent /
// eraseComponent / the in-place operators) and therefore unhashable, following
// Python's mutable-implies-unhashable rule.
//
// Python container sugar (see pypgl/__init__.py): C++ iterates a set's
// *components*, since that is the sequence it is made of. Python instead
// flattens the vertices of every ring of every component, as it already does
// for PolygonWithHoles, so a set reads like every other pypgl shape;
// componentCount() / component(i) / components() reach the components
// themselves.

void bind_polygonset(nb::module_ &m) {
    nb::class_<PolygonSet> cls(m, "PolygonSet");

    // --- construction ---
    cls.def(nb::init<>(), "Create the empty set: no components, covering no point.");
    cls.def(nb::init<PolygonWithHoles>(), nb::arg("component"),
            "Create a set with a single region as its only component.");
    cls.def("__init__",
            [](PolygonSet *self, const std::vector<PolygonWithHoles> &components, bool trusted) {
                new (self) PolygonSet(components, trusted);
            },
            nb::arg("components"), nb::arg("trusted") = false,
            "Create a set from a list of regions. They are stored in canonical (sorted) "
            "order, so the order they are given in does not affect equality, ordering or "
            "hashing; zero-area components are dropped and duplicates erased. Pairwise "
            "disjoint interiors are a precondition, not a check -- call isValid(). Set "
            "trusted to skip the canonical reordering when they are already in it.");

    // --- components ---
    cls.def("componentCount", [](const PolygonSet &a) { return a.componentCount(); },
            "Number of components.");
    cls.def("component", [](const PolygonSet &a, std::size_t i) { return a.component(i); },
            nb::arg("index"), "The i-th component, in canonical order.");
    cls.def("components", [](const PolygonSet &a) { return a.components(); },
            "The components, in canonical order.");
    cls.def("addComponent", [](PolygonSet &a, const PolygonWithHoles &c) { a.addComponent(c); },
            nb::arg("component"),
            "Add a component in place, keeping the canonical order. A zero-area region "
            "covers nothing and is ignored, and a duplicate is not added twice.");
    cls.def("eraseComponent", [](PolygonSet &a, std::size_t i) { a.eraseComponent(i); },
            nb::arg("index"), "Remove component i, by its index in the canonical order.");
    cls.def("eraseComponent", [](PolygonSet &a, const PolygonWithHoles &c) { return a.eraseComponent(c); },
            nb::arg("component"),
            "Remove the given component, returning whether one was found to remove "
            "(O(log k) comparisons, since the components are sorted).");

    // --- holes, vertices and edges, over every ring of every component ---
    cls.def("holeCount", [](const PolygonSet &a) { return a.holeCount(); },
            "Total number of holes over all components.");
    cls.def("hasHoles", [](const PolygonSet &a) { return a.hasHoles(); },
            "Whether any component has a hole.");
    cls.def("vertexCount", [](const PolygonSet &a) { return a.vertexCount(); },
            "Total number of vertices over every ring of every component. Deliberately "
            "not called size() in C++, since it counts something different from a "
            "polygon's; len(shape) is wired to it here.");
    cls.def("vertices", [](const PolygonSet &a) { return a.vertices(); },
            "Every ring's vertices, component by component, each component's outer "
            "boundary first.");
    cls.def("edges", [](const PolygonSet &a) { return a.edges(); },
            "Every ring's boundary edges as segments.");
    cls.def("orientedEdges", [](const PolygonSet &a) { return a.orientedEdges(); },
            "Every ring's boundary edges directed so the set lies to the left: outer "
            "rings counterclockwise, hole rings clockwise.");

    // --- structure ---
    cls.def("empty", [](const PolygonSet &a) { return a.empty(); },
            "Whether the set has no components at all, and hence covers no point.");
    cls.def("isConnected", [](const PolygonSet &a) { return a.isConnected(); },
            "Whether the set is connected as a point set. This is the one pypgl shape "
            "that need not be: two components that never touch are two pieces. The empty "
            "set is connected by convention, having nothing to come apart.");
    cls.def("isPinched", [](const PolygonSet &a) { return a.isPinched(); },
            "Whether two components touch each other anywhere. False is the cheap exact "
            "case: components that stay apart make every relation fold componentwise.");
    cls.def("isDegenerate", [](const PolygonSet &a) { return a.isDegenerate(); },
            "Whether the set has zero area.");
    // isPoint/isSegment without the getIf* pair, exactly as PolygonWithHoles
    // has them: pgl does not define the extracting form for either shape.
    cls.def("isPoint", [](const PolygonSet &a) { return a.isPoint(); },
            "Whether the set covers exactly one point.");
    cls.def("isSegment", [](const PolygonSet &a) { return a.isSegment(); },
            "Whether the set covers exactly one segment of positive length.");
    PGL_BIND_IS_UNDEFINED(cls, PolygonSet);
    cls.def("isSimple", [](const PolygonSet &a) { return a.isSimple(); },
            "Whether every ring of every component is simple. A per-ring check only: it "
            "says nothing about how the rings or the components sit relative to one "
            "another, which is what isValid() adds.");
    cls.def("isValid", [](const PolygonSet &a) { return a.isValid(); },
            "Whether the whole structural contract holds: every component valid, "
            "component interiors pairwise disjoint, and no two components sharing a "
            "stretch of edge (they may meet at finitely many points).");
    cls.def("isRegular", [](const PolygonSet &a) { return a.isRegular(); },
            "Whether the set is the closure of its own interior. A set is regular exactly "
            "when every component is, since no slit can run between two components.");
    cls.def("regularized", [](const PolygonSet &a) { return a.regularized(); },
            "The set without its slits, closure(interior), again as a PolygonSet -- so "
            "unlike PolygonWithHoles.regularized(), the regularization is idempotent in "
            "the type system and not only in the mathematics.");

    // --- measures ---
    cls.def("twiceArea", [](const PolygonSet &a) { return a.twiceArea(); },
            "Exactly twice the area, summed over the components, without division.");
    cls.def("area", [](const PolygonSet &a) { return a.area(); },
            "Exact area (a Fraction): the components have disjoint interiors, so it is "
            "simply their sum.");
    cls.def("centroid", [](const PolygonSet &a) { return a.centroid(); },
            "Exact area-weighted centroid over the components. When the net area is zero "
            "the centroid of the vertex set is returned instead.");
    cls.def("verticesCentroid", [](const PolygonSet &a) { return a.verticesCentroid(); },
            "Exact centroid of the vertex set over every ring of every component.");
    cls.def("pointInside", [](const PolygonSet &a) { return a.pointInside(); },
            "An exact point strictly inside the set. Undefined for a set with no area.");
    cls.def("diameter", [](const PolygonSet &a) { return a.diameter(); },
            "Longest distance between two vertices, as a segment -- over all components, "
            "so the two ends may lie in different ones.");
    cls.def("bbox", [](const PolygonSet &a) { return a.bbox(); },
            "Exact axis-aligned bounding box (a Rectangle) enclosing every component.");

    // --- triangulation and convex decomposition ---
    cls.def("triangulation", [](const PolygonSet &a) { return a.triangulation(); },
            "Constrained Delaunay triangulation of the set. Every ring of every component "
            "becomes constrained edges, and the hole interiors and the gaps between "
            "components are left out of the domain.");
    cls.def("triangulation",
            [](const PolygonSet &a, const std::vector<Segment> &segments) {
                return a.triangulation(segments);
            },
            nb::arg("segments"),
            "Constrained Delaunay triangulation of the set with extra interior "
            "constraint segments, which are assumed to lie in it.");
    cls.def("convexPartition", [](const PolygonSet &a) { return a.convexPartition(); },
            "Cut the set into Convex pieces with pairwise disjoint interiors whose union "
            "is the part of it that has area.");
    cls.def("convexCovering", [](const PolygonSet &a) { return a.convexCovering(); },
            "Cover the set's area with Convex pieces, which may overlap. Irredundant but "
            "not necessarily minimum.");

    // --- boolean operations, Minkowski sum, intersection ---
    // A set is one of the two shapes that can hold a regularized intersection
    // (a PolygonWithHoles is the other), so it gets all four operations. Every
    // one of them answers with another PolygonSet: this is the type the whole
    // family is closed over.
    PGL_BIND_BOOLEANS(cls, PolygonSet);
    PGL_BIND_REGULARIZED_INTERSECTION(cls, PolygonSet);
    PGL_BIND_MINKOWSKI_REGION(cls, PolygonSet);
    PGL_BIND_INTERSECTION_SET(cls, PolygonSet);

    // --- the shared matrices ---
    PGL_BIND_ALL_PREDICATES(cls, PolygonSet);
    PGL_BIND_ALL_SQUARED_DISTANCE(cls, PolygonSet);
    PGL_BIND_ALL_L1LINF_DISTANCE(cls, PolygonSet);
    PGL_BIND_ALL_SAME_POINT_SET(cls, PolygonSet);
    // No Hausdorff family: pgl defines it only for the six bounded convex
    // shapes, and a set of regions is neither convex nor even connected.

    PGL_BIND_TRANSFORMS(cls, PolygonSet);
    // In-place transforms (mutate, return None), as on every other mutable
    // shape. A negative scale factor reflects the components, which can change
    // their relative order, so the result is re-canonicalized.
    cls.def("rotate90", [](PolygonSet &a, int k) { a.rotate90(k); }, nb::arg("k") = 1,
            "Rotate the set in place by 90*k degrees about the origin.");
    cls.def("scaleUpX", [](PolygonSet &a, const Num &k) { a.scaleUpX(k); }, nb::arg("scalar"),
            "Multiply the set's x-coordinates by scalar in place.");
    cls.def("scaleUpY", [](PolygonSet &a, const Num &k) { a.scaleUpY(k); }, nb::arg("scalar"),
            "Multiply the set's y-coordinates by scalar in place.");
    cls.def("scaleDownX", [](PolygonSet &a, const Num &k) { a.scaleDownX(k); }, nb::arg("scalar"),
            "Divide the set's x-coordinates by scalar in place.");
    cls.def("scaleDownY", [](PolygonSet &a, const Num &k) { a.scaleDownY(k); }, nb::arg("scalar"),
            "Divide the set's y-coordinates by scalar in place.");

    bind_value_semantics<PolygonSet>(cls, /*hashable=*/false);

    cls.def("__iadd__", [](PolygonSet &a, const Point &p) { a += p; return &a; },
            nb::rv_policy::none, nb::is_operator());
    cls.def("__isub__", [](PolygonSet &a, const Point &p) { a -= p; return &a; },
            nb::rv_policy::none, nb::is_operator());
    cls.def("__imul__", [](PolygonSet &a, const Num &k) { a *= k; return &a; },
            nb::rv_policy::none, nb::is_operator());
    cls.def("__itruediv__", [](PolygonSet &a, const Num &k) { a /= k; return &a; },
            nb::rv_policy::none, nb::is_operator());
    // Translation by a Point -- the Point special case of the Minkowski sum,
    // whose named method PGL_BIND_MINKOWSKI_REGION binds.
    cls.def("__add__", [](const PolygonSet &a, const Point &p) { return a + p; },
            nb::is_operator());
    cls.def("__radd__", [](const PolygonSet &a, const Point &p) { return p + a; },
            nb::is_operator());
    cls.def("__sub__", [](const PolygonSet &a, const Point &p) { return a - p; },
            nb::is_operator());
    cls.def("__mul__", [](const PolygonSet &a, const Num &k) { return a * k; },
            nb::is_operator());
    cls.def("__rmul__", [](const PolygonSet &a, const Num &k) { return k * a; },
            nb::is_operator());
    cls.def("__truediv__", [](const PolygonSet &a, const Num &k) { return a / k; },
            nb::is_operator());
}
