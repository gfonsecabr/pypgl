#pragma once

// Shared definitions for every binding translation unit: the one bound numeric
// instantiation, the concrete shape aliases, value-semantics helpers, and the
// predicate-binding macro.

#include <nanobind/nanobind.h>
#include <nanobind/stl/array.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/variant.h>
#include <nanobind/stl/vector.h>

#include <compare>
#include <functional>
#include <sstream>

#include "casters.h"
#include "pgl.hpp"

namespace nb = nanobind;

namespace pypgl {

// pypgl binds exactly one numeric instantiation: pgl::ERational = Rational<BigInt>.
// All shapes are the corresponding pgl `E*` aliases over EPoint = Point<ERational>.
using Num = pgl::ERational;
using Point = pgl::EPoint;                         // pgl::Point<ERational>
using Segment = pgl::ESegment;                     // pgl::Segment<EPoint>
using OrientedSegment = pgl::EOrientedSegment;     // pgl::OrientedSegment<EPoint>
using Line = pgl::ELine;                           // pgl::Line<EPoint>
using OrientedLine = pgl::EOrientedLine;           // pgl::OrientedLine<EPoint>
using Ray = pgl::ERay;                             // pgl::Ray<EPoint>
using Halfplane = pgl::EHalfplane;                 // pgl::Halfplane<EPoint>
using Triangle = pgl::ETriangle;                   // pgl::Triangle<EPoint>
using Rectangle = pgl::ERectangle;                 // pgl::Rectangle<EPoint>
using Convex = pgl::EConvex;                        // pgl::Convex<EPoint>
using Polygon = pgl::EPolygon;                      // pgl::Polygon<EPoint>
using Disk = pgl::EDisk;                            // pgl::Disk<EPoint>
using MonotoneChain = pgl::EMonotoneChain;          // pgl::MonotoneChain<EPoint>
using Polyline = pgl::EPolyline;                    // pgl::Polyline<EPoint>
// A closed region: a simple outer polygon minus the *interiors* of a set of
// pairwise interior-disjoint polygonal holes, each contained in the outer one
// (shape/polygonwithholes.hpp). The one shape whose intersections can keep
// holes, and hence what every boolean operation and every non-convex Minkowski
// sum returns.
using PolygonWithHoles = pgl::EPolygonWithHoles;    // pgl::PolygonWithHoles<EPoint>
// The intersection of finitely many closed half-planes (shape/
// halfplaneintersection.hpp): convex like Convex, but -- unlike it -- possibly
// unbounded (a wedge, a strip, a half-plane, the whole plane) and possibly
// empty. Its vertices are generally not representable in the coordinate type of
// its half-planes, which is exactly why pypgl's single ERational instantiation
// suits it: the constructive accessors stay exact.
using HalfplaneIntersection = pgl::EHalfplaneIntersection;
// A set of PolygonWithHoles components with pairwise disjoint interiors
// (shape/polygonset.hpp), whose point set is simply their union. This is what
// closes the regularized boolean operations: a difference, a union or a
// symmetric difference of two regions can come apart into several pieces, and
// an island stranded inside a hole of the answer is a piece like any other. As
// a shape rather than a list, such a result can be fed straight back in,
// compared, hashed, drawn, transformed and measured.
using PolygonSet = pgl::EPolygonSet;               // pgl::PolygonSet<EPoint>

// Type-erased wrapper over one of the seventeen shapes above (shape/shape.hpp).
// Only used as ShapeTree's element/query type (bind_shapetree.cpp) -- see the
// casters.h caster for pgl::Shape<EPoint>, which is what keeps this wrapper
// itself unbound and invisible from Python.
using AnyShape = pgl::Shape<Point>;

// A mutable mesh over a fixed vertex set (algorithm/triangulation.hpp,
// pulled in transitively by pgl.hpp). Its edge type defaults to
// TriangleType::BoundaryType<false>, which for our Triangle already is
// Segment -- spelled out here rather than left to the default so both
// bind_triangulation.cpp and bind_canvas.cpp share one alias.
using Triangulation = pgl::Triangulation<Triangle, Segment>;

// A static spatial index (algorithm/shapetree.hpp) storing a mix of AnyShape
// elements, queryable by any AnyShape-convertible shape. Bound as a single
// Python class ("ShapeTree") in bind_shapetree.cpp -- the WeightFn template
// parameter is left at its default (no weight function), so pgl's weighted
// sumIntersecting/sumContainedIn are not exposed: every other pypgl traversal
// already returns a materialized list rather than taking a Python callback
// (see bind_triangulation.cpp), and a weight function would be exactly that.
using ShapeTree = pgl::ShapeTree<AnyShape>;

// One bit per cell of a rectangular window of the integer grid
// (algorithm/bitmatrix.hpp). This is the one bound class pypgl cannot hold over
// its own Point: pgl constrains BitMatrix to `std::signed_integral` coordinates,
// since a cell of the grid *is* an integer position, so BitMatrix<Point> (whose
// coordinates are ERational) is ill-formed by construction. The cells are
// therefore stored over `Cell = pgl::Point<std::int64_t>`, which never surfaces
// in Python: every cell crosses the boundary either as a pair of plain ints or
// as an ordinary pypgl Point, and every shape a matrix hands back
// (asPolygonSet, asPolygonWithHoles, convexHull, bbox, cells, ...) is widened
// into the bound ERational class by pgl's own cross-point-type converting
// constructors. int64_t is exactly what pgl itself picks for an ERational shape
// (grid_number_t<Rational<BigInt>> is int64_t), so `polygon.asBitMatrix()` and
// `BitMatrix(polygon)` name the same grid.
using Cell = pgl::Point<std::int64_t>;
using BitMatrix = pgl::BitMatrix<Cell>;

// A pypgl Point -> the cell of the grid it names. pgl's gridCoordinate is what
// does the checking, exactly as it does for asBitMatrix: a coordinate that is
// not a whole number, or is a whole one int64_t cannot hold, throws rather than
// being rounded (which would move the shape). Reused here rather than
// reimplemented so a bad coordinate reports the same message wherever it enters.
inline Cell toCell(const Point &p) {
    return Cell(pgl::detail::gridCoordinate<std::int64_t>(p.x()),
                pgl::detail::gridCoordinate<std::int64_t>(p.y()));
}

// A pypgl Rectangle -> the window of cells it covers. An empty rectangle has no
// corners to convert (pgl stores sentinel ones), so it maps to the empty window
// directly -- which is what BitMatrix's own Rectangle constructor does with it.
inline pgl::Rectangle<Cell> toGridWindow(const Rectangle &box) {
    if (box.empty()) return pgl::Rectangle<Cell>();
    return pgl::Rectangle<Cell>(toCell(box.min()), toCell(box.max()), true);
}

// An affine transformation of the plane (core/transformation.hpp), templated
// only on the matrix-entry type -- unlike every shape above it carries no
// point/label type of its own. Bound over the same single numeric
// instantiation as everything else (Num = ERational) in bind_transformation.cpp.
using Transformation = pgl::Transformation<Num>;

// pgl's orientation() returns a std::partial_ordering, which nanobind has no
// caster for (and which would be a strange thing to hand a Python caller
// anyway); expose the sign it stands for instead: -1 to the right of the
// direction, +1 to the left, 0 collinear. The `unordered` case cannot arise —
// the comparison is an exact rational determinant, never a NaN.
inline int orientationSign(std::partial_ordering o) {
    if (o == std::partial_ordering::less) return -1;
    if (o == std::partial_ordering::greater) return 1;
    return 0;
}

// A flat coordinate list -> the points it spells, consumed in (x, y) pairs:
// [x0, y0, x1, y1, ...]. This is the Python spelling of pgl's
// `std::initializer_list<NumberType>` constructors (Convex, Polygon,
// MonotoneChain, Polyline all have one), which let C++ write
// `Polygon{0,0, 4,0, 4,4}` without naming a Point per vertex.
//
// pgl states the even-count requirement as an assert(), which the release build
// pypgl ships compiles out, so it is checked here and reported as a ValueError
// rather than silently dropping the odd trailing value.
inline std::vector<Point> pointsFromCoords(const std::vector<Num> &coords) {
    if (coords.size() % 2 != 0)
        throw nb::value_error(
            "expected an even number of coordinates: a flat list is read in "
            "(x, y) pairs, one per vertex");
    std::vector<Point> points;
    points.reserve(coords.size() / 2);
    for (std::size_t i = 0; i + 1 < coords.size(); i += 2)
        points.emplace_back(coords[i], coords[i + 1]);
    return points;
}

// repr, ordering, equality, and (optionally) hashing — uniform across all
// value-type shapes. Fixed-size shapes are immutable and hashable. The
// variable-size shapes (Convex, later Polygon) are mutable so they support
// O(1) in-place translation; following Python's mutable-implies-unhashable rule
// they are bound with `hashable = false`, which sets `__hash__` to None so they
// cannot be used as dict keys / set members (and thus never corrupt a container
// when mutated).
template <class T, class Class>
void bind_value_semantics(Class &cls, bool hashable = true) {
    cls.def("__repr__", [](const T &self) {
        std::ostringstream out;
        out << self;
        return out.str();
    });
    cls.def("__str__", [](const T &self) {
        std::ostringstream out;
        out << self;
        return out.str();
    });
    cls.def("__eq__", [](const T &a, const T &b) { return a == b; }, nb::is_operator());
    cls.def("__ne__", [](const T &a, const T &b) { return !(a == b); }, nb::is_operator());
    cls.def("__lt__", [](const T &a, const T &b) { return a < b; }, nb::is_operator());
    cls.def("__le__", [](const T &a, const T &b) { return !(b < a); }, nb::is_operator());
    cls.def("__gt__", [](const T &a, const T &b) { return b < a; }, nb::is_operator());
    cls.def("__ge__", [](const T &a, const T &b) { return !(a < b); }, nb::is_operator());
    if (hashable)
        cls.def("__hash__", [](const T &self) { return std::hash<T>{}(self); });
    else
        cls.attr("__hash__") = nb::none();
}

}  // namespace pypgl

