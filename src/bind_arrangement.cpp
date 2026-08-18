#include <nanobind/stl/optional.h>
#include <nanobind/stl/variant.h>

#include "bind_graph.h"

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
// **One instantiation, with Point labels.** pgl templates the class on a label
// type, and its Voronoi diagram (Triangulation.voronoiDiagram) labels each face
// with the site that generated it -- so pypgl binds Arrangement<Point, Point>,
// which makes a Voronoi diagram and a plain arrangement the same Python class.
// For an arrangement built from shapes, the labels simply start out as the
// default Point(0, 0); label(cell) reads one and setLabel(cell, value) writes
// it, which is what lets a caller record a classification per cell.
//
// **Handles are their own types.** VertexId, HalfedgeId and FaceId are distinct
// classes rather than plain ints, mirroring pgl's strongly typed handles: a
// face handle cannot be passed where a vertex handle is meant, and locateCell()
// can hand back "the cell containing this point" as whichever of the three it
// is, for the caller to tell apart with isinstance().
//
// Not bound: visitIntersecting's callback form (reportIntersecting /
// firstIntersecting / emptyIntersecting give the same information without a
// Python callback, as everywhere else in pypgl), and the raw locate*Linear
// variants, which are the same queries with the index deliberately bypassed.

namespace {

using Arrangement = pgl::Arrangement<Point, Point>;
using VertexId = Arrangement::VertexId;
using HalfedgeId = Arrangement::HalfedgeId;
using FaceId = Arrangement::FaceId;

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

// The arrangement carries its label type into the shapes it hands back, so its
// own SegmentType is Segment<Point, Point> rather than the unlabeled Segment
// pypgl binds -- a distinct C++ type, and one no caster knows. These rebuild
// each piece as the bound, label-free shape it geometrically is. (Only the edge
// and halfedge accessors need it: polygonWithHoles() and halfplaneIntersection()
// are declared over plain points already.)
using Edge = std::variant<Segment, Line, Ray>;
using HalfedgeGeometry = std::variant<OrientedSegment, OrientedLine, Ray>;

Edge stripLabel(const Arrangement::EdgeType &edge) {
    return std::visit(
        [](const auto &e) -> Edge {
            using T = std::decay_t<decltype(e)>;
            if constexpr (std::is_same_v<T, Arrangement::SegmentType>)
                return Segment(e.min(), e.max());
            else if constexpr (std::is_same_v<T, Arrangement::LineType>)
                return Line(e.min(), e.max());
            else
                return Ray(e.source(), e.target());
        },
        edge);
}

HalfedgeGeometry stripLabel(const Arrangement::HalfedgeType &halfedge) {
    return std::visit(
        [](const auto &h) -> HalfedgeGeometry {
            using T = std::decay_t<decltype(h)>;
            if constexpr (std::is_same_v<T, Arrangement::OrientedSegmentType>)
                return OrientedSegment(h.source(), h.target());
            else if constexpr (std::is_same_v<T, Arrangement::OrientedLineType>)
                return OrientedLine(h.source(), h.target());
            else
                return Ray(h.source(), h.target());
        },
        halfedge);
}

// One query overload of the curve-tracing family, for each shape pgl's walk
// accepts (a directed curve: it reports the cells in order along it).
#define PGL_ARRANGEMENT_QUERY(cls, QueryT)                                                     \
    cls.def("reportIntersecting",                                                              \
            [](const Arrangement &a, const QueryT &q) { return a.reportIntersecting(q); },      \
            nb::arg("curve"));                                                                  \
    cls.def("firstIntersecting",                                                               \
            [](const Arrangement &a, const QueryT &q) { return a.firstIntersecting(q); },       \
            nb::arg("curve"));                                                                  \
    cls.def("emptyIntersecting",                                                               \
            [](const Arrangement &a, const QueryT &q) { return a.emptyIntersecting(q); },       \
            nb::arg("curve"))

}  // namespace

