#include "common.h"

using namespace pypgl;

// MonotoneChain and Polyline: the two open polygonal chains (shape/
// monotonechain.hpp, shape/polyline.hpp). Both mirror Convex/Polygon's storage
// -- a vertex vector plus a lazy translation, so translating is O(1) -- and are
// likewise bound **mutable** (the in-place operators mutate) and therefore
// unhashable, even though pgl specializes std::hash for them.
//
// They differ in what the vertex sequence means, and that difference drives
// every method below:
//
//   * MonotoneChain is weakly x-monotone. Its constructor treats the input as a
//     *point set*: the points are sorted lexicographically (x, then y) and
//     deduplicated, so shuffled input yields the same chain and the chain is
//     always simple. Consecutive vertices may share an x (a vertical edge),
//     hence "weakly"; isStrictlyMonotone() reports whether the chain is the
//     graph of a function. That sorted order is what buys the O(log n) vertical
//     queries -- indexAtX/yAtX/isBelow/isAbove -- which no other shape has, and
//     it is also why the chain can grow: insert() splices a new vertex into the
//     sorted sequence.
//
//   * Polyline keeps its vertices in *traversal order* (only the direction is
//     canonicalized -- the sequence is reversed when the reversal compares
//     lexicographically smaller -- so a polyline equals its own reverse). It may
//     therefore self-intersect; isSimple() checks. Being an arbitrary chain it
//     has no ordered structure to exploit, so no vertical queries and no
//     incremental insert.
//
// Both have n - 1 edges for n vertices (no closing edge, unlike Polygon) and,
// as 1-dimensional manifolds with boundary, their boundary is the two extreme
// vertices and their relative interior is everything else -- matching Segment's
// convention, which is what makes boundaryContains/interiorContains meaningful
// for them.
//
// Both join the shared PGL_BIND_ALL_PREDICATES / PGL_BIND_ALL_SQUARED_DISTANCE
// / PGL_BIND_ALL_L1LINF_DISTANCE macros in src/common.h as full columns, so
// every other shape picked up a MonotoneChain and a Polyline column for free.
// Neither has the Hausdorff family: pgl defines it only for the six convex
// shapes (see PGL_BIND_ALL_HAUSDORFF_DISTANCE), and a chain is not convex.
//
// intersection() is bound against the twelve shapes pgl implements it for --
// every shape except Disk and Polygon (a chain-vs-disk intersection has no
// exact closed form, and a chain-vs-polygon one is simply not written yet).
// The result is always a *list* of Point/Segment pieces: a chain can meet even
// a line in arbitrarily many disjoint places, so there is no single-piece
// optional form like Convex's.