// Bind one predicate overload (self.NAME(other)) for a given other-shape type.
#define PGL_PRED(cls, SelfT, NAME, OtherT)                                  \
    cls.def(#NAME,                                                          \
            [](const SelfT &self, const OtherT &other) {                    \
                return self.NAME(other);                                    \
            },                                                              \
            nb::arg("other"))

// -----------------------------------------------------------------------------
// Degeneracy classification
//
// pgl splits degenerate shapes in two. Some are *well defined*: a triangle with
// three collinear vertices really is a segment, a radius-zero disk really is a
// point, and every operation on them answers the limit case. Others are
// **undefined** -- a line through two equal points has no direction, a disk
// through three distinct collinear points could be either of two half-planes --
// and for those every geometric operation is undefined behavior in the C++
// sense (any value may come back, but no crash or hang). `isUndefined()` is what
// tells the two apart, and it is bound on every shape.
//
// The well-defined collapses are named by `isPoint`/`isSegment`, with
// `getIfPoint`/`getIfSegment` returning the shape the point set actually is
// (None when it is not that shape) -- std::optional, so nanobind's optional
// caster gives back a Point/Segment or None. A shape that has dropped below its
// natural dimension is *entirely boundary with empty interior*, so on it
// `boundaryContains` coincides with `contains`, and `interiorContains` /
// `interiorsIntersect` are always False.
//
// Three tiers, since not every shape can collapse in every way:
//   PGL_BIND_IS_UNDEFINED      -- Line, OrientedLine, Ray, Halfplane: nothing to
//                                 collapse *to* (a degenerate one is undefined
//                                 outright), so only isUndefined.
//   PGL_BIND_DEGENERACY_POINT  -- Segment, OrientedSegment, Disk: can only ever
//                                 collapse to a single point.
//   PGL_BIND_DEGENERACY        -- Triangle, Rectangle, Convex, Polygon,
//                                 MonotoneChain, Polyline, HalfplaneIntersection:
//                                 both collapses.
// PolygonWithHoles has isPoint/isSegment but no getIf* pair upstream, so it
// binds them by hand rather than through these macros.

#define PGL_BIND_IS_UNDEFINED(cls, SelfT)                                            \
    cls.def("isUndefined", [](const SelfT &s) { return s.isUndefined(); },           \
            "Whether the shape is degenerate in a way that has no meaningful "       \
            "interpretation, making every geometric operation on it undefined.")

#define PGL_BIND_DEGENERACY_POINT(cls, SelfT)                                        \
    PGL_BIND_IS_UNDEFINED(cls, SelfT);                                               \
    cls.def("isPoint", [](const SelfT &s) { return s.isPoint(); },                   \
            "Whether the shape has collapsed to cover exactly one point.");          \
    cls.def("getIfPoint", [](const SelfT &s) { return s.getIfPoint(); },             \
            "The single point the shape covers, or None if it covers more.")

#define PGL_BIND_DEGENERACY(cls, SelfT)                                              \
    PGL_BIND_DEGENERACY_POINT(cls, SelfT);                                           \
    cls.def("isSegment", [](const SelfT &s) { return s.isSegment(); },               \
            "Whether the shape has collapsed to cover exactly one segment of "       \
            "positive length.");                                                     \
    cls.def("getIfSegment", [](const SelfT &s) { return s.getIfSegment(); },         \
            "The single segment the shape covers, or None if it covers more.")

// The four no-argument helpers shared by every line-like shape (Segment,
// OrientedSegment, Line, OrientedLine, Ray). `slope` is exact (ERational) but
// undefined for vertical shapes — division by zero.
#define PGL_BIND_LINE_HELPERS(cls, SelfT)                                          \
    cls.def("slope", [](const SelfT &s) { return s.slope(); },                    \
            "Exact signed slope (ERational). Undefined for vertical shapes.");     \
    cls.def("isVertical", [](const SelfT &s) { return s.isVertical(); },          \
            "Whether the supporting direction is vertical.");                      \
    cls.def("isHorizontal", [](const SelfT &s) { return s.isHorizontal(); },      \
            "Whether the supporting direction is horizontal.");                    \
    cls.def("isDegenerate", [](const SelfT &s) { return s.isDegenerate(); },       \
            "Whether the two defining points coincide.")

// The two vertical/horizontal ray-shooting queries of the line-like shapes
// (Segment, OrientedSegment, Line, OrientedLine, Ray): the coordinate at which
// the shape meets the vertical line x = given (resp. the horizontal line
// y = given), or None when it does not meet it at all — a segment or ray that
// stops short. Exact: ResultNumber defaults to the number type (ERational), so
// the division stays a Fraction. A shape that is *itself* vertical meets x at
// all of its points; pgl resolves that by returning the smaller coordinate
// (likewise for a horizontal shape and xAtY). MonotoneChain has its own yAtX
// with a different contract (see bind_chains.cpp) and is not bound here.
#define PGL_BIND_XY_AT(cls, SelfT)                                                      \
    cls.def("yAtX", [](const SelfT &s, const ::pypgl::Num &x) { return s.yAtX(x); },     \
            nb::arg("x"),                                                                \
            "Exact y coordinate where the shape meets the vertical line at x, or None.");\
    cls.def("xAtY", [](const SelfT &s, const ::pypgl::Num &y) { return s.xAtY(y); },     \
            nb::arg("y"),                                                                \
            "Exact x coordinate where the shape meets the horizontal line at y, or None.")

