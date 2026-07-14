#include <nanobind/make_iterator.h>

#include "common.h"

using namespace pypgl;

// ShapeTree: a static spatial index over a mix of shapes (algorithm/shapetree.hpp),
// bound over pypgl::AnyShape = pgl::Shape<Point> (::pypgl::ShapeTree in common.h).
//
// Unlike every other bound type, this is deliberately the one place pypgl
// stores the type-erased pgl::Shape wrapper rather than a concrete class (see
// "Load-bearing design decisions" in CLAUDE.md) -- a spatial index that can
// hold, say, a Triangle and a Disk side by side needs a type-erased element,
// and the casters.h caster for pgl::Shape<EPoint> is what makes that
// transparent from Python: every method below takes/returns ordinary pypgl
// shape objects, never a "Shape" object.
//
// Only bounded shapes (those with bbox(): Point, Segment, OrientedSegment,
// Triangle, Rectangle, Convex, MonotoneChain, Polyline, Polygon, Disk) can
// actually be *stored* --
// pgl's own Shape::bbox() throws std::logic_error for the four unbounded
// alternatives (Line, OrientedLine, Ray, Halfplane), and that exception
// surfaces to Python unmodified (as a RuntimeError), the same way e.g.
// Disk.radius() already lets pgl's own throwing radius<ERational>() surface
// for an irrational radius. Unbounded shapes remain perfectly valid *queries*
// though (e.g. "every stored shape intersecting this Line"), since a query
// never needs its own bbox() -- only pruning against a stored subtree's box.
//
// No weight-function support (see the ShapeTree alias comment in common.h):
// sumIntersecting/sumContainedIn are not bound. visitIntersecting/
// visitContainedIn (the C++ early-stop callback overloads) are not bound
// either, for the same reason bind_triangulation.cpp skips
// visitTriangles/visitEdges -- reportIntersecting/reportContainedIn already
// give the same information as a materialized list, and
// emptyIntersecting/emptyContainedIn already give an efficient short-circuited
// existence check without a Python callback.
//
// nearestNeighbor is guarded on tree.empty() here and returns None rather
// than mirroring pgl's own "reference to a default-constructed ShapeType"
// contract for an empty tree -- AnyShape's default state is EmptyShape, which
// has no corresponding Python object to hand back, so None (pypgl's usual
// stand-in for "no such shape") is the only sensible mapping.

namespace {

// One query overload (self.METHOD(query)) returning T, for a query type
// accepted via the AnyShape caster (i.e. any of the twelve concrete shapes).
template <class T>
void bind_query(nb::class_<ShapeTree> &cls, const char *name,
                T (ShapeTree::*method)(const AnyShape &) const) {
    cls.def(name, [method](const ShapeTree &self, const AnyShape &query) { return (self.*method)(query); },
            nb::arg("query"));
}

}  // namespace

