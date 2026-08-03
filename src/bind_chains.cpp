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
//   * Polyline keeps its vertices in *traversal order*, stored verbatim: what
//     vertices()/indexing/iteration give back is exactly what was passed.
//     Direction is still not part of its identity -- equality, ordering and
//     hashing read the vertices through the canonical direction, so a polyline
//     equals its own reverse -- but the storage never moves, which is what lets
//     it be edited in place (set/insert/pushBack) and flipped edge-wise. It may
//     self-intersect; isSimple() checks. Being an arbitrary chain it has no
//     ordered structure to exploit, so it has no vertical queries.
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
    PGL_BIND_DEGENERACY(cls, SelfT);                                                                                  \
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

        // Shrinking it again. Erasing an interior vertex reroutes the chain
        // through a single edge between its neighbours; erasing an extreme one
        // shortens it. The point form is O(log n) (the vertices are sorted) and
        // reports whether it found a vertex to remove; the index form is
        // positional, over the same lexicographic order that indexing uses.
        cls.def("erase", [](MonotoneChain &c, const Point &p) { return c.erase(p); },
                nb::arg("point"),
                "Remove the vertex equal to point, returning whether there was one.");
        cls.def("erase", [](MonotoneChain &c, std::size_t i) { c.erase(i); }, nb::arg("index"),
                "Remove the i-th vertex in lexicographic order; i must be less than size().");

        // A perturbation-robust crossing test, unique to this shape: true when
        // this chain has a point strictly above the other and one strictly
        // below, so every small enough perturbation of both still leaves them
        // intersecting. Unlike crosses(), a touch that does not swap sides never
        // counts, and overlapping x-extents of a single point are rejected
        // outright -- a shared x that is only one chain's own extreme vertex is
        // not robust.
        // A chain's only summable pair is with a Point; anything wider needs
        // asPolyline() (see the Polyline section below).
        PGL_BIND_TRANSLATION_MINKOWSKI(cls, MonotoneChain);

        cls.def("edgesCross",
                [](const MonotoneChain &a, const MonotoneChain &b) { return a.edgesCross(b); },
                nb::arg("other"),
                "Whether the two chains cross robustly: this chain has a point "
                "strictly above the other and one strictly below.");

        cls.def("asPolyline", [](const MonotoneChain &c) { return c.asPolyline(); },
                "The same vertex sequence as a Polyline. A MonotoneChain has no "
                "minkowskiSum of its own, so this is how to ask for one.");

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
                [](Polyline *self, const std::vector<Point> &points) {
                    new (self) Polyline(points);
                },
                nb::arg("points"),
                "Create a polyline through the given vertices, in traversal order. "
                "The sequence is stored verbatim -- iteration and indexing give it "
                "back exactly as passed. Direction is not part of a polyline's "
                "identity, though: equality, ordering and hashing read the vertices "
                "through the canonical direction, so a polyline still equals its own "
                "reverse. Self-intersections are allowed (use isSimple() to check).");

        PGL_BIND_CHAIN_COMMON(cls, Polyline, "polyline");

        cls.def("isSimple", [](const Polyline &p) { return p.isSimple(); },
                "Whether the polyline does not touch or cross itself: no two "
                "non-adjacent edges meet, adjacent edges meet only at their shared "
                "vertex, and no edge has zero length. A closed polyline (first "
                "vertex equal to the last) is therefore not simple.");

        // The 2-opt edge flip: remove one edge and rejoin the two sub-paths it
        // leaves by a different edge over the same vertex set. Removing edge
        // (p_i, p_i+1) from [p_0 .. p_n-1] leaves A = [p_0 .. p_i] and
        // B = [p_i+1 .. p_n-1], so the new edge must connect an endpoint of A to
        // one of B; the three non-trivial reconnections reverse the suffix, the
        // prefix, or both. Re-adding the removed edge is not a flip.
        cls.def("flippable",
                [](const Polyline &p, const Segment &oldEdge, const Segment &newEdge) {
                    return p.flippable(oldEdge, newEdge);
                },
                nb::arg("old_edge"), nb::arg("new_edge"),
                "Whether replacing old_edge (an existing edge) by new_edge yields a "
                "path over the same vertices. Edges are compared as unordered vertex "
                "pairs; in a self-intersecting polyline old_edge may match several "
                "edges, and the first that admits new_edge is used.");
        cls.def("flipped",
                [](const Polyline &p, const Segment &oldEdge, const Segment &newEdge) {
                    return p.flipped(oldEdge, newEdge);
                },
                nb::arg("old_edge"), nb::arg("new_edge"),
                "A copy with old_edge flipped to new_edge. The flip must be possible "
                "-- check flippable() first.");
        cls.def("flip",
                [](Polyline &p, const Segment &oldEdge, const Segment &newEdge) {
                    p.flip(oldEdge, newEdge);
                },
                nb::arg("old_edge"), nb::arg("new_edge"),
                "Flip old_edge to new_edge in place. The flip must be possible -- "
                "check flippable() first.");

        // With the direction invariant gone upstream (the sequence is now stored
        // verbatim rather than canonicalized on every mutation), a polyline can
        // be edited in place. A MonotoneChain has no counterpart to these: it
        // keeps its vertices sorted, so it has no positional insert and its
        // erase is by value or by sorted position.
        cls.def("set", [](Polyline &p, std::size_t i, const Point &v) { p.set(i, v); },
                nb::arg("index"), nb::arg("point"), "Replace the i-th vertex.");
        cls.def("insert", [](Polyline &p, std::size_t i, const Point &v) { p.insert(i, v); },
                nb::arg("index"), nb::arg("point"),
                "Insert a vertex at position i (in [0, size()]), shifting the rest along.");
        cls.def("insert",
                [](Polyline &p, std::size_t i, const std::vector<Point> &points) {
                    p.insert(i, points);
                },
                nb::arg("index"), nb::arg("points"),
                "Insert several vertices at position i, in traversal order.");
        cls.def("pushBack", [](Polyline &p, const Point &v) { p.pushBack(v); }, nb::arg("point"),
                "Append a vertex, extending the polyline by one edge.");
        cls.def("pushBack",
                [](Polyline &p, const std::vector<Point> &points) { p.pushBack(points); },
                nb::arg("points"), "Append several vertices, in traversal order.");

        // A chain has no area of its own, and the sum still needs a region:
        // dragging a shape along a chain that comes back on itself closes the
        // swept material over a hole, a closed chain being the plainest example.
        // A MonotoneChain has no minkowskiSum -- convert with asPolyline() when
        // its sum is wanted, which is what pgl asks for too.
        PGL_BIND_REGION_MINKOWSKI(cls, Polyline);
    }
}