// The direction-dependent helpers of the *oriented* shapes (OrientedSegment,
// OrientedLine, Ray): which side of the directed line a point falls on, and the
// two closed half-planes that side splits the plane into. `orientation` returns
// a plain sign — see orientationSign above.
#define PGL_BIND_ORIENTED_HELPERS(cls, SelfT)                                                        \
    cls.def("orientation",                                                                           \
            [](const SelfT &s, const ::pypgl::Point &p) {                                            \
                return ::pypgl::orientationSign(s.orientation(p));                                   \
            },                                                                                       \
            nb::arg("point"),                                                                        \
            "Sign of (source, target, point): -1 if the point is to the right of the direction, "    \
            "+1 to the left, 0 if collinear.");                                                      \
    cls.def("rightHalfplane", [](const SelfT &s) { return s.rightHalfplane(); },                     \
            "Closed half-plane to the right of the direction (orientation(p) <= 0).");               \
    cls.def("leftHalfplane", [](const SelfT &s) { return s.leftHalfplane(); },                       \
            "Closed half-plane to the left of the direction (orientation(p) >= 0).")

// The two closed half-planes bounded by the supporting line of a shape that has
// one (Line, OrientedLine, Ray) — split by y, so unlike right/leftHalfplane
// these do not depend on the shape's orientation.
#define PGL_BIND_HALFPLANES(cls, SelfT)                                             \
    cls.def("halfplaneAbove", [](const SelfT &s) { return s.halfplaneAbove(); },     \
            "Closed half-plane above the supporting line.");                         \
    cls.def("halfplaneBelow", [](const SelfT &s) { return s.halfplaneBelow(); },     \
            "Closed half-plane below the supporting line.")

// collinear: Self against a Point and the five line-like shapes.
#define PGL_BIND_COLLINEAR(cls, SelfT)                       \
    PGL_PRED(cls, SelfT, collinear, ::pypgl::Point);            \
    PGL_PRED(cls, SelfT, collinear, ::pypgl::Segment);          \
    PGL_PRED(cls, SelfT, collinear, ::pypgl::OrientedSegment);  \
    PGL_PRED(cls, SelfT, collinear, ::pypgl::Line);             \
    PGL_PRED(cls, SelfT, collinear, ::pypgl::OrientedLine);     \
    PGL_PRED(cls, SelfT, collinear, ::pypgl::Ray)

// parallel: Self against the five line-like shapes (no Point — points have no
// direction).
#define PGL_BIND_PARALLEL(cls, SelfT)                        \
    PGL_PRED(cls, SelfT, parallel, ::pypgl::Segment);          \
    PGL_PRED(cls, SelfT, parallel, ::pypgl::OrientedSegment);  \
    PGL_PRED(cls, SelfT, parallel, ::pypgl::Line);             \
    PGL_PRED(cls, SelfT, parallel, ::pypgl::OrientedLine);     \
    PGL_PRED(cls, SelfT, parallel, ::pypgl::Ray)

// Value-returning arithmetic for the immutable fixed-size shapes: translation
// by a Point (`+`, `-`, both orders) and scaling by a scalar (`*`, `/`). Uses
// pgl's free operators, which return a fresh shape. Not for Point (which adds
// points to points and has a unary minus) nor for the mutable Convex (no free
// operators; see its in-place bindings).
#define PGL_BIND_OPERATORS(cls, SelfT)                                                          \
    cls.def("__add__",  [](const SelfT &s, const ::pypgl::Point &p) { return s + p; }, nb::is_operator());  \
    cls.def("__radd__", [](const SelfT &s, const ::pypgl::Point &p) { return p + s; }, nb::is_operator());  \
    cls.def("__sub__",  [](const SelfT &s, const ::pypgl::Point &p) { return s - p; }, nb::is_operator());  \
    cls.def("__mul__",  [](const SelfT &s, const ::pypgl::Num &k)   { return s * k; }, nb::is_operator());  \
    cls.def("__rmul__", [](const SelfT &s, const ::pypgl::Num &k)   { return k * s; }, nb::is_operator());  \
    cls.def("__truediv__", [](const SelfT &s, const ::pypgl::Num &k) { return s / k; }, nb::is_operator())

// Value-returning rigid/axis transforms (return a new shape). Shared by every
// shape, mutable or not. `rotated90` rotates by 90*k degrees about the origin;
// the `scaled{Up,Down}{X,Y}` methods scale a single axis by an exact scalar.
#define PGL_BIND_TRANSFORMS(cls, SelfT)                                                                        \
    cls.def("rotated90", [](const SelfT &s, int k) { return s.rotated90(k); }, nb::arg("k") = 1,               \
            "Return the shape rotated by 90*k degrees about the origin.");                                     \
    cls.def("scaledUpX", [](const SelfT &s, const ::pypgl::Num &k) { return s.scaledUpX(k); }, nb::arg("scalar"),   \
            "Return the shape with its x-coordinates multiplied by scalar.");                                  \
    cls.def("scaledUpY", [](const SelfT &s, const ::pypgl::Num &k) { return s.scaledUpY(k); }, nb::arg("scalar"),   \
            "Return the shape with its y-coordinates multiplied by scalar.");                                  \
    cls.def("scaledDownX", [](const SelfT &s, const ::pypgl::Num &k) { return s.scaledDownX(k); }, nb::arg("scalar"), \
            "Return the shape with its x-coordinates divided by scalar.");                                     \
    cls.def("scaledDownY", [](const SelfT &s, const ::pypgl::Num &k) { return s.scaledDownY(k); }, nb::arg("scalar"), \
            "Return the shape with its y-coordinates divided by scalar.")

// The convex hull, bound on every shape that has a bbox and can be written as
// the hull of finitely many points -- the eleven bounded ones other than the
// Disk, plus the HalfplaneIntersection, which raises when it is unbounded.
// Twelve in all: not the Disk, whose hull is itself and is no polygon, and not
// the four unbounded shapes, which have no bbox to begin with. The answer is always a Convex, and it is what
// makes the shapes a Minkowski sum or erosion refuses reachable: eroding by a
// hull is the convex approximation a caller can always ask for by hand.
#define PGL_BIND_CONVEX_HULL(cls, SelfT)                                       \
    cls.def("convexHull", [](const SelfT &s) { return s.convexHull(); },       \
            "The convex hull of the shape's points, as a Convex.")

// Rasterization onto the integer grid, bound on the three region shapes pgl
// gives it to (Polygon, PolygonWithHoles, PolygonSet). Only a rectilinear region
// *is* a set of grid cells, so every edge must be axis-parallel; and only whole
// coordinates name a cell, so a fractional one is refused rather than rounded
// (rounding it would move the region). Both are pgl's own checks -- the
// ResultNumber of asBitMatrix defaults, for an ERational shape, to exactly the
// int64_t grid ::pypgl::BitMatrix stores. Use innerRaster/outerRaster to
// approximate any other shape.
#define PGL_BIND_AS_BIT_MATRIX(cls, SelfT)                                                      \
    cls.def("asBitMatrix", [](const SelfT &s) { return s.asBitMatrix(); },                      \
            "The shape rasterized into a BitMatrix over its bounding box, one bit per "         \
            "covered cell (holes and the gaps between components left unset). Raises if an "    \
            "edge is not axis-parallel, or a coordinate is not a whole number the grid can "    \
            "hold; use innerRaster/outerRaster to approximate any other shape.")

// Queries over a shape's defining points, bound on every shape that has them
// (all but Point, whose `index` takes a coordinate and which has no interior):
//   pointInside()        — an exact interior point (ResultNumber defaults to
//                          ERational, so the /2 or /4 it uses stays exact);
//   verticesContain(p)   — is p one of the defining points?;
//   index(p)             — position of the defining point equal to p, else -1.
#define PGL_BIND_VERTEX_QUERIES(cls, SelfT)                                                          \
    cls.def("pointInside", [](const SelfT &s) { return s.pointInside(); },                            \
            "An exact point strictly inside the shape.");                                             \
    cls.def("verticesContain", [](const SelfT &s, const ::pypgl::Point &p) { return s.verticesContain(p); }, \
            nb::arg("point"), "Whether the point is one of the shape's defining points.");            \
    cls.def("index", [](const SelfT &s, const ::pypgl::Point &p) -> std::optional<std::ptrdiff_t> {   \
                auto i = s.index(p);                                                                  \
                if (i < 0) return std::nullopt;                                                       \
                return i;                                                                             \
            }, nb::arg("point"), "Index of the defining point equal to point, or None if none.")

