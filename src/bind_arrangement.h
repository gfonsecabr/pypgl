#pragma once

// The Arrangement binding, written once as a template because pgl instantiates
// Arrangement<Point, Label> over four label types that pypgl hands back:
//
//   * Point               -- a plain arrangement, Triangulation.voronoiDiagram,
//                            voronoiDiagram(sites), farthestVoronoiDiagram
//                            (bind_arrangement.cpp, Python "Arrangement");
//   * std::vector<Point>  -- the order-k voronoiDiagram(sites, k)
//                            (bind_voronoi.cpp, "PointListArrangement");
//   * Disk                -- powerDiagram(disks)
//                            (bind_powerdiagram.cpp, "DiskArrangement");
//   * std::vector<Disk>   -- the order-k powerDiagram(disks, k)
//                            (bind_powerdiagram.cpp, "DiskListArrangement").
//
// **One handle family for all four.** pgl nests the VertexId/HalfedgeId/FaceId
// tags inside the class template, so every label type has its own three handle
// types -- distinct C++ types that nanobind would have to bind as distinct
// Python classes, and `isinstance(cell, pgl.FaceId)` would then depend on which
// diagram the cell came from. All of them are the same 32-bit index with the
// same invalid state, though, so the Python side keeps the single family bound
// over Arrangement<Point, Point> and every other instantiation converts by
// index at the boundary (`toPy` / `fromPy` below). For the Point instantiation
// the conversion is the identity.

#include <nanobind/stl/optional.h>
#include <nanobind/stl/variant.h>

#include <sstream>
#include <string>
#include <variant>
#include <vector>

#include "bind_graph.h"

namespace pypgl {

// The handle types Python sees, whatever the label type of the arrangement.
using PyArrangement = pgl::Arrangement<Point, Point>;
using PyVertexId = PyArrangement::VertexId;
using PyHalfedgeId = PyArrangement::HalfedgeId;
using PyFaceId = PyArrangement::FaceId;
using PyCellId = std::variant<PyVertexId, PyHalfedgeId, PyFaceId>;
using PyIntersectionId = std::variant<PyHalfedgeId, PyVertexId>;

namespace arrangement_detail {

template <class To, class Tag>
To rehandle(pgl::detail::Handle<Tag> h) {
    return h.valid() ? To(h.index()) : To();
}

// Conversions between the Python handle family and the one of Arrangement `A`.
template <class A>
struct Handles {
    static PyVertexId toPy(typename A::VertexId v) { return rehandle<PyVertexId>(v); }
    static PyHalfedgeId toPy(typename A::HalfedgeId h) { return rehandle<PyHalfedgeId>(h); }
    static PyFaceId toPy(typename A::FaceId f) { return rehandle<PyFaceId>(f); }

    static typename A::VertexId fromPy(PyVertexId v) { return rehandle<typename A::VertexId>(v); }
    static typename A::HalfedgeId fromPy(PyHalfedgeId h) { return rehandle<typename A::HalfedgeId>(h); }
    static typename A::FaceId fromPy(PyFaceId f) { return rehandle<typename A::FaceId>(f); }

    template <class Handle>
    static auto toPy(const std::vector<Handle> &handles) {
        std::vector<decltype(toPy(std::declval<Handle>()))> result;
        result.reserve(handles.size());
        for (const auto &h : handles)
            result.push_back(toPy(h));
        return result;
    }

    static std::vector<std::vector<PyHalfedgeId>>
    toPy(const std::vector<std::vector<typename A::HalfedgeId>> &cycles) {
        std::vector<std::vector<PyHalfedgeId>> result;
        result.reserve(cycles.size());
        for (const auto &cycle : cycles)
            result.push_back(toPy(cycle));
        return result;
    }

    static PyCellId toPy(const typename A::CellId &cell) {
        return std::visit([](const auto &c) -> PyCellId { return toPy(c); }, cell);
    }