void bind_shapetree(nb::module_ &m) {
    nb::class_<ShapeTree> cls(m, "ShapeTree");

    cls.def(nb::init<>(), "Create an empty tree.");
    cls.def("__init__",
            [](ShapeTree *self, const std::vector<AnyShape> &shapes, std::size_t leafSize) {
                new (self) ShapeTree(shapes, leafSize > 0 ? leafSize : 1);
            },
            nb::arg("shapes"), nb::arg("leaf_size") = 6,
            "Build a tree over shapes (Point/Segment/OrientedSegment/Triangle/"
            "Rectangle/Convex/MonotoneChain/Polyline/Polygon/Disk, in any mix). "
            "leaf_size caps how many elements are kept at a node before it is split.");

    // ---- sizes / storage -----------------------------------------------
    cls.def("size", [](const ShapeTree &t) { return t.size(); }, "Number of stored shapes.");
    cls.def("empty", [](const ShapeTree &t) { return t.empty(); }, "Whether the tree stores no shapes.");
    cls.def("shapes", [](const ShapeTree &t) { return t.shapes(); },
            "The stored shapes, in their internal order.");
    cls.def("__len__", [](const ShapeTree &t) { return t.size(); });
    cls.def("__iter__",
            [](const ShapeTree &t) { return nb::make_iterator(nb::type<ShapeTree>(), "Iterator", t.begin(), t.end()); },
            nb::keep_alive<0, 1>());
    cls.def("__contains__", [](const ShapeTree &t, const AnyShape &shape) { return t.has(shape); },
            nb::arg("shape"), "Whether a shape equal to shape is stored (exact membership).");

    // ---- mutation ---------------------------------------------------------
    cls.def("insert", [](ShapeTree &t, const AnyShape &shape) { t.insert(shape); }, nb::arg("shape"),
            "Insert a shape without rebalancing the existing tree (raises if it "
            "is unbounded -- Line/OrientedLine/Ray/Halfplane have no bbox()).");
    cls.def("rebuild", [](ShapeTree &t, std::size_t leafSize) { t.rebuild(leafSize); }, nb::arg("leaf_size") = 0,
            "Rebuild from the stored shapes, restoring tree quality after many "
            "insert()/erase() calls. Pass 0 to keep the current leaf size.");
    cls.def("erase", [](ShapeTree &t, const AnyShape &shape) { return t.erase(shape); }, nb::arg("shape"),
            "Remove one shape equal to shape; returns whether one was found.");
    // Exact membership, named `has` to mirror pgl (which renamed it from
    // contains() so that a spatial index's "do you store this shape" never
    // reads like a shape's geometric contains(); pypgl's `shape in tree` sugar
    // above is the same query).
    cls.def("has", [](const ShapeTree &t, const AnyShape &shape) { return t.has(shape); },
            nb::arg("shape"), "Whether a shape equal to shape is stored (exact membership).");

    // ---- spatial queries ----------------------------------------------------
    bind_query<std::size_t>(cls, "countIntersecting", &ShapeTree::countIntersecting<AnyShape>);
    bind_query<std::vector<AnyShape>>(cls, "reportIntersecting", &ShapeTree::reportIntersecting<AnyShape>);
    bind_query<bool>(cls, "emptyIntersecting", &ShapeTree::emptyIntersecting<AnyShape>);
    bind_query<std::size_t>(cls, "countContainedIn", &ShapeTree::countContainedIn<AnyShape>);
    bind_query<std::vector<AnyShape>>(cls, "reportContainedIn", &ShapeTree::reportContainedIn<AnyShape>);
    bind_query<bool>(cls, "emptyContainedIn", &ShapeTree::emptyContainedIn<AnyShape>);

    cls.def("nearestNeighbor",
            [](const ShapeTree &t, const AnyShape &query) -> std::optional<AnyShape> {
                if (t.empty())
                    return std::nullopt;
                return t.nearestNeighbor<Num>(query);
            },
            nb::arg("query"),
            "The stored shape nearest to query (exact squared distance), or None "
            "if the tree is empty.");
    cls.def("nearestNeighborL1",
            [](const ShapeTree &t, const AnyShape &query) -> std::optional<AnyShape> {
                if (t.empty())
                    return std::nullopt;
                return t.nearestNeighborL1<Num>(query);
            },
            nb::arg("query"),
            "The stored shape nearest to query under Manhattan (L1) distance, or "
            "None if the tree is empty. Same branch-and-bound traversal as "
            "nearestNeighbor, minimizing a different metric.");
    cls.def("nearestNeighborLInf",
            [](const ShapeTree &t, const AnyShape &query) -> std::optional<AnyShape> {
                if (t.empty())
                    return std::nullopt;
                return t.nearestNeighborLInf<Num>(query);
            },
            nb::arg("query"),
            "The stored shape nearest to query under Chebyshev (L-infinity) "
            "distance, or None if the tree is empty. Same branch-and-bound "
            "traversal as nearestNeighbor, minimizing a different metric.");

    // ---- structure ----------------------------------------------------------
    cls.def("boundingBoxes", [](const ShapeTree &t) { return t.boundingBoxes(); },
            "Every node's subtree bounding box, in pre-order (empty tree -> empty list).");

    cls.def("__repr__", [](const ShapeTree &t) {
        std::ostringstream out;
        out << "ShapeTree(size=" << t.size() << ")";
        return out.str();
    });
}