namespace {

// The intersection overloads shared by both chains: every shape except Disk and
// Polygon (see the file comment). Each returns a list of Point/Segment pieces.
#define PGL_BIND_CHAIN_INTERSECTION(cls, SelfT)                                                                     \
    cls.def("intersection", [](const SelfT &a, const Point &b) { return a.intersection(b); }, nb::arg("other"));      \
    cls.def("intersection", [](const SelfT &a, const Segment &b) { return a.intersection(b); }, nb::arg("other"));    \
    cls.def("intersection", [](const SelfT &a, const OrientedSegment &b) { return a.intersection(b); }, nb::arg("other")); \
    cls.def("intersection", [](const SelfT &a, const Line &b) { return a.intersection(b); }, nb::arg("other"));       \
    cls.def("intersection", [](const SelfT &a, const OrientedLine &b) { return a.intersection(b); }, nb::arg("other")); \
    cls.def("intersection", [](const SelfT &a, const Ray &b) { return a.intersection(b); }, nb::arg("other"));        \
    cls.def("intersection", [](const SelfT &a, const Halfplane &b) { return a.intersection(b); }, nb::arg("other"));  \
    cls.def("intersection", [](const SelfT &a, const Rectangle &b) { return a.intersection(b); }, nb::arg("other"));  \
    cls.def("intersection", [](const SelfT &a, const Triangle &b) { return a.intersection(b); }, nb::arg("other"));   \
    cls.def("intersection", [](const SelfT &a, const Convex &b) { return a.intersection(b); }, nb::arg("other"));     \
    cls.def("intersection", [](const SelfT &a, const MonotoneChain &b) { return a.intersection(b); }, nb::arg("other")); \
    cls.def("intersection", [](const SelfT &a, const Polyline &b) { return a.intersection(b); }, nb::arg("other"))

// The vertex/edge accessors, measures, value semantics, operators and
// transforms shared by both chains. Everything here is spelled the same for a
// MonotoneChain and a Polyline; only the docstrings' wording differs, so the
// noun ("chain") is passed in.
#define PGL_BIND_CHAIN_COMMON(cls, SelfT, NOUN)                                                                     \
    cls.def("vertices", [](const SelfT &c) { return c.vertices(); }, "Vertices in chain order.");                     \
    cls.def("edges", [](const SelfT &c) { return c.edges(); },                                                        \
            "The n-1 edges as segments (no closing edge back to the first vertex).");                                 \
    cls.def("orientedEdges", [](const SelfT &c) { return c.orientedEdges(); },                                        \
            "The n-1 edges as oriented segments, each directed from vertex i to vertex i+1.");                        \
    cls.def("bbox", [](const SelfT &c) { return c.bbox(); }, "Exact axis-aligned bounding box (a Rectangle).");        \
    cls.def("diameter", [](const SelfT &c) { return c.diameter(); },                                                  \
            "Longest distance as a segment between two vertices.");                                                   \
    cls.def("isDegenerate", [](const SelfT &c) { return c.isDegenerate(); },                                          \
            "Whether every vertex coincides (the " NOUN " is a single point or empty).");                             \
    cls.def("empty", [](const SelfT &c) { return c.empty(); }, "Whether the " NOUN " has no vertex.");                 \
    cls.def("length", [](const SelfT &c) { return c.length(); },                                                      \
            "Euclidean length: the sum of the edge lengths. Irrational in general, so always a float.");              \
    cls.def("lengthL1", [](const SelfT &c) { return c.lengthL1(); },                                                  \
            "Exact Manhattan (L1) length: the sum of the edges' L1 lengths.");                                        \
    cls.def("lengthLInf", [](const SelfT &c) { return c.lengthLInf(); },                                              \
            "Exact Chebyshev (L-infinity) length: the sum of the edges' LInf lengths.");                              \
    cls.def("pointInside", [](const SelfT &c) { return c.pointInside(); },                                            \
            "An exact point in the " NOUN "'s relative interior (the midpoint of its first edge).");                   \
    cls.def("index", [](const SelfT &c, const Point &p) -> std::optional<std::ptrdiff_t> {                            \
                auto i = c.index(p);                                                                                  \
                if (i < 0) return std::nullopt;                                                                       \
                return i;                                                                                             \
            }, nb::arg("point"), "Index of the vertex equal to point, or None if none.");                             \
    bind_value_semantics<SelfT>(cls, /*hashable=*/false);                                                             \
    cls.def("__iadd__", [](nb::object self, const Point &p) { nb::cast<SelfT &>(self) += p; return self; }, nb::is_operator()); \
    cls.def("__isub__", [](nb::object self, const Point &p) { nb::cast<SelfT &>(self) -= p; return self; }, nb::is_operator()); \
    cls.def("__imul__", [](nb::object self, const Num &k) { nb::cast<SelfT &>(self) *= k; return self; }, nb::is_operator());   \
    cls.def("__itruediv__", [](nb::object self, const Num &k) { nb::cast<SelfT &>(self) /= k; return self; }, nb::is_operator()); \
    cls.def("__add__",  [](const SelfT &c, const Point &p) { SelfT r = c; r += p; return r; }, nb::is_operator());     \
    cls.def("__radd__", [](const SelfT &c, const Point &p) { SelfT r = c; r += p; return r; }, nb::is_operator());     \
    cls.def("__sub__",  [](const SelfT &c, const Point &p) { SelfT r = c; r -= p; return r; }, nb::is_operator());     \
    cls.def("__mul__",  [](const SelfT &c, const Num &k) { SelfT r = c; r *= k; return r; }, nb::is_operator());       \
    cls.def("__rmul__", [](const SelfT &c, const Num &k) { SelfT r = c; r *= k; return r; }, nb::is_operator());       \
    cls.def("__truediv__", [](const SelfT &c, const Num &k) { SelfT r = c; r /= k; return r; }, nb::is_operator());    \
    PGL_BIND_TRANSFORMS(cls, SelfT);                                                                                  \
    cls.def("rotate90", [](SelfT &c, int k) { c.rotate90(k); }, nb::arg("k") = 1,                                     \
            "Rotate the " NOUN " in place by 90*k degrees about the origin.");                                        \
    cls.def("scaleUpX", [](SelfT &c, const Num &k) { c.scaleUpX(k); }, nb::arg("scalar"),                             \
            "Multiply the " NOUN "'s x-coordinates by scalar in place.");                                              \
    cls.def("scaleUpY", [](SelfT &c, const Num &k) { c.scaleUpY(k); }, nb::arg("scalar"),                             \
            "Multiply the " NOUN "'s y-coordinates by scalar in place.");                                              \
    cls.def("scaleDownX", [](SelfT &c, const Num &k) { c.scaleDownX(k); }, nb::arg("scalar"),                         \
            "Divide the " NOUN "'s x-coordinates by scalar in place.");                                                \
    cls.def("scaleDownY", [](SelfT &c, const Num &k) { c.scaleDownY(k); }, nb::arg("scalar"),                         \
            "Divide the " NOUN "'s y-coordinates by scalar in place.");                                                \
    PGL_BIND_INDEXING(cls, SelfT);                                                                                    \
    PGL_BIND_ALL_PREDICATES(cls, SelfT);                                                                              \
    PGL_BIND_ALL_SQUARED_DISTANCE(cls, SelfT);                                                                        \
    PGL_BIND_ALL_L1LINF_DISTANCE(cls, SelfT);                                                                         \
    PGL_BIND_CHAIN_INTERSECTION(cls, SelfT)

}  // namespace

