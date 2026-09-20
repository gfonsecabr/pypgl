#include "common.h"

using namespace pypgl;

// Support for the frozen shapes built in pypgl/__init__.py.
//
// Seven bound shapes are mutable -- Convex, MonotoneChain, Polyline, Polygon,
// PolygonWithHoles, PolygonSet and HalfplaneIntersection -- so none of them
// binds __hash__: a key that can change value underneath a dict is worse than
// no key at all. The Python layer answers that with a frozen subclass of each,
// which refuses every mutator and is hashable.
//
// What the subclass needs from C++ is the value hash itself. pgl defines
// std::hash for all seven (core/hash.hpp), consistent with its own operator==,
// which is the part that matters: a Polyline equals its own reverse, and a
// PolygonWithHoles stores its holes in canonical order, so two objects that
// compare equal hash equal however they were built. Computing that in Python
// from the vertices would mean re-deriving each shape's canonical form, and
// getting one of them wrong would silently break dict lookups.
//
// It is bound as a module-level private function rather than as a method, so
// the mutable classes' own API is unchanged: a method named `valueHash` on a
// shape that has no __hash__ would only invite the confusion this avoids.

namespace {

template <class T>
std::size_t valueHash(const T &shape) {
    return std::hash<T>{}(shape);
}

}  // namespace

void bind_frozen(nb::module_ &m) {
    const char *doc =
        "The value hash of a mutable shape, from pgl's std::hash. Private: it backs "
        "__hash__ on the Frozen* classes in pypgl/__init__.py, which are the supported "
        "way to use these shapes as dict keys.";
    m.def("_valueHash", &valueHash<Convex>, nb::arg("shape"), doc);
    m.def("_valueHash", &valueHash<MonotoneChain>, nb::arg("shape"), doc);
    m.def("_valueHash", &valueHash<Polyline>, nb::arg("shape"), doc);
    m.def("_valueHash", &valueHash<Polygon>, nb::arg("shape"), doc);
    m.def("_valueHash", &valueHash<PolygonWithHoles>, nb::arg("shape"), doc);
    m.def("_valueHash", &valueHash<PolygonSet>, nb::arg("shape"), doc);
    m.def("_valueHash", &valueHash<HalfplaneIntersection>, nb::arg("shape"), doc);
}
