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
using Num = pgl::ERational;
using Point = pgl::EPoint;            // pgl::Point<ERational>
using Segment = pgl::Segment<Point>;  // pgl::Segment<Point<ERational>>

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