// Indexed access over a shape's defining points (or, for Point, its two
// coordinates): `size()` is the count and `get(i)` returns the i-th element
// with i taken modulo size() (negative indices wrap from the end), so it never
// raises. Python's `len(shape)`, `shape[i]`, and iteration are wired to these
// in __init__.py for every shape.
#define PGL_BIND_INDEXING(cls, SelfT)                                                     \
    cls.def("size", [](const SelfT &s) { return s.size(); }, "Number of indexable elements."); \
    cls.def("get", [](const SelfT &s, std::ptrdiff_t i) { return s.get(i); }, nb::arg("index"), \
            "The i-th element, with i taken modulo size() (cyclic).")

// Bind the seven uniform predicates of SelfT against one OtherT.
#define PGL_BIND_PREDICATES(cls, SelfT, OtherT)        \
    PGL_PRED(cls, SelfT, contains, OtherT);            \
    PGL_PRED(cls, SelfT, boundaryContains, OtherT);    \
    PGL_PRED(cls, SelfT, interiorContains, OtherT);    \
    PGL_PRED(cls, SelfT, intersects, OtherT);          \
    PGL_PRED(cls, SelfT, interiorsIntersect, OtherT);  \
    PGL_PRED(cls, SelfT, separates, OtherT);           \
    PGL_PRED(cls, SelfT, crosses, OtherT)

// Containment of an *open* segment, bound on the three region shapes pgl
// defines it for (Polygon, PolygonWithHoles, PolygonSet). It is the predicate
// `interiorContains` cannot express: the segment's endpoints may sit on the
// boundary as long as everything strictly between them stays strictly inside,
// which is exactly what a visibility edge between two boundary vertices needs.
// The operand is a Segment and only a Segment -- upstream gates it on
// SegmentConcept, which an OrientedSegment does not satisfy.
#define PGL_BIND_INTERIOR_CONTAINS_INTERIOR(cls, SelfT)                                    \
    cls.def("interiorContainsInterior",                                                    \
            [](const SelfT &self, const ::pypgl::Segment &other) {                         \
                return self.interiorContainsInterior(other);                               \
            },                                                                             \
            nb::arg("segment"),                                                            \
            "Whether the open segment lies in this shape's strict interior. Either "       \
            "endpoint may lie on the boundary; every point strictly between them must "    \
            "not. A degenerate segment is accepted exactly when its sole point is "        \
            "contained.")

// Bind the exact squared distance self.squaredDistance(other) for one OtherT.
// ResultNumber defaults to the number type (ERational), so the result is the
// exact squared Euclidean distance as a Fraction — never an approximation.
#define PGL_SQDIST(cls, SelfT, OtherT)                                       \
    cls.def("squaredDistance",                                              \
            [](const SelfT &self, const OtherT &other) {                    \
                return self.squaredDistance(other);                         \
            },                                                              \
            nb::arg("other"))

// squaredDistance of SelfT against every bound shape (all sixteen, including
// itself). pgl makes every pair available (an explicit overload on the
// higher-rank shape plus rank-based forwarding on the lower-rank one), so
// every shape in this list can safely call the macro on itself and on each
// other. Disk's pairs against Convex/Polygon were the last gap (pgl fix:
// Convex::squaredDistance(Disk) plus a generic shapeRank-based forwarder on
// Disk); all pairs return the shapes' own declared type (a Fraction between
// two non-Disk shapes, a float whenever Disk is on either side, since the
// gap to a disjoint disk is generally irrational).
#define PGL_BIND_ALL_SQUARED_DISTANCE(cls, SelfT)            \
    PGL_SQDIST(cls, SelfT, ::pypgl::Point);                     \
    PGL_SQDIST(cls, SelfT, ::pypgl::Segment);                   \
    PGL_SQDIST(cls, SelfT, ::pypgl::OrientedSegment);           \
    PGL_SQDIST(cls, SelfT, ::pypgl::Line);                      \
    PGL_SQDIST(cls, SelfT, ::pypgl::OrientedLine);              \
    PGL_SQDIST(cls, SelfT, ::pypgl::Ray);                       \
    PGL_SQDIST(cls, SelfT, ::pypgl::Halfplane);                 \
    PGL_SQDIST(cls, SelfT, ::pypgl::Triangle);                  \
    PGL_SQDIST(cls, SelfT, ::pypgl::Rectangle);                 \
    PGL_SQDIST(cls, SelfT, ::pypgl::Convex);                    \
    PGL_SQDIST(cls, SelfT, ::pypgl::MonotoneChain);             \
    PGL_SQDIST(cls, SelfT, ::pypgl::Polyline);                  \
    PGL_SQDIST(cls, SelfT, ::pypgl::Polygon);                    \
    PGL_SQDIST(cls, SelfT, ::pypgl::PolygonWithHoles);           \
    PGL_SQDIST(cls, SelfT, ::pypgl::HalfplaneIntersection);      \
    PGL_SQDIST(cls, SelfT, ::pypgl::PolygonSet);                 \
    PGL_SQDIST(cls, SelfT, ::pypgl::Disk)

// samePointSet of SelfT against every bound shape (all seventeen, including
// itself): whether the two shapes are the same set of points, which is what
// `a.contains(b) and b.contains(a)` says but decided directly and usually
// faster. It is *not* `==`: equality compares representations of one type, so
// it cannot compare across types at all, and even within one it can disagree --
// a Polygon carrying a redundant vertex in the middle of an edge covers the
// same points as one without it, yet the two are unequal. Every pair is
// implemented (pgl's implementation/samepointset.hpp specializes all of them),
// so this macro is called on every shape with every shape.
#define PGL_BIND_ALL_SAME_POINT_SET(cls, SelfT)                  \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::Point);          \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::Segment);        \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::OrientedSegment); \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::Line);           \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::OrientedLine);   \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::Ray);            \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::Halfplane);      \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::Triangle);       \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::Rectangle);      \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::Convex);         \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::MonotoneChain);  \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::Polyline);       \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::Polygon);        \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::PolygonWithHoles); \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::HalfplaneIntersection); \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::PolygonSet);     \
    PGL_PRED(cls, SelfT, samePointSet, ::pypgl::Disk)

// Bind the seven predicates of SelfT against every bound shape (all sixteen,
// including itself), so the full pair matrix is exposed. Every pgl shape
// declares all seven predicates against every other concrete shape (explicit
// overloads plus a rank-based forwarding template), so each pair compiles;
// pairs pgl has not implemented yet throw at runtime (or return a placeholder
// value — behavior is whatever pgl itself does). Overload resolution on the
// Python side dispatches by argument type.
#define PGL_BIND_ALL_PREDICATES(cls, SelfT)               \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::Point);          \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::Segment);        \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::OrientedSegment); \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::Line);           \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::OrientedLine);   \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::Ray);            \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::Halfplane);      \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::Triangle);       \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::Rectangle);      \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::Convex);         \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::MonotoneChain);  \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::Polyline);       \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::Polygon);        \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::PolygonWithHoles); \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::HalfplaneIntersection); \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::PolygonSet);     \
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::Disk)