void bind_arrangement(nb::module_ &m) {
    bindHandle<VertexId>(m, "VertexId");
    bindHandle<HalfedgeId>(m, "HalfedgeId");
    bindHandle<FaceId>(m, "FaceId");

    // The 1-skeleton of an arrangement is a graph over *handles*, not over
    // points: the symbolic vertex at infinity has no position, so it could not
    // be keyed by one. Same class as Graph in every other respect.
    bindGraph<VertexId>(m, "ArrangementGraph");

    nb::class_<Arrangement> cls(m, "Arrangement");

    cls.def(nb::init<>(), "Create the empty arrangement: no vertex, no edge, one face.");
    cls.def("__init__",
            [](Arrangement *self, const std::vector<AnyShape> &shapes) {
                new (self) Arrangement(shapes);
            },
            nb::arg("shapes"),
            "Build the arrangement of the given shapes, in any mix: points, segments and "
            "oriented segments, polylines and monotone chains, the boundaries of "
            "triangles, rectangles, convexes, polygons and regions, and lines, oriented "
            "lines and rays. The input may cross, overlap collinearly, repeat, share "
            "endpoints or dangle with a free end; overlapping stretches are merged into "
            "one edge that remembers every input shape covering it.");
    cls.def("__init__",
            [](Arrangement *self, const std::vector<AnyShape> &shapes, const std::vector<Point> &points) {
                new (self) Arrangement(shapes, points);
            },
            nb::arg("shapes"), nb::arg("points"),
            "Build the arrangement of the given shapes, additionally making every given "
            "point a vertex wherever it falls: a point on a shape splits it there, and a "
            "point on nothing becomes a vertex incident to no edge, in the interior of "
            "the face holding it.");

    // --- cells ---
    cls.def("vertexCount", [](const Arrangement &a) { return a.vertexCount(); },
            "Number of finite vertices. The symbolic vertex at infinity is not one of "
            "them; its handle index is exactly this count.");
    cls.def("edgeCount", [](const Arrangement &a) { return a.edgeCount(); }, "Number of geometric edges.");
    cls.def("halfedgeCount", [](const Arrangement &a) { return a.halfedgeCount(); },
            "Twice edgeCount(): halfedges have consecutive handles and twin pairs are "
            "adjacent.");
    cls.def("faceCount", [](const Arrangement &a) { return a.faceCount(); },
            "Number of faces, every unbounded one included. Face 0 is unbounded, though "
            "a line or a pair of rays can create several unbounded faces.");
    cls.def("vertices", [](const Arrangement &a) { return a.vertices(); },
            "The positions of the finite vertices, in handle order.");
    cls.def("edges",
            [](const Arrangement &a) {
                std::vector<Edge> result;
                for (const auto &edge : a.edges())
                    result.push_back(stripLabel(edge));
                return result;
            },
            "One shape per edge, in edge-index order: a Segment, a Line or a Ray.");
    cls.def("boundedEdges",
            [](const Arrangement &a) {
                std::vector<Segment> result;
                for (const auto &edge : a.boundedEdges())
                    result.emplace_back(edge.min(), edge.max());
                return result;
            },
            "Only the edges that are segments.");

    // --- handles to geometry ---
    cls.def("position", [](const Arrangement &a, VertexId v) { return a[v]; }, nb::arg("vertex"),
            "The position of a finite vertex. Raises for the symbolic vertex at "
            "infinity, which has none. (C++ spells this a[v].)");
    cls.def("halfedge", [](const Arrangement &a, HalfedgeId h) { return stripLabel(a[h]); }, nb::arg("halfedge"),
            "The geometry of a halfedge, directed along it: an OrientedSegment, an "
            "OrientedLine or a Ray. The two halfedges of a segment or line give opposite "
            "orientations; a ray has one finite source, so both of its halfedges give "
            "the same Ray though they stay distinct halfedges. (C++ spells this a[h].)");
    cls.def("witness", [](const Arrangement &a, VertexId v) { return a.witness(v); }, nb::arg("vertex"),
            "The vertex itself; raises for the vertex at infinity.");
    cls.def("witness", [](const Arrangement &a, HalfedgeId h) { return a.witness(h); }, nb::arg("halfedge"),
            "A point in the relative interior of the edge.");
    cls.def("witness", [](const Arrangement &a, FaceId f) { return a.witness(f); }, nb::arg("face"),
            "A point strictly inside a bounded face -- a diagonal midpoint or an ear's "
            "interior point when the boundary is one simple ring, and otherwise the more "
            "expensive point obtained by leaving a boundary edge along the inward normal.");

    // --- incidence and topology ---
    cls.def("twin", [](const Arrangement &a, HalfedgeId h) { return a.twin(h); }, nb::arg("halfedge"),
            "The other halfedge of the same edge.");
    cls.def("next", [](const Arrangement &a, HalfedgeId h) { return a.next(h); }, nb::arg("halfedge"),
            "The following halfedge along the boundary of the face on the left; "
            "following it repeatedly traverses one boundary cycle.");
    cls.def("source", [](const Arrangement &a, HalfedgeId h) { return a.source(h); }, nb::arg("halfedge"),
            "The halfedge's first endpoint in traversal order.");
    cls.def("target", [](const Arrangement &a, HalfedgeId h) { return a.target(h); }, nb::arg("halfedge"),
            "The halfedge's second endpoint in traversal order.");
    cls.def("face", [](const Arrangement &a, HalfedgeId h) { return a.face(h); }, nb::arg("halfedge"),
            "The face on the halfedge's left.");
    cls.def("outgoing", [](const Arrangement &a, VertexId v) { return a.outgoing(v); }, nb::arg("vertex"),
            "One halfedge leaving the vertex, or the invalid handle when it is isolated.");
    cls.def("outgoingHalfedges", [](const Arrangement &a, VertexId v) { return a.outgoingHalfedges(v); },
            nb::arg("vertex"),
            "Every halfedge leaving the vertex, clockwise; empty for an isolated vertex. "
            "Also accepts the infinity handle, giving the angularly ordered fan of "
            "unbounded ends.");
    cls.def("degree", [](const Arrangement &a, VertexId v) { return a.degree(v); }, nb::arg("vertex"),
            "How many halfedges leave the vertex -- one per incident edge end, so a "
            "vertex where k lines cross has degree 2k.");
    cls.def("isUnbounded", [](const Arrangement &a) { return a.isUnbounded(); },
            "Whether the arrangement has any unbounded edge, equivalently whether the "
            "symbolic vertex at infinity exists.");
    cls.def("isUnbounded", [](const Arrangement &a, HalfedgeId h) { return a.isUnbounded(h); },
            nb::arg("halfedge"),
            "Whether the edge reaches infinity; the same for both of its halfedges.");
    cls.def("isUnbounded", [](const Arrangement &a, FaceId f) { return a.isUnbounded(f); },
            nb::arg("face"), "Whether the face is unbounded.");
    cls.def("isFictitious", [](const Arrangement &a, VertexId v) { return a.isFictitious(v); },
            nb::arg("vertex"), "Whether the handle is the symbolic vertex at infinity.");

    // --- faces ---
    cls.def("outerCycle", [](const Arrangement &a, FaceId f) { return a.outerCycle(f); }, nb::arg("face"),
            "One halfedge of a bounded face's counterclockwise outer cycle; the invalid "
            "handle for an unbounded face.");
    cls.def("innerCycles",
            [](const Arrangement &a, FaceId f) {
                auto span = a.innerCycles(f);
                return std::vector<HalfedgeId>(span.begin(), span.end());
            },
            nb::arg("face"),
            "One starting halfedge per clockwise inner cycle. An unbounded face's "
            "boundary walks through infinity are represented here too.");
    cls.def("outerBoundaryOf", [](const Arrangement &a, FaceId f) { return a.outerBoundaryOf(f); },
            nb::arg("face"),
            "The halfedges of a bounded face's counterclockwise outer boundary; empty "
            "for an unbounded face.");
    cls.def("innerBoundariesOf", [](const Arrangement &a, FaceId f) { return a.innerBoundariesOf(f); },
            nb::arg("face"), "One list of halfedges per clockwise inner boundary.");
    cls.def("boundaryOf", [](const Arrangement &a, FaceId f) { return a.boundaryOf(f); }, nb::arg("face"),
            "The outer boundary when there is one, then every inner boundary, in "
            "traversal order.");
    cls.def("hasSimpleBoundary", [](const Arrangement &a, FaceId f) { return a.hasSimpleBoundary(f); },
            nb::arg("face"),
            "Whether the face has neither a hole nor an edge with the face on both sides.");
    cls.def("polygonWithHoles", [](const Arrangement &a, FaceId f) { return a.polygonWithHoles(f); },
            nb::arg("face"),
            "The closure of a bounded face as a PolygonWithHoles; raises for an unbounded "
            "or invalid face. The result is regularized: a dangling edge sticking into "
            "the face is dropped and a cycle pinching shut at a vertex is cut there into "
            "one ring per side. Vertices in the middle of a straight stretch are kept.");
    cls.def("halfplaneIntersection", [](const Arrangement &a, FaceId f) { return a.halfplaneIntersection(f); },
            nb::arg("face"),
            "The intersection of the supporting half-planes of the face's outer boundary, "
            "ignoring holes and two-sided edges. Accepts bounded and unbounded faces "
            "alike; it equals the face with its holes filled when that boundary is "
            "convex, and is the whole plane for the empty arrangement.");

    // --- labels and history ---
    cls.def("label", [](const Arrangement &a, HalfedgeId h) { return a.label(h); }, nb::arg("halfedge"),
            "The label of an edge. It starts as the label of the input shape that "
            "produced it -- for a pypgl shape, which carries none, that is the default "
            "Point(0, 0) -- and setLabel() overwrites it.");
    cls.def("label", [](const Arrangement &a, FaceId f) { return a.label(f); }, nb::arg("face"),
            "The label of a face. Nothing in the input is a face, so it starts "
            "default-constructed; a Voronoi diagram is the exception, labelling each face "
            "with the site that generated it.");
    cls.def("setLabel", [](Arrangement &a, HalfedgeId h, const Point &value) { a.label(h) = value; },
            nb::arg("halfedge"), nb::arg("value"), "Write an edge's label.");
    cls.def("setLabel", [](Arrangement &a, FaceId f, const Point &value) { a.label(f) = value; },
            nb::arg("face"), nb::arg("value"),
            "Write a face's label -- what to use to record a classification per cell.");
    cls.def("originsOf",
            [](const Arrangement &a, HalfedgeId h) {
                auto span = a.originsOf(h);
                return std::vector<std::uint32_t>(span.begin(), span.end());
            },
            nb::arg("halfedge"),
            "The positions, in the shape list the arrangement was built from, of every "
            "input shape that produced this edge -- more than one exactly when the input "
            "overlaps along it. Sorted, without repetition.");
    cls.def("originsOf", [](const Arrangement &a, VertexId v) { return a.originsOf(v); }, nb::arg("vertex"),
            "The same positions for every input shape passing through a vertex, the union "
            "over its incident edges. An isolated vertex is incident to no edge and has "
            "no origins, even when an input point put it there.");

    // --- point location ---
    cls.def("buildPointLocation", [](Arrangement &a) { a.buildPointLocation(); },
            "Build the exact randomized trapezoidal map and search DAG, after which "
            "locateFace()/locateCell() answer in expected logarithmic time instead of "
            "scanning the edges. Expected O(E log E) time and O(E) space.");
    cls.def("hasPointLocation", [](const Arrangement &a) { return a.hasPointLocation(); },
            "Whether the point-location index has been built.");
    cls.def("clearPointLocation", [](Arrangement &a) { a.clearPointLocation(); },
            "Release this arrangement's reference to the point-location index.");
    cls.def("locateFace", [](const Arrangement &a, const Point &p) { return a.locateFace(p); }, nb::arg("point"),
            "The face containing the point. A point on an edge or a vertex belongs to no "
            "face, and the answer is then the face an infinitesimal displacement of the "
            "query lands in.");
    cls.def("locateCell", [](const Arrangement &a, const Point &p) { return a.locateCell(p); }, nb::arg("point"),
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
    PGL_ARRANGEMENT_QUERY(cls, OrientedSegment);
    PGL_ARRANGEMENT_QUERY(cls, OrientedLine);
    PGL_ARRANGEMENT_QUERY(cls, Ray);
    PGL_ARRANGEMENT_QUERY(cls, MonotoneChain);
    PGL_ARRANGEMENT_QUERY(cls, Polyline);

    // --- the combinatorial view ---
    cls.def("asGraph", [](const Arrangement &a) { return a.asGraph(); },
            "The vertex-edge incidence structure as an ArrangementGraph over vertex "
            "handles, isolated vertices included. The symbolic vertex at infinity is one "
            "of them whenever the arrangement has it. A graph is simple, so a line -- "
            "whose two ends are that same vertex -- contributes a self-loop and hence no "
            "graph edge, and two edges sharing both endpoints coalesce into one.");

    cls.def("__repr__", [](const Arrangement &a) {
        std::ostringstream out;
        out << "Arrangement(vertices=" << a.vertexCount() << ", edges=" << a.edgeCount()
            << ", faces=" << a.faceCount() << ")";
        return out.str();
    });
}