    static PyIntersectionId toPy(const typename A::IntersectionId &cell) {
        return std::visit([](const auto &c) -> PyIntersectionId { return toPy(c); }, cell);
    }
};

// The arrangement carries its label type into the shapes it hands back, so its
// own SegmentType is Segment<Point, Label> rather than the unlabeled Segment
// pypgl binds -- a distinct C++ type, and one no caster knows. These rebuild
// each piece as the bound, label-free shape it geometrically is. (Only the edge
// and halfedge accessors need it: polygonWithHoles() and halfplaneIntersection()
// are declared over plain points already.)
using Edge = std::variant<Segment, Line, Ray>;
using HalfedgeGeometry = std::variant<OrientedSegment, OrientedLine, Ray>;

template <class A>
Edge stripLabel(const typename A::EdgeType &edge) {
    return std::visit(
        [](const auto &e) -> Edge {
            using T = std::decay_t<decltype(e)>;
            if constexpr (std::is_same_v<T, typename A::SegmentType>)
                return Segment(e.min(), e.max());
            else if constexpr (std::is_same_v<T, typename A::LineType>)
                return Line(e.min(), e.max());
            else
                return Ray(e.source(), e.target());
        },
        edge);
}

template <class A>
HalfedgeGeometry stripLabel(const typename A::HalfedgeType &halfedge) {
    return std::visit(
        [](const auto &h) -> HalfedgeGeometry {
            using T = std::decay_t<decltype(h)>;
            if constexpr (std::is_same_v<T, typename A::OrientedSegmentType>)
                return OrientedSegment(h.source(), h.target());
            else if constexpr (std::is_same_v<T, typename A::OrientedLineType>)
                return OrientedLine(h.source(), h.target());
            else
                return Ray(h.source(), h.target());
        },
        halfedge);
}

// One query overload of the curve-tracing family, for each shape pgl's walk
// accepts (a directed curve: it reports the cells in order along it).
#define PGL_ARRANGEMENT_QUERY(cls, A, QueryT)                                                  \
    cls.def("reportIntersecting",                                                              \
            [](const A &a, const QueryT &q) { return H::toPy(a.reportIntersecting(q)); },      \
            nb::arg("curve"));                                                                  \
    cls.def("firstIntersecting",                                                               \
            [](const A &a, const QueryT &q) -> std::optional<PyIntersectionId> {                \
                auto first = a.firstIntersecting(q);                                            \
                if (!first)                                                                     \
                    return std::nullopt;                                                        \
                return H::toPy(*first);                                                         \
            },                                                                                  \
            nb::arg("curve"));                                                                  \
    cls.def("emptyIntersecting",                                                               \
            [](const A &a, const QueryT &q) { return a.emptyIntersecting(q); }, nb::arg("curve"))

}  // namespace arrangement_detail

// Bind pgl::Arrangement<Point, Label> as `name`, without constructors: only the
// Point instantiation is built from shapes (bind_arrangement.cpp adds those);
// the others exist only as the results of the diagram functions.
//
// `faceLabelDoc` / `edgeLabelDoc` describe what label(face) / label(halfedge)
// mean for this instantiation.
template <class Label>
nb::class_<pgl::Arrangement<Point, Label>>
bindArrangement(nb::module_ &m, const char *name, const char *classDoc, const char *faceLabelDoc,
                const char *edgeLabelDoc) {
    using A = pgl::Arrangement<Point, Label>;
    using H = arrangement_detail::Handles<A>;
    using arrangement_detail::Edge;
    using arrangement_detail::stripLabel;

    nb::class_<A> cls(m, name, classDoc);

    // --- cells ---
    cls.def("vertexCount", [](const A &a) { return a.vertexCount(); },
            "Number of finite vertices. The symbolic vertex at infinity is not one of "
            "them; its handle index is exactly this count.");
    cls.def("edgeCount", [](const A &a) { return a.edgeCount(); }, "Number of geometric edges.");
    cls.def("halfedgeCount", [](const A &a) { return a.halfedgeCount(); },
            "Twice edgeCount(): halfedges have consecutive handles and twin pairs are "
            "adjacent.");
    cls.def("faceCount", [](const A &a) { return a.faceCount(); },
            "Number of faces, every unbounded one included. Face 0 is unbounded, though "
            "a line or a pair of rays can create several unbounded faces.");
    cls.def("vertices", [](const A &a) { return a.vertices(); },
            "The positions of the finite vertices, in handle order.");
    cls.def("edges",
            [](const A &a) {
                std::vector<Edge> result;
                for (const auto &edge : a.edges())
                    result.push_back(stripLabel<A>(edge));
                return result;
            },
            "One shape per edge, in edge-index order: a Segment, a Line or a Ray.");
    cls.def("boundedEdges",
            [](const A &a) {
                std::vector<Segment> result;
                for (const auto &edge : a.boundedEdges())
                    result.emplace_back(edge.min(), edge.max());
                return result;
            },
            "Only the edges that are segments.");

    // --- handles to geometry ---
    cls.def("position", [](const A &a, PyVertexId v) { return a[H::fromPy(v)]; }, nb::arg("vertex"),
            "The position of a finite vertex. Raises for the symbolic vertex at "
            "infinity, which has none. (C++ spells this a[v].)");
    cls.def("halfedge", [](const A &a, PyHalfedgeId h) { return stripLabel<A>(a[H::fromPy(h)]); },
            nb::arg("halfedge"),
            "The geometry of a halfedge, directed along it: an OrientedSegment, an "
            "OrientedLine or a Ray. The two halfedges of a segment or line give opposite "
            "orientations; a ray has one finite source, so both of its halfedges give "
            "the same Ray though they stay distinct halfedges. (C++ spells this a[h].)");
    cls.def("witness", [](const A &a, PyVertexId v) { return a.witness(H::fromPy(v)); }, nb::arg("vertex"),
            "The vertex itself; raises for the vertex at infinity.");
    cls.def("witness", [](const A &a, PyHalfedgeId h) { return a.witness(H::fromPy(h)); },
            nb::arg("halfedge"), "A point in the relative interior of the edge.");
    cls.def("witness", [](const A &a, PyFaceId f) { return a.witness(H::fromPy(f)); }, nb::arg("face"),
            "A point strictly inside a bounded face -- a diagonal midpoint or an ear's "
            "interior point when the boundary is one simple ring, and otherwise the more "
            "expensive point obtained by leaving a boundary edge along the inward normal.");

    // --- incidence and topology ---
    cls.def("twin", [](const A &a, PyHalfedgeId h) { return H::toPy(a.twin(H::fromPy(h))); },
            nb::arg("halfedge"), "The other halfedge of the same edge.");
    cls.def("next", [](const A &a, PyHalfedgeId h) { return H::toPy(a.next(H::fromPy(h))); },
            nb::arg("halfedge"),
            "The following halfedge along the boundary of the face on the left; "
            "following it repeatedly traverses one boundary cycle.");
    cls.def("source", [](const A &a, PyHalfedgeId h) { return H::toPy(a.source(H::fromPy(h))); },
            nb::arg("halfedge"), "The halfedge's first endpoint in traversal order.");
    cls.def("target", [](const A &a, PyHalfedgeId h) { return H::toPy(a.target(H::fromPy(h))); },
            nb::arg("halfedge"), "The halfedge's second endpoint in traversal order.");
    cls.def("face", [](const A &a, PyHalfedgeId h) { return H::toPy(a.face(H::fromPy(h))); },
            nb::arg("halfedge"), "The face on the halfedge's left.");
    cls.def("outgoing", [](const A &a, PyVertexId v) { return H::toPy(a.outgoing(H::fromPy(v))); },
            nb::arg("vertex"),
            "One halfedge leaving the vertex, or the invalid handle when it is isolated.");
    cls.def("outgoingHalfedges",
            [](const A &a, PyVertexId v) { return H::toPy(a.outgoingHalfedges(H::fromPy(v))); },
            nb::arg("vertex"),
            "Every halfedge leaving the vertex, clockwise; empty for an isolated vertex. "
            "Also accepts the infinity handle, giving the angularly ordered fan of "
            "unbounded ends.");
    cls.def("degree", [](const A &a, PyVertexId v) { return a.degree(H::fromPy(v)); }, nb::arg("vertex"),
            "How many halfedges leave the vertex -- one per incident edge end, so a "
            "vertex where k lines cross has degree 2k.");
    cls.def("isUnbounded", [](const A &a) { return a.isUnbounded(); },
            "Whether the arrangement has any unbounded edge, equivalently whether the "
            "symbolic vertex at infinity exists.");
    cls.def("isUnbounded", [](const A &a, PyHalfedgeId h) { return a.isUnbounded(H::fromPy(h)); },
            nb::arg("halfedge"),
            "Whether the edge reaches infinity; the same for both of its halfedges.");
    cls.def("isUnbounded", [](const A &a, PyFaceId f) { return a.isUnbounded(H::fromPy(f)); },
            nb::arg("face"), "Whether the face is unbounded.");
    cls.def("isFictitious", [](const A &a, PyVertexId v) { return a.isFictitious(H::fromPy(v)); },
            nb::arg("vertex"), "Whether the handle is the symbolic vertex at infinity.");

    // --- faces ---
    cls.def("outerCycle", [](const A &a, PyFaceId f) { return H::toPy(a.outerCycle(H::fromPy(f))); },
            nb::arg("face"),
            "One halfedge of a bounded face's counterclockwise outer cycle; the invalid "
            "handle for an unbounded face.");
    cls.def("innerCycles",
            [](const A &a, PyFaceId f) {
                auto span = a.innerCycles(H::fromPy(f));
                return H::toPy(std::vector<typename A::HalfedgeId>(span.begin(), span.end()));
            },
            nb::arg("face"),
            "One starting halfedge per clockwise inner cycle. An unbounded face's "
            "boundary walks through infinity are represented here too.");
    cls.def("outerBoundaryOf", [](const A &a, PyFaceId f) { return H::toPy(a.outerBoundaryOf(H::fromPy(f))); },
            nb::arg("face"),
            "The halfedges of a bounded face's counterclockwise outer boundary; empty "
            "for an unbounded face.");
    cls.def("innerBoundariesOf",
            [](const A &a, PyFaceId f) { return H::toPy(a.innerBoundariesOf(H::fromPy(f))); },
            nb::arg("face"), "One list of halfedges per clockwise inner boundary.");
    cls.def("boundaryOf", [](const A &a, PyFaceId f) { return H::toPy(a.boundaryOf(H::fromPy(f))); },
            nb::arg("face"),
            "The outer boundary when there is one, then every inner boundary, in "
            "traversal order.");
    cls.def("hasSimpleBoundary", [](const A &a, PyFaceId f) { return a.hasSimpleBoundary(H::fromPy(f)); },
            nb::arg("face"),
            "Whether the face has neither a hole nor an edge with the face on both sides.");
    cls.def("polygonWithHoles", [](const A &a, PyFaceId f) { return a.polygonWithHoles(H::fromPy(f)); },
            nb::arg("face"),
            "The closure of a bounded face as a PolygonWithHoles; raises for an unbounded "
            "or invalid face. The result is regularized: a dangling edge sticking into "
            "the face is dropped and a cycle pinching shut at a vertex is cut there into "
            "one ring per side. Vertices in the middle of a straight stretch are kept.");
    cls.def("halfplaneIntersection",
            [](const A &a, PyFaceId f) { return a.halfplaneIntersection(H::fromPy(f)); }, nb::arg("face"),
            "The intersection of the supporting half-planes of the face's outer boundary, "
            "ignoring holes and two-sided edges. Accepts bounded and unbounded faces "
            "alike; it equals the face with its holes filled when that boundary is "
            "convex, and is the whole plane for the empty arrangement.");

    // --- labels and history ---
    cls.def("label", [](const A &a, PyHalfedgeId h) { return a.label(H::fromPy(h)); },
            nb::arg("halfedge"), edgeLabelDoc);
    cls.def("label", [](const A &a, PyFaceId f) { return a.label(H::fromPy(f)); }, nb::arg("face"),
            faceLabelDoc);
    cls.def("setLabel", [](A &a, PyHalfedgeId h, const Label &value) { a.label(H::fromPy(h)) = value; },
            nb::arg("halfedge"), nb::arg("value"), "Write an edge's label.");
    cls.def("setLabel", [](A &a, PyFaceId f, const Label &value) { a.label(H::fromPy(f)) = value; },
            nb::arg("face"), nb::arg("value"),
            "Write a face's label -- what to use to record a classification per cell.");
    cls.def("originsOf",
            [](const A &a, PyHalfedgeId h) {
                auto span = a.originsOf(H::fromPy(h));
                return std::vector<std::uint32_t>(span.begin(), span.end());
            },
            nb::arg("halfedge"),
            "The positions, in the shape list the arrangement was built from, of every "
            "input shape that produced this edge -- more than one exactly when the input "
            "overlaps along it. Sorted, without repetition.");
    cls.def("originsOf", [](const A &a, PyVertexId v) { return a.originsOf(H::fromPy(v)); },
            nb::arg("vertex"),
            "The same positions for every input shape passing through a vertex, the union "
            "over its incident edges. An isolated vertex is incident to no edge and has "
            "no origins, even when an input point put it there.");

    // --- point location ---
    cls.def("buildPointLocation", [](A &a) { a.buildPointLocation(); },
            "Build the exact randomized trapezoidal map and search DAG, after which "
            "locateFace()/locateCell() answer in expected logarithmic time instead of "
            "scanning the edges. Expected O(E log E) time and O(E) space.");
    cls.def("hasPointLocation", [](const A &a) { return a.hasPointLocation(); },
            "Whether the point-location index has been built.");
    cls.def("clearPointLocation", [](A &a) { a.clearPointLocation(); },
            "Release this arrangement's reference to the point-location index.");
    cls.def("locateFace", [](const A &a, const Point &p) { return H::toPy(a.locateFace(p)); },
            nb::arg("point"),
            "The face containing the point. A point on an edge or a vertex belongs to no "
            "face, and the answer is then the face an infinitesimal displacement of the "
            "query lands in.");
    cls.def("locateCell", [](const A &a, const Point &p) { return H::toPy(a.locateCell(p)); },
            nb::arg("point"),
            "The cell that actually contains the point, as a VertexId, a HalfedgeId or a "
            "FaceId -- tell them apart with isinstance().");

    // --- tracing a directed curve through the cells ---
    //
    // The walk reports the cells in order along the curve. Where the curve
    // meets an edge only at one of its endpoints, the vertex there stands for
    // the contact and the edge is not reported; an edge is named by one of its
    // two twin halfedges, and a chain meeting a cell more than once reports it
    // at its first encounter. With a point-location index built, the search is
    // earliest-first, so firstIntersecting() on a long or unbounded curve pays
    // only for its beginning.
    PGL_ARRANGEMENT_QUERY(cls, A, OrientedSegment);
    PGL_ARRANGEMENT_QUERY(cls, A, OrientedLine);
    PGL_ARRANGEMENT_QUERY(cls, A, Ray);
    PGL_ARRANGEMENT_QUERY(cls, A, MonotoneChain);
    PGL_ARRANGEMENT_QUERY(cls, A, Polyline);

    // --- the combinatorial view ---
    cls.def("asGraph",
            [](const A &a) {
                if constexpr (std::is_same_v<typename A::VertexId, PyVertexId>) {
                    return a.asGraph();
                } else {
                    const auto graph = a.asGraph();
                    pgl::Graph<PyVertexId> result;
                    for (const auto &v : graph.vertices())
                        result.addVertex(H::toPy(v));
                    for (const auto &e : graph.edges())
                        result.addEdge(H::toPy(e[0]), H::toPy(e[1]));
                    return result;
                }
            },
            "The vertex-edge incidence structure as an ArrangementGraph over vertex "
            "handles, isolated vertices included. The symbolic vertex at infinity is one "
            "of them whenever the arrangement has it. A graph is simple, so a line -- "
            "whose two ends are that same vertex -- contributes a self-loop and hence no "
            "graph edge, and two edges sharing both endpoints coalesce into one.");

    cls.def("__repr__", [name](const A &a) {
        std::ostringstream out;
        out << name << "(vertices=" << a.vertexCount() << ", edges=" << a.edgeCount()
            << ", faces=" << a.faceCount() << ")";
        return out.str();
    });

    return cls;
}

}  // namespace pypgl
