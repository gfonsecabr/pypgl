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

// repr, ordering, equality, and hashing — uniform across all value-type shapes.
template <class T, class Class>
void bind_value_semantics(Class &cls) {
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
    cls.def("__hash__", [](const T &self) { return std::hash<T>{}(self); });
}

}  // namespace pypgl

// Bind one predicate overload (self.NAME(other)) for a given other-shape type.
#define PGL_PRED(cls, SelfT, NAME, OtherT)                                  \
    cls.def(#NAME,                                                          \
            [](const SelfT &self, const OtherT &other) {                    \
                return self.NAME(other);                                    \
            },                                                              \
            nb::arg("other"))

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
