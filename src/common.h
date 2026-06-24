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
using Disk = pgl::EDisk;                            // pgl::Disk<EPoint>

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

// Bind the exact squared distance self.squaredDistance(other) for one OtherT.
// ResultNumber defaults to the number type (ERational), so the result is the
// exact squared Euclidean distance as a Fraction — never an approximation.
#define PGL_SQDIST(cls, SelfT, OtherT)                                       \
    cls.def("squaredDistance",                                              \
            [](const SelfT &self, const OtherT &other) {                    \
                return self.squaredDistance(other);                         \
            },                                                              \
            nb::arg("other"))

// squaredDistance of SelfT against every bound shape. Like the predicate
// matrix, pgl makes every pair available (explicit overload on the higher-rank
// shape plus rank-based forwarding). The single exception is Convex×Halfplane,
// which pgl does not implement in either direction, so Convex and Halfplane bind
// their squared-distance lists explicitly (omitting each other) instead of using
// this macro.
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
    PGL_SQDIST(cls, SelfT, ::pypgl::Convex)

// Bind the seven predicates of SelfT against every bound shape, so the full
// pair matrix is exposed. Every pgl shape declares all seven predicates against
// every other concrete shape (explicit overloads plus a rank-based forwarding
// template), so each pair compiles; pairs pgl has not implemented yet throw at
// runtime. Overload resolution on the Python side dispatches by argument type.
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
    PGL_BIND_PREDICATES(cls, SelfT, ::pypgl::Convex)
