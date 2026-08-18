#include <nanobind/make_iterator.h>

#include "common.h"

using namespace pypgl;

// IntervalTree: a *mutable* one-dimensional index over bounded shapes
// (algorithm/intervaltree.hpp), holding, for each stored shape, the closed
// interval its bounding box projects to on one axis. The shapes themselves are
// kept, so a query can go back to exact two-dimensional geometry after the
// projection has pruned the candidates.
//
// Where it differs from ShapeTree, which is what to reach for otherwise:
//
//   * it is a red-black tree keyed by one coordinate, so insert() and erase()
//     keep it balanced -- unlike ShapeTree, whose insert() does not rebalance
//     and which has a rebuild() to make up for it;
//   * it answers a *projection* family of queries (the four
//     ...Projections... methods below) that decide from the intervals alone,
//     never looking at the shapes. That is a different question, not a faster
//     approximation of the same one: two shapes whose x-ranges overlap may be
//     far apart in the plane;
//   * its unprefixed family prunes by the projection and then applies the exact
//     two-dimensional predicate, so it returns exactly what ShapeTree's method
//     of the same name returns over the same stored shapes.
//
// The axis is a template parameter in C++ (ProjectionAxis::x or ::y). pypgl
// binds both instantiations as two classes rather than taking a runtime flag,
// which is what keeps each tree's storage as tight as C++'s: IntervalTree
// projects on x, IntervalTreeY on y.
//
// Elements are pypgl::AnyShape, exactly as in ShapeTree, so the same caster
// (casters.h) makes ordinary shape objects go in and come out. The
// bounded/unbounded rule is stricter here than in a ShapeTree, though: *every*
// query is projected before anything else happens, so an unbounded shape has no
// interval to offer and raises as a query too, where a ShapeTree accepts one
// (it prunes the query against stored boxes instead).
//
// Not bound, for the same reason as in ShapeTree and Triangulation: the
// visit... early-stop callback overloads. The report... methods already hand
// back the same information as a list, and the empty... ones already
// short-circuit.

namespace {

template <pgl::ProjectionAxis Axis>
void bindIntervalTree(nb::module_ &m, const char *name, const char *axisName) {
    using Tree = pgl::IntervalTree<AnyShape, Axis>;

    nb::class_<Tree> cls(m, name);

    cls.def(nb::init<>(), "Create an empty tree.");
    cls.def("__init__",
            [](Tree *self, const std::vector<AnyShape> &shapes) {
                new (self) Tree();
                for (const auto &s : shapes)
                    self->insert(s);
            },
            nb::arg("shapes"),
            "Build a tree over the given bounded shapes, in any mix. Equal projected "
            "intervals are stored independently.");

    // ---- sizes / storage ----------------------------------------------------
    cls.def("size", [](const Tree &t) { return t.size(); }, "Number of stored shapes.");
    cls.def("empty", [](const Tree &t) { return t.empty(); }, "Whether the tree stores no shapes.");
    cls.def("shapes", [](const Tree &t) { return t.shapes(); },
            "The stored shapes, in their internal order.");
    cls.def("has", [](const Tree &t, const AnyShape &s) { return t.has(s); }, nb::arg("shape"),
            "Whether a shape equal to shape is stored (exact membership, not a "
            "geometric containment -- the same distinction ShapeTree.has() makes).");
    cls.def("__len__", [](const Tree &t) { return t.size(); });
    cls.def("__contains__", [](const Tree &t, const AnyShape &s) { return t.has(s); });
    cls.def("__iter__",
            [](const Tree &t) { return nb::make_iterator(nb::type<Tree>(), "Iterator", t.begin(), t.end()); },
            nb::keep_alive<0, 1>());

    // ---- mutation -----------------------------------------------------------
    cls.def("insert", [](Tree &t, const AnyShape &s) { t.insert(s); }, nb::arg("shape"),
            "Insert a shape, keeping the tree balanced (raises for an unbounded shape, "
            "which has no bounding box to project).");
    cls.def("erase", [](Tree &t, const AnyShape &s) { return t.erase(s); }, nb::arg("shape"),
            "Remove one stored shape equal to shape, keeping the tree balanced; returns "
            "whether one was found.");

    // ---- projection queries: decided from the intervals alone ---------------
    cls.def("countProjectionsIntersecting",
            [](const Tree &t, const AnyShape &q) { return t.countProjectionsIntersecting(q); },
            nb::arg("query"),
            "Number of stored shapes whose projected interval meets the query's; "
            "touching at an endpoint counts.");
    cls.def("reportProjectionsIntersecting",
            [](const Tree &t, const AnyShape &q) { return t.reportProjectionsIntersecting(q); },
            nb::arg("query"), "Those shapes.");
    cls.def("emptyProjectionsIntersecting",
            [](const Tree &t, const AnyShape &q) { return t.emptyProjectionsIntersecting(q); },
            nb::arg("query"), "Whether there is no such shape.");
    cls.def("countProjectionsContainedIn",
            [](const Tree &t, const AnyShape &q) { return t.countProjectionsContainedIn(q); },
            nb::arg("query"),
            "Number of stored shapes whose whole projected interval lies within the "
            "query's, shared endpoints included.");
    cls.def("reportProjectionsContainedIn",
            [](const Tree &t, const AnyShape &q) { return t.reportProjectionsContainedIn(q); },
            nb::arg("query"), "Those shapes.");
    cls.def("emptyProjectionsContainedIn",
            [](const Tree &t, const AnyShape &q) { return t.emptyProjectionsContainedIn(q); },
            nb::arg("query"), "Whether there is no such shape.");

    // ---- exact queries: the projection prunes, the predicate decides --------
    cls.def("countIntersecting", [](const Tree &t, const AnyShape &q) { return t.countIntersecting(q); },
            nb::arg("query"),
            "Number of stored shapes s with s.intersects(query) -- the same answer "
            "ShapeTree gives, reached by pruning on the projection first.");
    cls.def("reportIntersecting", [](const Tree &t, const AnyShape &q) { return t.reportIntersecting(q); },
            nb::arg("query"), "Those shapes.");
    cls.def("emptyIntersecting", [](const Tree &t, const AnyShape &q) { return t.emptyIntersecting(q); },
            nb::arg("query"), "Whether there is no such shape.");
    cls.def("countContainedIn", [](const Tree &t, const AnyShape &q) { return t.countContainedIn(q); },
            nb::arg("query"), "Number of stored shapes s with query.contains(s).");
    cls.def("reportContainedIn", [](const Tree &t, const AnyShape &q) { return t.reportContainedIn(q); },
            nb::arg("query"), "Those shapes.");
    cls.def("emptyContainedIn", [](const Tree &t, const AnyShape &q) { return t.emptyContainedIn(q); },
            nb::arg("query"), "Whether there is no such shape.");

    cls.def("__repr__", [name, axisName](const Tree &t) {
        std::ostringstream out;
        out << name << "(size=" << t.size() << ", axis=" << axisName << ")";
        return out.str();
    });
}

}  // namespace

void bind_intervaltree(nb::module_ &m) {
    bindIntervalTree<pgl::ProjectionAxis::x>(m, "IntervalTree", "x");
    bindIntervalTree<pgl::ProjectionAxis::y>(m, "IntervalTreeY", "y");
}
