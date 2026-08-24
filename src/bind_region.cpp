#include "common.h"

using namespace pypgl;

// PolygonWithHoles: a closed region, an outer simple polygon minus the
// *interiors* of a set of polygonal holes (shape/polygonwithholes.hpp).
//
//     A = P \ union(H_i degree)
//
// Every hole must lie inside the outer polygon (closed containment, so a hole
// may touch the outer ring but never poke through it) and hole interiors must be
// pairwise disjoint. Like Polygon's simplicity, that contract is a documented
// precondition rather than an enforced invariant -- the constructor does not
// check it, and isValid() tests the whole thing on demand.
//
// This is the shape whose intersections can keep holes, and that is what it
// exists for: removing a shape from the middle of another leaves a hole, and no
// other pgl shape but a PolygonSet (which is made of these) can say so. Every
// regularized boolean operation answers with a PolygonSet of them -- see the
// boolean-operation section of common.h for the grids and for why the answer
// needs a set rather than a single region.
//
// Storage mirrors Convex/Polygon (rings plus a lazy translation, so translating
// is O(1)) and it is likewise bound **mutable** -- addHole/eraseHole and the
// in-place operators mutate -- and therefore unhashable, even though pgl
// specializes std::hash for it.
//
// Python container sugar (see pypgl/__init__.py): unlike C++, where iterating a
// region iterates its *holes*, len()/[]/iteration here run over the region's
// vertices, so a region reads like every other pypgl shape. The holes stay
// reachable through holeCount()/hole(i)/holes(). `point in region` is
// point-in-shape as everywhere else.