// distanceL1/distanceLInf of SelfT against every *non-Disk* bound shape (all
// fifteen, including itself). Unlike squaredDistance, pgl does not (yet) give
// Disk a closed form against anything but Point (doc/todo.md: "L1 / LInf
// distance to and from Disk") -- so Disk is deliberately left out of this
// macro. The Point<->Disk pair is bound by hand in bind_point.cpp/
// bind_disk.cpp instead, the only L1/LInf pair Disk currently supports.
#define PGL_BIND_ALL_L1LINF_DISTANCE(cls, SelfT)                \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::Point);             \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::Segment);           \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::OrientedSegment);   \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::Line);              \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::OrientedLine);      \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::Ray);               \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::Halfplane);         \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::Triangle);          \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::Rectangle);         \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::Convex);            \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::MonotoneChain);     \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::Polyline);          \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::Polygon);           \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::PolygonWithHoles);  \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::HalfplaneIntersection); \
    PGL_PRED(cls, SelfT, distanceL1, ::pypgl::PolygonSet);        \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::Point);           \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::Segment);         \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::OrientedSegment); \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::Line);            \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::OrientedLine);    \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::Ray);             \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::Halfplane);       \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::Triangle);        \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::Rectangle);       \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::Convex);          \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::MonotoneChain);   \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::Polyline);        \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::Polygon);         \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::PolygonWithHoles); \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::HalfplaneIntersection); \
    PGL_PRED(cls, SelfT, distanceLInf, ::pypgl::PolygonSet)

// squaredHausdorffDistance / hausdorffDistanceL1 / hausdorffDistanceLInf of
// SelfT against the six shapes pgl currently implements it for: Point,
// Segment, OrientedSegment, Rectangle, Triangle, Convex -- all convex, so
// each one-sided (directed) Hausdorff distance between any two of them is
// attained at a vertex of the "from" shape. pgl returns the standard
// *symmetric* Hausdorff distance, max(h(A, B), h(B, A)) where h is the
// one-sided sup-inf distance -- so a.squaredHausdorffDistance(b) always
// equals b.squaredHausdorffDistance(a); there is no separate one-sided form
// bound (compute that yourself from vertices and squaredDistance/
// distanceL1/distanceLInf if needed). Disk (no closed form: would need a
// farthest-point-on-a-circle search) and Polygon (may be non-convex; would
// need a Voronoi-based approach) are excluded -- pgl does not define these
// methods for them at all. Only call this macro for SelfT in that same
// six-shape set.
#define PGL_BIND_ALL_HAUSDORFF_DISTANCE(cls, SelfT)                          \
    PGL_PRED(cls, SelfT, squaredHausdorffDistance, ::pypgl::Point);            \
    PGL_PRED(cls, SelfT, squaredHausdorffDistance, ::pypgl::Segment);          \
    PGL_PRED(cls, SelfT, squaredHausdorffDistance, ::pypgl::OrientedSegment);  \
    PGL_PRED(cls, SelfT, squaredHausdorffDistance, ::pypgl::Rectangle);        \
    PGL_PRED(cls, SelfT, squaredHausdorffDistance, ::pypgl::Triangle);         \
    PGL_PRED(cls, SelfT, squaredHausdorffDistance, ::pypgl::Convex);           \
    PGL_PRED(cls, SelfT, hausdorffDistanceL1, ::pypgl::Point);                \
    PGL_PRED(cls, SelfT, hausdorffDistanceL1, ::pypgl::Segment);              \
    PGL_PRED(cls, SelfT, hausdorffDistanceL1, ::pypgl::OrientedSegment);      \
    PGL_PRED(cls, SelfT, hausdorffDistanceL1, ::pypgl::Rectangle);            \
    PGL_PRED(cls, SelfT, hausdorffDistanceL1, ::pypgl::Triangle);             \
    PGL_PRED(cls, SelfT, hausdorffDistanceL1, ::pypgl::Convex);              \
    PGL_PRED(cls, SelfT, hausdorffDistanceLInf, ::pypgl::Point);              \
    PGL_PRED(cls, SelfT, hausdorffDistanceLInf, ::pypgl::Segment);            \
    PGL_PRED(cls, SelfT, hausdorffDistanceLInf, ::pypgl::OrientedSegment);    \
    PGL_PRED(cls, SelfT, hausdorffDistanceLInf, ::pypgl::Rectangle);          \
    PGL_PRED(cls, SelfT, hausdorffDistanceLInf, ::pypgl::Triangle);           \
    PGL_PRED(cls, SelfT, hausdorffDistanceLInf, ::pypgl::Convex)


// -----------------------------------------------------------------------------
// The general intersection (implementation/intersection.hpp)
//
// `a.intersection(b)` is the literal point set A n B, with no regularization:
// every piece is kept, whatever its dimension. What comes back therefore
// depends on the pair, and nanobind's optional/variant casters turn each form
// into the obvious Python one:
//
//   * a pair whose intersection is guaranteed connected returns
//     optional<variant<...>>  ->  the concrete shape, or None when disjoint;
//   * a pair that can come apart returns vector<variant<...>>  ->  a list of
//     concrete shapes (empty when disjoint), mixing dimensions freely: two
//     polygons can meet in a point, a Polyline and a Polygon all at once;
//   * two half-plane intersections (and the shapes that convert to one) return
//     a HalfplaneIntersection directly, since that class has an empty state and
//     needs no optional.
//
// Every shape but Disk takes part: pgl implements no clipping against a circle,
// so a Disk's only intersection is with a Point (both orders), bound by hand.
//
// The operand sets differ slightly by receiver, which is why there are four
// macros rather than one -- see each one's comment for what it leaves out.

#define PGL_ISECT(cls, SelfT, OtherT) PGL_PRED(cls, SelfT, intersection, OtherT)

// The fourteen operands every non-Disk receiver below accepts.
#define PGL_BIND_INTERSECTION_COMMON(cls, SelfT)            \
    PGL_ISECT(cls, SelfT, ::pypgl::Point);                  \
    PGL_ISECT(cls, SelfT, ::pypgl::Segment);                \
    PGL_ISECT(cls, SelfT, ::pypgl::OrientedSegment);        \
    PGL_ISECT(cls, SelfT, ::pypgl::Line);                   \
    PGL_ISECT(cls, SelfT, ::pypgl::OrientedLine);           \
    PGL_ISECT(cls, SelfT, ::pypgl::Ray);                    \
    PGL_ISECT(cls, SelfT, ::pypgl::Halfplane);              \
    PGL_ISECT(cls, SelfT, ::pypgl::Triangle);               \
    PGL_ISECT(cls, SelfT, ::pypgl::Rectangle);              \
    PGL_ISECT(cls, SelfT, ::pypgl::Convex);                 \
    PGL_ISECT(cls, SelfT, ::pypgl::MonotoneChain);          \
    PGL_ISECT(cls, SelfT, ::pypgl::Polyline);               \
    PGL_ISECT(cls, SelfT, ::pypgl::Polygon);                \
    PGL_ISECT(cls, SelfT, ::pypgl::PolygonWithHoles)

// The 0D/1D receivers -- Segment, OrientedSegment, Line, OrientedLine, Ray --
// and the four 2D ones that are convex or simple: everything but a PolygonSet,
// whose intersection is only defined against the shapes that can hold an
// arbitrary set of regions back (see PGL_BIND_INTERSECTION_SET).
#define PGL_BIND_INTERSECTION_LINEAR(cls, SelfT)            \
    PGL_BIND_INTERSECTION_COMMON(cls, SelfT);               \
    PGL_ISECT(cls, SelfT, ::pypgl::HalfplaneIntersection)

// The 2D receivers whose intersection with a set of regions is defined:
// Halfplane, Triangle, Rectangle, Convex, Polygon and PolygonWithHoles.
#define PGL_BIND_INTERSECTION_AREA(cls, SelfT)              \
    PGL_BIND_INTERSECTION_LINEAR(cls, SelfT);               \
    PGL_ISECT(cls, SelfT, ::pypgl::PolygonSet)

// A chain receiver (MonotoneChain, Polyline) takes the common fourteen and no
// more: pgl clips a chain against no half-plane intersection and against no
// set of regions.
#define PGL_BIND_INTERSECTION_CHAIN(cls, SelfT)             \
    PGL_BIND_INTERSECTION_COMMON(cls, SelfT)

