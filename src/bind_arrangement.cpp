#include "bind_arrangement.h"

using namespace pypgl;

// Arrangement: the subdivision of the plane induced by segments, rays and lines
// (algorithm/arrangement.hpp), stored as a doubly connected edge list whose
// topology is fixed once it is built.
//
//   * its *vertices* are finite input endpoints, isolated input points,
//     crossings, and the ends of overlaps;
//   * its *edges* are the atomic pieces between them;
//   * its *faces* are the connected components of the complement.
//
// Every finite point of the plane lies in exactly one cell. The face of a
// halfedge is always the one on its **left**, so a bounded face is enclosed by
// a counterclockwise cycle and the outer boundary of a connected piece of the
// input runs clockwise. All unbounded ends meet at one symbolic vertex at
// infinity, ordered by their exact escape direction -- there is no clipping
// frame and no fictitious halfedge, so every halfedge really is part of some
// input shape.
//
// **Exactness is the reason pypgl gets this one for free.** Two segments with
// integer endpoints generally cross at a rational point, so an integer-valued
// arrangement is only adequate for special input (orthogonal segments, say).
// pypgl's single ERational instantiation has no such caveat: every crossing is
// representable and the construction is exact throughout.
//
// **Point labels here, and three more label types elsewhere.** pgl templates the
// class on a label type, and its Voronoi diagram (Triangulation.voronoiDiagram,
// voronoiDiagram(sites), farthestVoronoiDiagram) labels each face with the site
// that generated it -- so this file binds Arrangement<Point, Point>, which makes
// a Voronoi diagram and a plain arrangement the same Python class. For an
// arrangement built from shapes, the labels simply start out as the default
// Point(0, 0); label(cell) reads one and setLabel(cell, value) writes it, which
// is what lets a caller record a classification per cell. The order-k and power
// diagrams label their faces with a list of points, a disk and a list of disks,
// which no Point can hold; those three instantiations are bound from the same
// template (bind_arrangement.h) as classes of their own, in bind_voronoi.cpp and
// bind_powerdiagram.cpp, and they are results only -- nothing constructs them
// from shapes.
//
// **Handles are their own types.** VertexId, HalfedgeId and FaceId are distinct
// classes rather than plain ints, mirroring pgl's strongly typed handles: a
// face handle cannot be passed where a vertex handle is meant, and locateCell()
// can hand back "the cell containing this point" as whichever of the three it
// is, for the caller to tell apart with isinstance(). The same three classes
// serve all four arrangement classes (see bind_arrangement.h).
//
// Not bound: visitIntersecting's callback form (reportIntersecting /
// firstIntersecting / emptyIntersecting give the same information without a
// Python callback, as everywhere else in pypgl), and the raw locate*Linear
// variants, which are the same queries with the index deliberately bypassed.

namespace {

// One handle family. All three are 32-bit indices with a distinct type, plus a
// default "invalid" state that stands in for pgl's would-be NO_FACE sentinels.
template <class Handle>
void bindHandle(nb::module_ &m, const char *name) {
    nb::class_<Handle> cls(m, name);
    cls.def(nb::init<>(), "Create the invalid handle, which refers to no cell.");
    cls.def("__init__",
            [](Handle *self, std::uint32_t index) { new (self) Handle(index); },
            nb::arg("index"), "Create a handle for a given cell index.");
    cls.def("index", [](const Handle &h) { return h.index(); }, "The underlying index.");
    cls.def("valid", [](const Handle &h) { return h.valid(); }, "Whether the handle refers to a cell.");
    cls.def("__bool__", [](const Handle &h) { return h.valid(); });
    cls.def("__eq__", [](const Handle &a, const Handle &b) { return a == b; }, nb::is_operator());
    cls.def("__ne__", [](const Handle &a, const Handle &b) { return !(a == b); }, nb::is_operator());
    cls.def("__lt__", [](const Handle &a, const Handle &b) { return a < b; }, nb::is_operator());
    cls.def("__le__", [](const Handle &a, const Handle &b) { return !(b < a); }, nb::is_operator());
    cls.def("__gt__", [](const Handle &a, const Handle &b) { return b < a; }, nb::is_operator());
    cls.def("__ge__", [](const Handle &a, const Handle &b) { return !(a < b); }, nb::is_operator());
    cls.def("__hash__", [](const Handle &h) { return static_cast<Py_hash_t>(h.index()); });
    cls.def("__repr__", [name](const Handle &h) {
        return h.valid() ? std::string(name) + "(" + std::to_string(h.index()) + ")"
                         : std::string(name) + "()";
    });
}

}  // namespace

void bind_arrangement(nb::module_ &m) {
    bindHandle<PyVertexId>(m, "VertexId");
    bindHandle<PyHalfedgeId>(m, "HalfedgeId");
    bindHandle<PyFaceId>(m, "FaceId");

    // The 1-skeleton of an arrangement is a graph over *handles*, not over
    // points: the symbolic vertex at infinity has no position, so it could not
    // be keyed by one. Same class as Graph in every other respect.
    bindGraph<PyVertexId>(m, "ArrangementGraph");

    auto cls = bindArrangement<Point>(
        m, "Arrangement",
        "The subdivision of the plane induced by points, segments, rays and lines, with "
        "a Point label on every edge and face.",
        "The label of a face. Nothing in the input is a face, so it starts "
        "default-constructed; a Voronoi diagram is the exception, labelling each face "
        "with the site that generated it (the farthest one, for "
        "farthestVoronoiDiagram).",
        "The label of an edge. It starts as the label of the input shape that "
        "produced it -- for a pypgl shape, which carries none, that is the default "
        "Point(0, 0) -- and setLabel() overwrites it.");

    cls.def(nb::init<>(), "Create the empty arrangement: no vertex, no edge, one face.");
    cls.def("__init__",
            [](PyArrangement *self, const std::vector<AnyShape> &shapes) {
                new (self) PyArrangement(shapes);
            },
            nb::arg("shapes"),
            "Build the arrangement of the given shapes, in any mix: points, segments and "
            "oriented segments, polylines and monotone chains, the boundaries of "
            "triangles, rectangles, convexes, polygons and regions, and lines, oriented "
            "lines and rays. The input may cross, overlap collinearly, repeat, share "
            "endpoints or dangle with a free end; overlapping stretches are merged into "
            "one edge that remembers every input shape covering it.");
    cls.def("__init__",
            [](PyArrangement *self, const std::vector<AnyShape> &shapes, const std::vector<Point> &points) {
                new (self) PyArrangement(shapes, points);
            },
            nb::arg("shapes"), nb::arg("points"),
            "Build the arrangement of the given shapes, additionally making every given "
            "point a vertex wherever it falls: a point on a shape splits it there, and a "
            "point on nothing becomes a vertex incident to no edge, in the interior of "
            "the face holding it.");
}
