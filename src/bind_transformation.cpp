#include "common.h"

using namespace pypgl;

// Transformation: an affine map of the plane, stored as a 2x3 matrix mapping
// (x, y) to (a*x + b*y + tx, c*x + d*y + ty) (core/transformation.hpp). Unlike
// every shape, it is templated only on the matrix-entry type -- there is no
// separate point/label parameter -- so it is bound over the module's single
// numeric instantiation directly (::pypgl::Transformation = Transformation<Num>
// in common.h), with no per-shape variation.
//
// `t * shape` applies t to shape (transformation on the left, matching pgl's
// own operator*), bound as one Transformation.__mul__ overload per supported
// shape type. pgl defines this for every shape except Rectangle and Disk -- a
// general affine map turns a rectangle into a parallelogram and a disk into
// an ellipse, and neither class can represent that -- so those two simply
// have no overload here; applying a Transformation to one raises a Python
// TypeError, the runtime equivalent of pgl's compile error. `t1 * t2`
// composes two transformations (t2 applied first), also bound as __mul__, so
// `t1 * t2 * shape` both composes and applies left to right exactly as in
// C++.
//
// rotation(radians) (an arbitrary-angle rotation) is intentionally not bound:
// it is only defined for a floating-point ResultNumber and would return a
// Transformation<double> -- a second numeric instantiation pypgl does not
// carry (see "Load-bearing design decisions" in CLAUDE.md) -- mirroring why
// Disk.fbox() is skipped for the same reason. rotation90 (exact, since its
// entries are always 0/1/-1) is bound normally.
//
// No repr/equality machinery is shared with bind_value_semantics<T> here:
// pgl's Transformation has no operator<< and no operator< (only operator==),
// so __repr__ and __eq__/__ne__ are written by hand instead.

void bind_transformation(nb::module_ &m) {
    nb::class_<Transformation> cls(m, "Transformation");

    cls.def(nb::init<>(), "Create the identity transformation.");
    cls.def(nb::init<Num, Num, Num, Num, Num, Num>(),
            nb::arg("a"), nb::arg("b"), nb::arg("c"), nb::arg("d"),
            nb::arg("tx") = Num(0), nb::arg("ty") = Num(0),
            "Create a transformation from its matrix entries: "
            "(x, y) -> (a*x + b*y + tx, c*x + d*y + ty).");

    cls.def_static("identity", []() { return Transformation::identity(); },
                   "The identity transformation.");
    cls.def_static("translation", [](const Num &dx, const Num &dy) { return Transformation::translation(dx, dy); },
                   nb::arg("dx"), nb::arg("dy"), "Translation by (dx, dy).");
    cls.def_static("scaling", [](const Num &sx, const Num &sy) { return Transformation::scaling(sx, sy); },
                   nb::arg("sx"), nb::arg("sy"), "Non-uniform scaling around the origin.");
    cls.def_static("scaling", [](const Num &s) { return Transformation::scaling(s); },
                   nb::arg("s"), "Uniform scaling around the origin.");
    cls.def_static("rotation90", [](int k) { return Transformation::rotation90(k); }, nb::arg("k") = 1,
                   "Exact rotation around the origin by 90*k degrees (matrix entries "
                   "are always 0, 1, or -1).");
    cls.def_static("shearX", [](const Num &k) { return Transformation::shearX(k); }, nb::arg("k"),
                   "Horizontal shear: (x, y) -> (x + k*y, y).");
    cls.def_static("shearY", [](const Num &k) { return Transformation::shearY(k); }, nb::arg("k"),
                   "Vertical shear: (x, y) -> (x, y + k*x).");
    cls.def_static("reflectionX", []() { return Transformation::reflectionX(); },
                   "Reflection across the x-axis.");
    cls.def_static("reflectionY", []() { return Transformation::reflectionY(); },
                   "Reflection across the y-axis.");

    cls.def("a", [](const Transformation &t) { return t.a(); }, "Row 0, column 0 of the linear part.");
    cls.def("b", [](const Transformation &t) { return t.b(); }, "Row 0, column 1 of the linear part.");
    cls.def("c", [](const Transformation &t) { return t.c(); }, "Row 1, column 0 of the linear part.");
    cls.def("d", [](const Transformation &t) { return t.d(); }, "Row 1, column 1 of the linear part.");
    cls.def("tx", [](const Transformation &t) { return t.tx(); }, "Translation added to the first coordinate.");
    cls.def("ty", [](const Transformation &t) { return t.ty(); }, "Translation added to the second coordinate.");

    cls.def("determinant", [](const Transformation &t) { return t.determinant(); },
            "Determinant of the linear part: negative when orientation is "
            "reversed, zero when the plane collapses onto a line or point.");
    cls.def("isInvertible", [](const Transformation &t) { return t.isInvertible(); },
            "Whether determinant() is nonzero.");
    cls.def("inverse",
            [](const Transformation &t) {
                // pgl's own reciprocal()/inverse() guard a zero determinant
                // with only an assert(), which no-ops in a release build (the
                // one pypgl ships) and silently produces a corrupted internal
                // Rational instead of throwing -- checked explicitly here so
                // a singular transformation always raises cleanly instead of
                // crashing the process.
                if (!t.isInvertible())
                    throw std::invalid_argument(
                        "Transformation.inverse() requires a nonzero determinant "
                        "(this transformation is not invertible)");
                return t.inverse();
            },
            "The inverse transformation (divides by determinant(); raises "
            "ValueError if the transformation is not invertible).");

    cls.def("__eq__", [](const Transformation &a, const Transformation &b) { return a == b; }, nb::is_operator());
    cls.def("__ne__", [](const Transformation &a, const Transformation &b) { return !(a == b); }, nb::is_operator());
    cls.def("__repr__", [](const Transformation &t) {
        std::ostringstream out;
        out << "Transformation(a=" << t.a() << ", b=" << t.b() << ", c=" << t.c()
            << ", d=" << t.d() << ", tx=" << t.tx() << ", ty=" << t.ty() << ")";
        return out.str();
    });

    // Composition: t1 * t2 applies t2 first, then t1.
    cls.def("__mul__", [](const Transformation &a, const Transformation &b) { return a * b; }, nb::is_operator());

    // Application to a shape: pgl defines operator* for every shape except
    // Rectangle and Disk (see the file comment above) -- ten overloads here.
    cls.def("__mul__", [](const Transformation &t, const Point &s) { return t * s; }, nb::is_operator());
    cls.def("__mul__", [](const Transformation &t, const Segment &s) { return t * s; }, nb::is_operator());
    cls.def("__mul__", [](const Transformation &t, const OrientedSegment &s) { return t * s; }, nb::is_operator());
    cls.def("__mul__", [](const Transformation &t, const Line &s) { return t * s; }, nb::is_operator());
    cls.def("__mul__", [](const Transformation &t, const OrientedLine &s) { return t * s; }, nb::is_operator());
    cls.def("__mul__", [](const Transformation &t, const Ray &s) { return t * s; }, nb::is_operator());
    cls.def("__mul__", [](const Transformation &t, const Halfplane &s) { return t * s; }, nb::is_operator());
    cls.def("__mul__", [](const Transformation &t, const Triangle &s) { return t * s; }, nb::is_operator());
    cls.def("__mul__", [](const Transformation &t, const Convex &s) { return t * s; }, nb::is_operator());
    cls.def("__mul__", [](const Transformation &t, const Polygon &s) { return t * s; }, nb::is_operator());
}