// A HalfplaneIntersection receiver: the common fourteen minus the two chains
// (the pair pgl does not implement in either direction), plus itself and a set.
#define PGL_BIND_INTERSECTION_HALFPLANES(cls, SelfT)        \
    PGL_ISECT(cls, SelfT, ::pypgl::Point);                  \
    PGL_ISECT(cls, SelfT, ::pypgl::Segment);                \
    PGL_ISECT(cls, SelfT, ::pypgl::OrientedSegment);        \
    PGL_ISECT(cls, SelfT, ::pypgl::Line);                   \
    PGL_ISECT(cls, SelfT, ::pypgl::OrientedLine);           \
    PGL_ISECT(cls, SelfT, ::pypgl::Ray);                    \
    PGL_ISECT(cls, SelfT, ::pypgl::Halfplane);              \
    PGL_ISECT(cls, SelfT, ::pypgl::Triangle);               \
    PGL_ISECT(cls, SelfT, ::pypgl::Rectangle);              \
    PGL_ISECT(cls, SelfT, ::pypgl::Convex);                 \
    PGL_ISECT(cls, SelfT, ::pypgl::Polygon);                \
    PGL_ISECT(cls, SelfT, ::pypgl::PolygonWithHoles);       \
    PGL_ISECT(cls, SelfT, ::pypgl::HalfplaneIntersection);  \
    PGL_ISECT(cls, SelfT, ::pypgl::PolygonSet)

// A PolygonSet receiver: only the shapes with area, since the components a set
// is made of are regions. A lower-dimensional operand is not refused by
// omission alone -- write it on the left (`segment.intersection(a_set)` is not
// defined either), so a caller wanting it clips against the components.
#define PGL_BIND_INTERSECTION_SET(cls, SelfT)               \
    PGL_ISECT(cls, SelfT, ::pypgl::Halfplane);              \
    PGL_ISECT(cls, SelfT, ::pypgl::Triangle);               \
    PGL_ISECT(cls, SelfT, ::pypgl::Rectangle);              \
    PGL_ISECT(cls, SelfT, ::pypgl::Convex);                 \
    PGL_ISECT(cls, SelfT, ::pypgl::Polygon);                \
    PGL_ISECT(cls, SelfT, ::pypgl::PolygonWithHoles);       \
    PGL_ISECT(cls, SelfT, ::pypgl::HalfplaneIntersection);  \
    PGL_ISECT(cls, SelfT, ::pypgl::PolygonSet)

// -----------------------------------------------------------------------------
// Regularized boolean operations (implementation/booleans.hpp)
//
// The four operations that treat their operands as *solids* rather than as
// point sets:
//
//   a.regularizedIntersection(b)   closure(A° n B°)
//   a.regularizedUnion(b)          closure(A° u B°)
//   a.difference(b)                closure(A° \ B)
//   a.symmetricDifference(b)       closure((A° \ B) u (B° \ A))
//
// Every one of them is **regularized** -- the closure of the operation applied
// to the *interiors*. Lower-dimensional leftovers are dropped: a stretch of
// boundary the operands share without either covering it, an isolated contact
// point, and a slit, which has no area to begin with. It also means material
// with no area never *joins* anything, so two shapes meeting at a single point
// come back as one PolygonSet with two components. In particular
// `a.regularizedUnion(a)` is not `a` but `a.regularized()`: idempotence holds
// up to regularization and no further.
//
// All four return a PolygonSet (never a bare list, as they did before pgl had
// that shape), which is what makes them closed: a result feeds straight back
// in. Its components are not nested -- an island stranded inside a hole of the
// answer is a component of its own.
//
// The grids are not square, and mirror pgl's exactly. The six bounded region
// types are Triangle, Rectangle, Convex, Polygon, PolygonWithHoles and
// PolygonSet.
//
//   * regularizedUnion / symmetricDifference: every pair among the six.
//   * difference: any of the six as receiver, and as argument any of the six
//     plus Halfplane and HalfplaneIntersection -- A \ B stays bounded however
//     big B is. It is the one operation that is not symmetric, so which side a
//     shape is written on decides what is removed from what, and an unbounded
//     shape may only be the argument.
//   * regularizedIntersection: a PolygonWithHoles or a PolygonSet must take
//     part, since only those two can hold an answer with a hole or with several
//     pieces. So `rectangle.regularizedIntersection(triangle)` is the one gap
//     worth knowing -- it raises where the other three answer, and
//     `rect.asPolygonWithHoles().regularizedIntersection(tri)` reaches it. The
//     unregularized `intersection` above is defined for that pair as it stands.
//
// Every pair outside the grids is simply not bound, so it raises a Python
// TypeError -- the runtime equivalent of pgl's compile error. (pgl's own
// runtime Shape wrapper throws std::logic_error there instead, since it cannot
// know the pair until it runs.)

// One boolean operation of SelfT against the six bounded region types.
#define PGL_BIND_BOOLEAN(cls, SelfT, NAME)                  \
    PGL_PRED(cls, SelfT, NAME, ::pypgl::Triangle);          \
    PGL_PRED(cls, SelfT, NAME, ::pypgl::Rectangle);         \
    PGL_PRED(cls, SelfT, NAME, ::pypgl::Convex);            \
    PGL_PRED(cls, SelfT, NAME, ::pypgl::Polygon);           \
    PGL_PRED(cls, SelfT, NAME, ::pypgl::PolygonWithHoles);  \
    PGL_PRED(cls, SelfT, NAME, ::pypgl::PolygonSet)

// The three operations every one of the six bounded region types has, whatever
// it is: the two symmetric ones over the six, and the difference, which also
// takes the two unbounded convex shapes as its argument.
#define PGL_BIND_BOOLEANS(cls, SelfT)                       \
    PGL_BIND_BOOLEAN(cls, SelfT, regularizedUnion);         \
    PGL_BIND_BOOLEAN(cls, SelfT, symmetricDifference);      \
    PGL_BIND_BOOLEAN(cls, SelfT, difference);               \
    PGL_PRED(cls, SelfT, difference, ::pypgl::Halfplane);   \
    PGL_PRED(cls, SelfT, difference, ::pypgl::HalfplaneIntersection)

// The regularized intersection for a receiver that can hold the answer: a
// PolygonWithHoles or a PolygonSet. Same argument grid as `difference`.
#define PGL_BIND_REGULARIZED_INTERSECTION(cls, SelfT)                        \
    PGL_BIND_BOOLEAN(cls, SelfT, regularizedIntersection);                   \
    PGL_PRED(cls, SelfT, regularizedIntersection, ::pypgl::Halfplane);       \
    PGL_PRED(cls, SelfT, regularizedIntersection, ::pypgl::HalfplaneIntersection)

// The other half of the regularized intersection, for the receivers that
// cannot hold the answer themselves (Halfplane, Triangle, Rectangle, Convex,
// Polygon, HalfplaneIntersection): the operation is available exactly when the
// *other* operand is one of the two shapes that can.
#define PGL_BIND_REGULARIZED_INTERSECTION_WITH_SET(cls, SelfT)                \
    PGL_PRED(cls, SelfT, regularizedIntersection, ::pypgl::PolygonWithHoles); \
    PGL_PRED(cls, SelfT, regularizedIntersection, ::pypgl::PolygonSet)