void bind_region(nb::module_ &m) {
    nb::class_<PolygonWithHoles> cls(m, "PolygonWithHoles");

    // --- construction ---
    cls.def(nb::init<>(),
            "Create the empty region: no outer boundary at all, and hence no holes.");
    cls.def(nb::init<Polygon>(), nb::arg("outer"),
            "Create a hole-free region from an outer simple polygon.");
    cls.def("__init__",
            [](PolygonWithHoles *self, const Polygon &outer,
               const std::vector<Polygon> &holes, bool trusted) {
                new (self) PolygonWithHoles(outer, holes, trusted);
            },
            nb::arg("outer"), nb::arg("holes"), nb::arg("trusted") = false,
            "Create a region from an outer simple polygon and its holes. The holes are "
            "stored in canonical (sorted) order, so the order they are given in does not "
            "affect equality, ordering or hashing, and a zero-area hole removes nothing "
            "and is dropped. Structural validity -- every ring simple, every hole inside "
            "the outer polygon, hole interiors pairwise disjoint -- is a precondition, "
            "not a check; call isValid() to test it. Set trusted to skip the canonical "
            "reordering when the holes are already in it.");

    // --- rings ---
    cls.def("outer", [](const PolygonWithHoles &a) { return a.outer(); },
            "The outer boundary polygon.");
    cls.def("holeCount", [](const PolygonWithHoles &a) { return a.holeCount(); },
            "Number of holes.");
    cls.def("hasHoles", [](const PolygonWithHoles &a) { return a.hasHoles(); },
            "Whether the region has at least one hole.");
    cls.def("hole", [](const PolygonWithHoles &a, std::size_t i) { return a.hole(i); },
            nb::arg("index"), "The i-th hole, in canonical order.");
    cls.def("holes", [](const PolygonWithHoles &a) { return a.holes(); },
            "The holes, in canonical order.");
    cls.def("addHole", [](PolygonWithHoles &a, const Polygon &h) { a.addHole(h); },
            nb::arg("hole"),
            "Add a hole in place, keeping the canonical order. A zero-area ring removes "
            "nothing and is ignored.");
    cls.def("eraseHole", [](PolygonWithHoles &a, std::size_t i) { a.eraseHole(i); },
            nb::arg("index"), "Fill hole i back in, by its index in the canonical order.");
    cls.def("eraseHole", [](PolygonWithHoles &a, const Polygon &h) { return a.eraseHole(h); },
            nb::arg("hole"),
            "Fill the given hole back in, returning whether one was found to erase "
            "(O(log k) comparisons, since the holes are sorted).");

    // --- vertices and edges, over every ring ---
    cls.def("vertexCount", [](const PolygonWithHoles &a) { return a.vertexCount(); },
            "Total number of vertices over all rings, outer boundary and holes alike. "
            "Deliberately not called size() in C++, since it counts something different "
            "from a polygon's; len(region) is wired to it here.");
    cls.def("vertices", [](const PolygonWithHoles &a) { return a.vertices(); },
            "Every ring's vertices, outer boundary first.");
    cls.def("edges", [](const PolygonWithHoles &a) { return a.edges(); },
            "Every ring's boundary edges as segments, outer boundary first.");
    cls.def("orientedEdges", [](const PolygonWithHoles &a) { return a.orientedEdges(); },
            "Every ring's boundary edges directed so the region lies to the left: the "
            "outer ring counterclockwise as stored, the hole rings reversed (clockwise).");

    // --- structure ---
    cls.def("empty", [](const PolygonWithHoles &a) { return a.empty(); },
            "Whether the region has no outer boundary at all, and hence covers no "
            "point. (Upstream renamed this from isEmpty(): every shape with an empty "
            "state now spells the test empty(), the standard container spelling.)");
    cls.def("isDegenerate", [](const PolygonWithHoles &a) { return a.isDegenerate(); },
            "Whether the region has zero area.");
    // PolygonWithHoles has isPoint/isSegment but no getIfPoint/getIfSegment
    // upstream, so it cannot use PGL_BIND_DEGENERACY. Zero-area holes are
    // dropped at construction, so both are decided by the outer boundary alone.
    cls.def("isPoint", [](const PolygonWithHoles &a) { return a.isPoint(); },
            "Whether the region covers exactly one point.");
    cls.def("isSegment", [](const PolygonWithHoles &a) { return a.isSegment(); },
            "Whether the region covers exactly one segment of positive length.");
    PGL_BIND_IS_UNDEFINED(cls, PolygonWithHoles);
    cls.def("isSimple", [](const PolygonWithHoles &a) { return a.isSimple(); },
            "Whether every ring is simple. A per-ring check only: it says nothing about "
            "how the rings sit relative to one another, which is what isValid() adds.");
    cls.def("isValid", [](const PolygonWithHoles &a) { return a.isValid(); },
            "Whether the whole structural contract holds: every ring simple, every hole "
            "inside the outer polygon, hole interiors pairwise disjoint.");
    cls.def("isRegular", [](const PolygonWithHoles &a) { return a.isRegular(); },
            "Whether the region is the closure of its own interior. Since the contract "
            "constrains interiors only, a valid region may pinch shut along a stretch of "
            "edge -- a *slit*, region material with no area on either side of it, as when "
            "a hole shares an edge with another hole or with the outer boundary. A region "
            "with area is regular exactly when it has no slit. Pinching at an isolated "
            "point is not a slit: the interior still reaches it from every side.");
    cls.def("regularized", [](const PolygonWithHoles &a) { return a.regularized(); },
            "The region without its slits, closure(interior), as a PolygonSet -- the "
            "same regularization every boolean operation applies to its own result. "
            "Dropping the slits can disconnect what they were holding together, which is "
            "why this is a set: a region whose slits are its only connective tissue comes "
            "back as several components, and a region with no area comes back empty. An "
            "already-regular region is returned unchanged, vertex for vertex.");

    // --- measures ---
    cls.def("twiceArea", [](const PolygonWithHoles &a) { return a.twiceArea(); },
            "Exactly twice the area, 2*area(outer) - sum of 2*area(hole), without division.");
    cls.def("area", [](const PolygonWithHoles &a) { return a.area(); },
            "Exact area (a Fraction). Divides twiceArea by 2.");
    cls.def("centroid", [](const PolygonWithHoles &a) { return a.centroid(); },
            "Exact area-weighted centroid, the holes entering with negative weight. When "
            "the net area is zero there is no area-weighted centroid and the centroid of "
            "the vertex set is returned instead.");
    cls.def("verticesCentroid", [](const PolygonWithHoles &a) { return a.verticesCentroid(); },
            "Exact centroid of the vertex set over all rings.");
    cls.def("pointInside", [](const PolygonWithHoles &a) { return a.pointInside(); },
            "An exact point strictly inside the region: inside the outer boundary and "
            "outside every hole. Undefined for a region with no area.");
    cls.def("diameter", [](const PolygonWithHoles &a) { return a.diameter(); },
            "Longest distance between two vertices, as a segment. The holes lie inside "
            "the outer boundary and cannot contribute, so this is the outer polygon's.");
    cls.def("bbox", [](const PolygonWithHoles &a) { return a.bbox(); },
            "Exact axis-aligned bounding box (a Rectangle); the outer polygon's.");

    cls.def("asPolygonSet", [](const PolygonWithHoles &a) { return a.asPolygonSet(); },
            "The same region as a one-component PolygonSet.");


    // --- visibility (implementation/visibilitygraph.hpp) ---
    //
    // All of these triangulate the region once and then run a *triangular
    // expansion* per vertex or query point: a traversal of the mesh carrying a
    // cone of still-unobstructed directions that every crossed diagonal clips,
    // at a cost proportional to the part of the region that vertex actually
    // sees. Sight is stopped by the boundary of the region, holes included.
    cls.def("visibilityGraph", [](const PolygonWithHoles &a) { return a.visibilityGraph(); },
            "The graph on the region's vertices joining two of them when the segment "
            "between them stays inside, even if it touches the boundary along the way.");
    cls.def("clearVisibilityGraph", [](const PolygonWithHoles &a) { return a.clearVisibilityGraph(); },
            "The strict reading of visibilityGraph(): the segment must not meet the "
            "boundary except at its two ends. Always a subgraph of visibilityGraph(); a "
            "degenerate region, having no interior, comes back with no edges at all.");
    cls.def("reducedVisibilityGraph", [](const PolygonWithHoles &a) { return a.reducedVisibilityGraph(); },
            "The subgraph of visibilityGraph() a shortest path can bend along: the edges "
            "tangent to the obstacles at both ends, which is the boundary edges plus the "
            "bitangents between reflex corners. Routing between two arbitrary points "
            "means adding them joined to everything visibleVertices() reports.");
    cls.def("visibleVertices", [](const PolygonWithHoles &a, const Point &q) { return a.visibleVertices(q); },
            nb::arg("query"),
            "The region's vertices visible from the query point, under "
            "visibilityGraph()'s convention. Counterclockwise around the query point, "
            "starting from the lexicographically smallest -- the order sortAround() "
            "gives. This is what joins a query point to reducedVisibilityGraph().");
    cls.def("clearlyVisibleVertices", [](const PolygonWithHoles &a, const Point &q) { return a.clearlyVisibleVertices(q); },
            nb::arg("query"),
            "The strict counterpart of visibleVertices(), under clearVisibilityGraph()'s "
            "convention: always a subset of it, in the same order.");
    cls.def("regularizedVisiblePolygon", [](const PolygonWithHoles &a, const Point &q) { return a.regularizedVisiblePolygon(q); },
            nb::arg("query"),
            "The region visible from the query point, as a Polygon: every point reached "
            "by a segment that stays inside. It is star-shaped about the query point and "
            "hence simply connected, so one Polygon holds it however many holes the "
            "region has. *Regularized* means the closure of the interior, so a sightline "
            "grazing along a wall or slipping through a vertex contributes nothing: what "
            "comes back always bounds area. Its vertices are the region's own plus the "
            "*window* ends where a sightline past a reflex corner lands on a farther "
            "edge -- ray-edge intersections, and exactly the coordinates that need "
            "division, which stays exact here.");

    // --- convex decomposition (shorthands for the triangulation's) ---
    cls.def("convexPartition", [](const PolygonWithHoles &a) { return a.convexPartition(); },
            "Cut the region into Convex pieces with pairwise disjoint interiors whose "
            "union is the part of the region that has area, using at most four times "
            "the fewest pieces possible. The holes are where there is no piece, and a "
            "slit, having no area, appears in none of them.");
    cls.def("convexCovering", [](const PolygonWithHoles &a) { return a.convexCovering(); },
            "Cover the region's area with Convex pieces, which may overlap. "
            "Irredundant but not necessarily minimum; leaves holes and slits "
            "uncovered.");

    // --- triangulation ---
    // Every ring becomes constrained edges and the hole interiors are left out
    // of the domain, so the in-domain triangles cover exactly the part of the
    // region that has area -- a slit, having none, carries no triangle.
    cls.def("triangulation", [](const PolygonWithHoles &a) { return a.triangulation(); },
            "Constrained Delaunay triangulation of the region. The hole interiors are "
            "left out of the domain, so the in-domain triangles cover exactly the part "
            "of the region that has area.");
    cls.def("triangulation",
            [](const PolygonWithHoles &a, const std::vector<Segment> &segments) {
                return a.triangulation(segments);
            },
            nb::arg("segments"),
            "Constrained Delaunay triangulation of the region with extra interior "
            "constraint segments, which are assumed to lie in the region.");

    // --- boolean operations and the Minkowski sum (both defined in common.h) ---
    // A region is one of the two shapes that can hold a regularized
    // intersection (a PolygonSet is the other), so unlike the convex shapes it
    // gets all four operations, not three.
    PGL_BIND_BOOLEANS(cls, PolygonWithHoles);
    PGL_BIND_REGULARIZED_INTERSECTION(cls, PolygonWithHoles);
    PGL_BIND_MINKOWSKI_REGION(cls, PolygonWithHoles);
    PGL_BIND_EROSION_REGION(cls, PolygonWithHoles);
    PGL_BIND_CONVEX_HULL(cls, PolygonWithHoles);
    cls.def("chainCount", [](const PolygonWithHoles &s) { return s.chainCount(); },
            "Number of lexicographically monotone chains the rings break into, outer boundary and holes together -- 2 for a convex ring, more the more the boundary reverses direction in x. It is what the containment and intersection tests cost: they run chain against chain when there are few, and fall back to a plane sweep when there are many.");

    // The literal intersection, which keeps every piece whatever its
    // dimension: a list of Point / Polyline / PolygonWithHoles against a shape
    // with area, of Point / Segment against a lower-dimensional one.
    PGL_BIND_INTERSECTION_AREA(cls, PolygonWithHoles);

    // --- the shared matrices ---
    PGL_BIND_ALL_PREDICATES(cls, PolygonWithHoles);
    PGL_BIND_ALL_SQUARED_DISTANCE(cls, PolygonWithHoles);
    PGL_BIND_ALL_L1LINF_DISTANCE(cls, PolygonWithHoles);
    PGL_BIND_ALL_SAME_POINT_SET(cls, PolygonWithHoles);
    // No Hausdorff family: pgl defines it only for the six bounded convex
    // shapes, and a region is neither convex nor (with holes) simply connected.

    PGL_BIND_TRANSFORMS(cls, PolygonWithHoles);
    // In-place transforms (mutate, return None), as on every other mutable
    // shape. PGL_BIND_TRANSFORMS above binds only the value-returning forms,
    // which every shape has; these are the counterpart the mutable ones add.
    cls.def("rotate90", [](PolygonWithHoles &a, int k) { a.rotate90(k); }, nb::arg("k") = 1,
            "Rotate the region in place by 90*k degrees about the origin.");
    cls.def("scaleUpX", [](PolygonWithHoles &a, const Num &k) { a.scaleUpX(k); }, nb::arg("scalar"),
            "Multiply the region's x-coordinates by scalar in place.");
    cls.def("scaleUpY", [](PolygonWithHoles &a, const Num &k) { a.scaleUpY(k); }, nb::arg("scalar"),
            "Multiply the region's y-coordinates by scalar in place.");
    cls.def("scaleDownX", [](PolygonWithHoles &a, const Num &k) { a.scaleDownX(k); }, nb::arg("scalar"),
            "Divide the region's x-coordinates by scalar in place.");
    cls.def("scaleDownY", [](PolygonWithHoles &a, const Num &k) { a.scaleDownY(k); }, nb::arg("scalar"),
            "Divide the region's y-coordinates by scalar in place.");

    bind_value_semantics<PolygonWithHoles>(cls, /*hashable=*/false);

    // In-place translation/scaling, as on the other mutable shapes. The
    // value-returning `+` by a Point is just below: it is the Point special case
    // of the Minkowski sum, whose named method PGL_BIND_MINKOWSKI_REGION binds.
    cls.def("__iadd__", [](PolygonWithHoles &a, const Point &p) { a += p; return &a; },
            nb::rv_policy::none, nb::is_operator());
    cls.def("__isub__", [](PolygonWithHoles &a, const Point &p) { a -= p; return &a; },
            nb::rv_policy::none, nb::is_operator());
    cls.def("__imul__", [](PolygonWithHoles &a, const Num &k) { a *= k; return &a; },
            nb::rv_policy::none, nb::is_operator());
    cls.def("__itruediv__", [](PolygonWithHoles &a, const Num &k) { a /= k; return &a; },
            nb::rv_policy::none, nb::is_operator());
    // Translation by a Point, the Point special case of the Minkowski sum that
    // PGL_BIND_MINKOWSKI_REGION binds the named method for. Spelled out here
    // rather than in the macro, because every shape's `+ Point` is bound by that
    // shape itself (PGL_BIND_OPERATORS for the immutable ones, their own
    // __add__ for the mutable ones).
    cls.def("__add__", [](const PolygonWithHoles &a, const Point &p) { return a + p; },
            nb::is_operator());
    cls.def("__radd__", [](const PolygonWithHoles &a, const Point &p) { return p + a; },
            nb::is_operator());
    cls.def("__sub__", [](const PolygonWithHoles &a, const Point &p) { return a - p; },
            nb::is_operator());
    cls.def("__mul__", [](const PolygonWithHoles &a, const Num &k) { return a * k; },
            nb::is_operator());
    cls.def("__rmul__", [](const PolygonWithHoles &a, const Num &k) { return k * a; },
            nb::is_operator());
    cls.def("__truediv__", [](const PolygonWithHoles &a, const Num &k) { return a / k; },
            nb::is_operator());
}
