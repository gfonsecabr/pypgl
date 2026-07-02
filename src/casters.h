#pragma once

// Hand-written plumbing in the binding: nanobind type casters that move values
// across the C++/Python boundary where a mechanical `.def(...)` isn't enough.
//
//   pgl::BigInt          <-> Python int
//   pgl::ERational        <-> fractions.Fraction   (also accepts int and "a/b" str)
//   pgl::Shape<EPoint>   <-> a concrete pypgl shape object   (ShapeTree only)
//
// Everything else in pypgl is mechanical `.def(...)`. All three casters live
// here so every translation unit shares one definition.

#include <nanobind/nanobind.h>

#include <sstream>
#include <string>

#include "pgl.hpp"

namespace nb = nanobind;

namespace nanobind::detail {

// --- pgl::BigInt <-> Python int ---------------------------------------------
//
// Small magnitudes take a machine-integer fast path; anything that overflows a
// 64-bit value round-trips through a decimal string, which pgl::BigInt already
// reads/writes via operator>>/operator<<. The string route is lossless and needs
// no library change.
template <>
struct type_caster<pgl::BigInt> {
    NB_TYPE_CASTER(pgl::BigInt, const_name("int"))

    bool from_python(handle src, uint8_t, cleanup_list *) noexcept {
        PyObject *o = src.ptr();
        if (!PyLong_Check(o))
            return false;

        int overflow = 0;
        long long fast = PyLong_AsLongLongAndOverflow(o, &overflow);
        if (fast == -1 && PyErr_Occurred()) {
            PyErr_Clear();
            return false;
        }
        if (overflow == 0) {
            value = pgl::BigInt(static_cast<std::int64_t>(fast));
            return true;
        }

        // Slow path: |value| exceeds int64 -> parse its decimal string.
        PyObject *str = PyObject_Str(o);
        if (!str) {
            PyErr_Clear();
            return false;
        }
        const char *text = PyUnicode_AsUTF8(str);
        if (!text) {
            Py_DECREF(str);
            PyErr_Clear();
            return false;
        }
        std::istringstream in(text);
        pgl::BigInt parsed;
        in >> parsed;
        Py_DECREF(str);
        if (in.fail())
            return false;
        value = parsed;
        return true;
    }

    static handle from_cpp(const pgl::BigInt &b, rv_policy, cleanup_list *) noexcept {
        std::ostringstream out;
        out << b;
        const std::string text = out.str();
        return PyLong_FromString(text.c_str(), nullptr, 10);
    }
};

// --- pgl::ERational <-> fractions.Fraction ----------------------------------
//
// Accepts Fraction, int, and "a/b"/"a" strings. Rejects float loudly: a float
// cannot represent an exact rational, so forcing the user to be explicit
// preserves the exactness contract. Each term flows through the BigInt caster,
// so arbitrarily large coordinates round-trip.
template <>
struct type_caster<pgl::ERational> {
    NB_TYPE_CASTER(pgl::ERational, const_name("fractions.Fraction"))

    bool from_python(handle src, uint8_t flags, cleanup_list *cl) noexcept {
        PyObject *o = src.ptr();

        // A float can only approximate; reject so overload resolution fails
        // loudly and points the user at int / Fraction / "a/b".
        if (PyFloat_Check(o))
            return false;

        // Keep any temporary built below alive until the terms are extracted.
        object owner;
        PyObject *target = o;

        if (PyUnicode_Check(o)) {
            // Parse "a/b", "a", "-3/4", and decimal strings exactly via Fraction.
            // (pgl's BigInt operator>> reads a whole token, so it cannot drive the
            // Rational "a/b" parse directly.)
            object fraction = module_::import_("fractions").attr("Fraction");
            try {
                owner = fraction(borrow(o));
            } catch (...) {
                PyErr_Clear();
                return false;
            }
            target = owner.ptr();
        }

        // int, Fraction, or any object exposing integer numerator/denominator.
        object num = steal(PyObject_GetAttrString(target, "numerator"));
        object den = steal(PyObject_GetAttrString(target, "denominator"));
        if (!num.is_valid() || !den.is_valid()) {
            PyErr_Clear();
            return false;
        }
        type_caster<pgl::BigInt> num_caster, den_caster;
        if (!num_caster.from_python(num, flags, cl) ||
            !den_caster.from_python(den, flags, cl))
            return false;
        value = pgl::ERational(num_caster.value, den_caster.value);
        return true;
    }