// -----------------------------------------------------------------------------
// Minkowski sum (implementation/minkowskisum.hpp)
//
// A (+) B = {a + b : a in A, b in B}, written `a.minkowskiSum(b)` or `a + b`.
//
// pgl gives every summable pair the tightest type that can hold its answer, and
// pypgl mirrors that exactly rather than flattening everything to one return
// type:
//
//   * a Point summand is a translation and gives back the other operand's own
//     type, for every shape there is;
//   * two bounded convex polygonal shapes give a Convex -- a Rectangle when
//     both are rectangles, the one pair closed under the sum. Every vertex of
//     such a result is a sum of two input vertices, so it stays exact;
//   * a MonotoneChain with a non-degenerate bounded convex shape gives a
//     Polygon: dragging a convex body along an x-monotone chain sweeps a region
//     that cannot enclose a hole;
//   * a sum involving an unbounded convex operand (Line, OrientedLine, Ray,
//     HalfplaneIntersection) is again an intersection of half-planes, so it
//     gives a HalfplaneIntersection. A Halfplane absorbs every bounded operand
//     and comes back a Halfplane -- just pushed out;
//   * a bounded sum with a non-convex operand generally needs a
//     PolygonWithHoles: sliding a shape around the inside of a C sweeps
//     material that closes over a hole neither operand has. When the answer is
//     not guaranteed connected -- a chain summed with a chain, or anything
//     summed with a PolygonSet -- it is a PolygonSet;
//   * two disks sum to a Disk (the one curved sum in the library) and a Disk
//     with a Halfplane to a Halfplane. Both are bound by hand rather than
//     through these macros: pgl's default result type there is `double`, which
//     pypgl does not instantiate, so they request ERational explicitly and
//     raise for a disk whose radius is irrational (see bind_disk.cpp).
//
// The remaining pairs -- a Disk with anything else, an unbounded operand with a
// non-convex one -- are deliberately not bound, so they raise a Python
// TypeError. Since hull(A (+) B) = hull(A) (+) hull(B), a caller who wants the
// convex approximation can ask for it by summing the hulls.

// `a + b` for one summable pair.
#define PGL_ADD(cls, SelfT, OtherT)                                                       \
    cls.def("__add__", [](const SelfT &a, const OtherT &b) { return a.minkowskiSum(b); }, \
            nb::is_operator())

// Both spellings of one summable pair.
#define PGL_MINK(cls, SelfT, OtherT)                       \
    PGL_PRED(cls, SelfT, minkowskiSum, OtherT);            \
    PGL_ADD(cls, SelfT, OtherT)

// A bounded convex polygonal receiver -- Point, Segment, OrientedSegment,
// Triangle, Rectangle, Convex -- which sums with every shape but a Disk. (A
// Point additionally sums with one, since that sum is its translation; a
// Halfplane also takes every one of these operands and adds the Disk itself.)
// The Point *operand* gets only the named spelling here: `shape + point` is
// bound by each shape itself, through PGL_BIND_OPERATORS for the immutable ones
// and its own __add__ for the mutable ones.
#define PGL_BIND_MINKOWSKI_CONVEX(cls, SelfT)              \
    PGL_PRED(cls, SelfT, minkowskiSum, ::pypgl::Point);    \
    PGL_MINK(cls, SelfT, ::pypgl::Segment);                \
    PGL_MINK(cls, SelfT, ::pypgl::OrientedSegment);        \
    PGL_MINK(cls, SelfT, ::pypgl::Line);                   \
    PGL_MINK(cls, SelfT, ::pypgl::OrientedLine);           \
    PGL_MINK(cls, SelfT, ::pypgl::Ray);                    \
    PGL_MINK(cls, SelfT, ::pypgl::Halfplane);              \
    PGL_MINK(cls, SelfT, ::pypgl::Triangle);               \
    PGL_MINK(cls, SelfT, ::pypgl::Rectangle);              \
    PGL_MINK(cls, SelfT, ::pypgl::Convex);                 \
    PGL_MINK(cls, SelfT, ::pypgl::MonotoneChain);          \
    PGL_MINK(cls, SelfT, ::pypgl::Polyline);               \
    PGL_MINK(cls, SelfT, ::pypgl::Polygon);                \
    PGL_MINK(cls, SelfT, ::pypgl::PolygonWithHoles);       \
    PGL_MINK(cls, SelfT, ::pypgl::HalfplaneIntersection);  \
    PGL_MINK(cls, SelfT, ::pypgl::PolygonSet)

// An unbounded convex receiver -- Line, OrientedLine, Ray,
// HalfplaneIntersection. Every sum is again an intersection of half-planes, so
// only convex operands are accepted: a non-convex one would need an unbounded
// region, which no pgl shape represents.
#define PGL_BIND_MINKOWSKI_UNBOUNDED(cls, SelfT)           \
    PGL_PRED(cls, SelfT, minkowskiSum, ::pypgl::Point);    \
    PGL_MINK(cls, SelfT, ::pypgl::Segment);                \
    PGL_MINK(cls, SelfT, ::pypgl::OrientedSegment);        \
    PGL_MINK(cls, SelfT, ::pypgl::Line);                   \
    PGL_MINK(cls, SelfT, ::pypgl::OrientedLine);           \
    PGL_MINK(cls, SelfT, ::pypgl::Ray);                    \
    PGL_MINK(cls, SelfT, ::pypgl::Halfplane);              \
    PGL_MINK(cls, SelfT, ::pypgl::Triangle);               \
    PGL_MINK(cls, SelfT, ::pypgl::Rectangle);              \
    PGL_MINK(cls, SelfT, ::pypgl::Convex);                 \
    PGL_MINK(cls, SelfT, ::pypgl::HalfplaneIntersection)

// A bounded receiver that is not convex, or not a single region: MonotoneChain,
// Polyline, Polygon, PolygonWithHoles, PolygonSet. It sums with every bounded
// operand (a Halfplane too, which simply absorbs it), and with no unbounded
// convex one: pgl asks for a convex operand there, which these are not.
#define PGL_BIND_MINKOWSKI_REGION(cls, SelfT)              \
    PGL_PRED(cls, SelfT, minkowskiSum, ::pypgl::Point);    \
    PGL_MINK(cls, SelfT, ::pypgl::Segment);                \
    PGL_MINK(cls, SelfT, ::pypgl::OrientedSegment);        \
    PGL_MINK(cls, SelfT, ::pypgl::Halfplane);              \
    PGL_MINK(cls, SelfT, ::pypgl::Triangle);               \
    PGL_MINK(cls, SelfT, ::pypgl::Rectangle);              \
    PGL_MINK(cls, SelfT, ::pypgl::Convex);                 \
    PGL_MINK(cls, SelfT, ::pypgl::MonotoneChain);          \
    PGL_MINK(cls, SelfT, ::pypgl::Polyline);               \
    PGL_MINK(cls, SelfT, ::pypgl::Polygon);                \
    PGL_MINK(cls, SelfT, ::pypgl::PolygonWithHoles);       \
    PGL_MINK(cls, SelfT, ::pypgl::PolygonSet)

// The named `minkowskiSum` for a receiver whose only *macro-bound* pair is the
// translation by a Point: the Disk, whose two other sums (with a Disk and with
// a Halfplane) each need an explicit result type and are bound by hand.
// `disk + point` already works through PGL_BIND_OPERATORS; this keeps the
// method spelling available too, so `a.minkowskiSum(point)` does not depend on
// which shape `a` is.
#define PGL_BIND_TRANSLATION_MINKOWSKI(cls, SelfT)         \
    PGL_PRED(cls, SelfT, minkowskiSum, ::pypgl::Point)