void bind_chains(nb::module_ &m) {
    // --- MonotoneChain ---
    {
        nb::class_<MonotoneChain> cls(m, "MonotoneChain");
        cls.def(nb::init<>(), "Create an empty chain (no vertices).");
        cls.def("__init__",
                [](MonotoneChain *self, const std::vector<Point> &points, bool trusted) {
                    new (self) MonotoneChain(points, trusted);
                },
                nb::arg("points"), nb::arg("trusted") = false,
                "Create the weakly x-monotone chain through a set of points. The "
                "points are treated as a set, not as a pre-linked chain: unless "
                "trusted is set they are sorted lexicographically (by x, ties "
                "broken by y) and deduplicated, so any input order gives the same "
                "chain.");

        PGL_BIND_CHAIN_COMMON(cls, MonotoneChain, "chain");

        cls.def("isStrictlyMonotone", [](const MonotoneChain &c) { return c.isStrictlyMonotone(); },
                "Whether every x-coordinate appears at most once, i.e. the chain "
                "has no vertical edge and so is the graph of a function of x.");

        // Growing the chain: pgl splices the new vertex into the sorted
        // sequence, so a chain (unlike a Polyline) can be built incrementally.
        // The single-point overload is registered first: a Point is iterable in
        // the Python layer, so it would also satisfy the list-of-points overload
        // by conversion.
        cls.def("insert", [](MonotoneChain &c, const Point &p) { c.insert(p); }, nb::arg("point"),
                "Insert a vertex, keeping the chain sorted (a duplicate of an "
                "existing vertex is ignored).");
        cls.def("insert", [](MonotoneChain &c, const std::vector<Point> &points) { c.insert(points); },
                nb::arg("points"), "Insert several vertices at once (a merge, cheaper than repeated insert).");

        // Vertical queries -- the payoff of the sorted storage, and unique to
        // this shape. All are O(log n) and exact; each returns None rather than
        // an index when the query x lies outside the chain's x-extent.
        cls.def("indexAtX",
                [](const MonotoneChain &c, const Num &x) { return c.indexAtX(x); }, nb::arg("x"),
                "The index of the vertex at x, or of the vertex starting the edge "
                "spanning x (the bottom vertex of a vertical edge); None if x is "
                "outside the chain's x-extent.");
        cls.def("yAtX",
                [](const MonotoneChain &c, const Num &x) { return c.yAtX(x); }, nb::arg("x"),
                "The exact y-coordinate of the chain at x, or None if x is outside "
                "its x-extent. At a vertical edge this is the bottom vertex's y; "
                "isStrictlyMonotone() is the precondition for the value to be the "
                "chain's unique y at every x.");
        cls.def("isStrictlyBelow",
                [](const MonotoneChain &c, const Point &p) { return c.isStrictlyBelow(p); }, nb::arg("point"),
                "indexAtX(point.x()) if the whole chain lies strictly below point "
                "there, else None. A point *on* the chain is neither strictly "
                "below nor strictly above it.");
        cls.def("isStrictlyAbove",
                [](const MonotoneChain &c, const Point &p) { return c.isStrictlyAbove(p); }, nb::arg("point"),
                "indexAtX(point.x()) if the whole chain lies strictly above point "
                "there, else None.");
        cls.def("isBelow",
                [](const MonotoneChain &c, const Point &p) { return c.isBelow(p); }, nb::arg("point"),
                "indexAtX(point.x()) if a ray shot straight down from point hits "
                "the chain, else None. Weak: a point on the chain satisfies both "
                "isBelow and isAbove.");
        cls.def("isAbove",
                [](const MonotoneChain &c, const Point &p) { return c.isAbove(p); }, nb::arg("point"),
                "indexAtX(point.x()) if a ray shot straight up from point hits the "
                "chain, else None.");
    }

    // --- Polyline ---
    {
        nb::class_<Polyline> cls(m, "Polyline");
        cls.def(nb::init<>(), "Create an empty polyline (no vertices).");
        cls.def("__init__",
                [](Polyline *self, const std::vector<Point> &points, bool trusted) {
                    new (self) Polyline(points, trusted);
                },
                nb::arg("points"), nb::arg("trusted") = false,
                "Create a polyline through the given vertices, in traversal order. "
                "Unless trusted is set the sequence is canonicalized by direction "
                "only (reversed when the reversal is lexicographically smaller), so "
                "a polyline equals its own reverse; the vertex order is otherwise "
                "kept as given, and self-intersections are allowed (use isSimple() "
                "to check).");

        PGL_BIND_CHAIN_COMMON(cls, Polyline, "polyline");

        cls.def("isSimple", [](const Polyline &p) { return p.isSimple(); },
                "Whether the polyline does not touch or cross itself: no two "
                "non-adjacent edges meet, adjacent edges meet only at their shared "
                "vertex, and no edge has zero length. A closed polyline (first "
                "vertex equal to the last) is therefore not simple.");
    }
}