    static handle from_cpp(const pgl::ERational &r, rv_policy pol, cleanup_list *cl) noexcept {
        object num = steal(type_caster<pgl::BigInt>::from_cpp(r.numerator(), pol, cl));
        object den = steal(type_caster<pgl::BigInt>::from_cpp(r.denominator(), pol, cl));
        if (!num.is_valid() || !den.is_valid())
            return handle();
        object fraction = module_::import_("fractions").attr("Fraction");
        try {
            return fraction(num, den).release();
        } catch (...) {
            return handle();
        }
    }
};

// --- pgl::Shape<EPoint> <-> a concrete pypgl shape object -------------------
//
// ShapeTree (bind_shapetree.cpp) is the one place pypgl breaks its own "bind
// concrete shapes, not the Shape variant wrapper" rule (see CLAUDE.md): a
// spatial index that holds a mix of shape types needs a type-erased element,
// and pgl::Shape<PointType> is exactly that. This caster type-erases on the
// way in and re-wraps on the way out, so Python code never sees pgl::Shape
// itself -- only whichever of the twelve concrete classes was actually stored
// or passed as a query.
//
// Py->C++: probes each of the twelve bound classes in turn with an exact,
// non-converting try_cast; the first match wins. try_cast checks the actual
// Python type rather than attempting any implicit conversion, so unlike the
// Triangulation Polygon/point-list overload-order pitfall (see
// bind_triangulation.cpp), there is no ambiguity for the probing order to get
// wrong.
//
// C++->Py: dispatches on the stored alternative and hands it to nb::cast,
// which reaches that alternative's own already-registered class caster
// regardless of which translation unit registered it (nanobind's class
// casters are looked up through a global type table, not per-TU). The leading
// EmptyShape alternative -- the state of a default-constructed Shape -- is
// never produced by this caster's from_python, and every path that could
// otherwise yield one (e.g. ShapeTree::nearestNeighbor on an empty tree) is
// guarded in bind_shapetree.cpp before reaching here, so it is treated as a
// cast failure rather than silently returned as something meaningless.
template <>
struct type_caster<pgl::Shape<pgl::EPoint>> {
    using Shape = pgl::Shape<pgl::EPoint>;
    NB_TYPE_CASTER(Shape,
                    const_name("Point | Segment | OrientedSegment | Line | OrientedLine | "
                                "Ray | Halfplane | Triangle | Rectangle | Convex | Polygon | Disk"))

    template <class T>
    bool try_alternative(handle src) noexcept {
        T v{};
        if (!nb::try_cast<T>(src, v, /*convert=*/false))
            return false;
        value = Shape(std::move(v));
        return true;
    }

    bool from_python(handle src, uint8_t, cleanup_list *) noexcept {
        return try_alternative<pgl::EPoint>(src) ||
               try_alternative<pgl::ESegment>(src) ||
               try_alternative<pgl::EOrientedSegment>(src) ||
               try_alternative<pgl::ELine>(src) ||
               try_alternative<pgl::EOrientedLine>(src) ||
               try_alternative<pgl::ERay>(src) ||
               try_alternative<pgl::EHalfplane>(src) ||
               try_alternative<pgl::ETriangle>(src) ||
               try_alternative<pgl::ERectangle>(src) ||
               try_alternative<pgl::EConvex>(src) ||
               try_alternative<pgl::EPolygon>(src) ||
               try_alternative<pgl::EDisk>(src);
    }

    static handle from_cpp(const Shape &s, rv_policy pol, cleanup_list *) noexcept {
        return std::visit(
            [pol](const auto &alt) -> handle {
                using T = std::decay_t<decltype(alt)>;
                if constexpr (std::is_same_v<T, pgl::EmptyShape<pgl::EPoint>>) {
                    return handle();
                } else {
                    try {
                        return nb::cast(alt, pol).release();
                    } catch (...) {
                        return handle();
                    }
                }
            },
            s.variant());
    }
};

}  // namespace nanobind::detail