// -----------------------------------------------------------------------------
// Minkowski erosions (implementation/minkowskierosion.hpp)
//
// A (-) B = {x : x (+) B is inside A} = the intersection of all A - b, the
// morphological dual of the sum above. Written `a.minkowskiErosion(b)`; there is
// no operator spelling, since pgl gives it none and `-` already means
// translation by a point on every shape that takes one.
//
// It is defined for exactly the pairs the sum is, so the four operand lists
// below are the four above verbatim, and a receiver simply calls the erosion
// macro next to its sum macro. What differs is the answer:
//
//   * a Point operand is again a translation, so every shape erodes by one and
//     gets its own type back -- the one case that is the sum's mirror image;
//   * erosion is *not* commutative, and the two operands are read quite
//     differently: a convex receiver needs nothing but its own half-planes and
//     the operand's support function, so it answers a HalfplaneIntersection --
//     for a *bounded* receiver too, where the sum would have given a Convex.
//     The operand need not be convex there, since a support function only sees
//     its hull. Two rectangles are the one pair closed under the erosion, as
//     they are under the sum;
//   * a Halfplane receiver comes back a Halfplane, pulled in rather than pushed
//     out, for every bounded operand; an unbounded operand makes it a
//     HalfplaneIntersection (usually the empty one);
//   * a bounded non-convex receiver answers a PolygonSet and never a single
//     PolygonWithHoles, which is the one structural difference from the sum:
//     an erosion disconnects. A dumbbell eroded by anything wider than its
//     handle is two regions, for operands that are in no way degenerate;
//   * a bounded receiver eroded by an unbounded operand is empty, and comes
//     back as the empty shape of whichever type the row above gives;
//   * the Disk pairs are bound by hand for the same reason the sums are (pgl
//     defaults them to `double`): Disk (-) Disk is a Disk or None -- None when
//     the eroding disk is the larger, where the sum always answers -- and
//     Disk (-) Halfplane is empty, which pgl models with a shape pypgl does not
//     bind, so it answers None (see bind_disk.cpp).
//
// pgl raises for an operand that covers no point, whose erosion is the whole
// plane and not a set of bounded regions.

// The named `minkowskiErosion` for one pair. There is no operator counterpart
// to PGL_MINK here on purpose.
#define PGL_EROSION(cls, SelfT, OtherT)                        \
    PGL_PRED(cls, SelfT, minkowskiErosion, OtherT)

// A bounded convex polygonal receiver -- Point, Segment, OrientedSegment,
// Triangle, Rectangle, Convex -- eroded by every shape but a Disk, matching
// PGL_BIND_MINKOWSKI_CONVEX operand for operand. (A Point additionally erodes
// by a Disk, and a Halfplane takes this list plus the Disk itself.)
#define PGL_BIND_EROSION_CONVEX(cls, SelfT)                    \
    PGL_EROSION(cls, SelfT, ::pypgl::Point);                   \
    PGL_EROSION(cls, SelfT, ::pypgl::Segment);                 \
    PGL_EROSION(cls, SelfT, ::pypgl::OrientedSegment);         \
    PGL_EROSION(cls, SelfT, ::pypgl::Line);                    \
    PGL_EROSION(cls, SelfT, ::pypgl::OrientedLine);            \
    PGL_EROSION(cls, SelfT, ::pypgl::Ray);                     \
    PGL_EROSION(cls, SelfT, ::pypgl::Halfplane);               \
    PGL_EROSION(cls, SelfT, ::pypgl::Triangle);                \
    PGL_EROSION(cls, SelfT, ::pypgl::Rectangle);               \
    PGL_EROSION(cls, SelfT, ::pypgl::Convex);                  \
    PGL_EROSION(cls, SelfT, ::pypgl::MonotoneChain);           \
    PGL_EROSION(cls, SelfT, ::pypgl::Polyline);                \
    PGL_EROSION(cls, SelfT, ::pypgl::Polygon);                 \
    PGL_EROSION(cls, SelfT, ::pypgl::PolygonWithHoles);        \
    PGL_EROSION(cls, SelfT, ::pypgl::HalfplaneIntersection);   \
    PGL_EROSION(cls, SelfT, ::pypgl::PolygonSet)

// An unbounded convex receiver -- Line, OrientedLine, Ray,
// HalfplaneIntersection -- which takes only convex operands, exactly as
// PGL_BIND_MINKOWSKI_UNBOUNDED does.
#define PGL_BIND_EROSION_UNBOUNDED(cls, SelfT)                 \
    PGL_EROSION(cls, SelfT, ::pypgl::Point);                   \
    PGL_EROSION(cls, SelfT, ::pypgl::Segment);                 \
    PGL_EROSION(cls, SelfT, ::pypgl::OrientedSegment);         \
    PGL_EROSION(cls, SelfT, ::pypgl::Line);                    \
    PGL_EROSION(cls, SelfT, ::pypgl::OrientedLine);            \
    PGL_EROSION(cls, SelfT, ::pypgl::Ray);                     \
    PGL_EROSION(cls, SelfT, ::pypgl::Halfplane);               \
    PGL_EROSION(cls, SelfT, ::pypgl::Triangle);                \
    PGL_EROSION(cls, SelfT, ::pypgl::Rectangle);               \
    PGL_EROSION(cls, SelfT, ::pypgl::Convex);                  \
    PGL_EROSION(cls, SelfT, ::pypgl::HalfplaneIntersection)

// A bounded receiver that is not convex, or not a single region: MonotoneChain,
// Polyline, Polygon, PolygonWithHoles, PolygonSet. Same operands as
// PGL_BIND_MINKOWSKI_REGION; every answer but the Point translation and the
// Halfplane is a PolygonSet.
#define PGL_BIND_EROSION_REGION(cls, SelfT)                    \
    PGL_EROSION(cls, SelfT, ::pypgl::Point);                   \
    PGL_EROSION(cls, SelfT, ::pypgl::Segment);                 \
    PGL_EROSION(cls, SelfT, ::pypgl::OrientedSegment);         \
    PGL_EROSION(cls, SelfT, ::pypgl::Halfplane);               \
    PGL_EROSION(cls, SelfT, ::pypgl::Triangle);                \
    PGL_EROSION(cls, SelfT, ::pypgl::Rectangle);               \
    PGL_EROSION(cls, SelfT, ::pypgl::Convex);                  \
    PGL_EROSION(cls, SelfT, ::pypgl::MonotoneChain);           \
    PGL_EROSION(cls, SelfT, ::pypgl::Polyline);                \
    PGL_EROSION(cls, SelfT, ::pypgl::Polygon);                 \
    PGL_EROSION(cls, SelfT, ::pypgl::PolygonWithHoles);        \
    PGL_EROSION(cls, SelfT, ::pypgl::PolygonSet)

// The Disk's one macro-bound erosion, its translation by a Point. Its other two
// (by a Disk and by a Halfplane) need an explicit result type and are bound by
// hand, exactly as its sums are.
#define PGL_BIND_TRANSLATION_EROSION(cls, SelfT)               \
    PGL_EROSION(cls, SelfT, ::pypgl::Point)

// -----------------------------------------------------------------------------
// A triangulation's domain predicates (algorithm/triangulation.hpp)
//
// The four predicates a Triangulation answers about the region it covers -- the
// polygon for the polygon constructors, the convex hull otherwise. They give
// exactly what the shape predicates of the same name give for that region as a
// Polygon, but decided on the mesh, so the cost follows the triangles the query
// shape meets rather than the size of the boundary. Every shape is a valid
// query: an unbounded one is never contained in the bounded domain, and the
// four are `contains` / `interiorContains` / `intersects` / `interiorsIntersect`
// only -- pgl gives a triangulation no boundaryContains / separates / crosses,
// so this is a smaller family than PGL_BIND_ALL_PREDICATES.
#define PGL_DOMAIN_PREDICATES(cls, SelfT, OtherT)      \
    PGL_PRED(cls, SelfT, contains, OtherT);            \
    PGL_PRED(cls, SelfT, interiorContains, OtherT);    \
    PGL_PRED(cls, SelfT, intersects, OtherT);          \
    PGL_PRED(cls, SelfT, interiorsIntersect, OtherT)

#define PGL_BIND_ALL_DOMAIN_PREDICATES(cls, SelfT)                   \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::Point);               \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::Segment);             \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::OrientedSegment);     \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::Line);                \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::OrientedLine);        \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::Ray);                 \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::Halfplane);           \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::Triangle);            \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::Rectangle);           \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::Convex);              \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::MonotoneChain);       \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::Polyline);            \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::Polygon);             \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::PolygonWithHoles);    \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::HalfplaneIntersection); \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::PolygonSet);          \
    PGL_DOMAIN_PREDICATES(cls, SelfT, ::pypgl::Disk)
