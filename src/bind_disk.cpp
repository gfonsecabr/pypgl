#include "common.h"

using namespace pypgl;

// Disk: the closed circle and its interior, stored exactly as three boundary
// points (so an integer-coordinate circle keeps an exact rational center and
// squared radius). Constructors from three boundary points or from a
// center+radius, the exact measures (center / squaredRadius / bbox /
// pointInside), the full predicate matrix, exact intersection against a point,
// and squared distance against the shapes pgl implements it for.
//
// Some disk quantities are irrational by nature (the area carries pi; the radius
// is a square root unless the disk was built from a center and radius). `area()`
// is therefore always a Python float; `radius()` is an exact Fraction in the
// center+radius case and a float otherwise (see its binding). The exact
// counterpart `squaredRadius()` (and `bbox()`) stay rational. `diameter()` is
// reconstructed as an exact Segment for center+radius disks (pgl only offers a
// floating-point one); `fbox()` is intentionally not bound — it returns a
// double-coordinate shape, which is not a registered Python type.

void bind_disk(nb::module_ &m) {
    nb::class_<Disk> cls(m, "Disk");
    cls.def(nb::init<Point, Point, Point>(), nb::arg("a"), nb::arg("b"), nb::arg("c"),
            "Create the disk through three boundary points (stored canonically: "
            "lex-sorted, CCW when non-degenerate, so argument order does not matter).");
    cls.def(nb::init<Point, Num>(), nb::arg("center"), nb::arg("radius"),
            "Create a disk from its center and radius (the radius is stored exactly; "
            "a negative radius is treated as its absolute value).");
    cls.def(nb::init<Num, Num, Num>(), nb::arg("x"), nb::arg("y"), nb::arg("radius"),
            "Create a disk from center coordinates and a radius.");

    cls.def("a", [](const Disk &d) { return d.a(); }, "First boundary point (lexicographically smallest).");
    cls.def("b", [](const Disk &d) { return d.b(); }, "Second boundary point in canonical order.");
    cls.def("c", [](const Disk &d) { return d.c(); }, "Third boundary point (a, b, c wind counterclockwise).");

    cls.def("center", [](const Disk &d) { return d.center(); },
            "Exact center (circumcenter of the three boundary points) as a Point.");
    cls.def("squaredRadius", [](const Disk &d) { return d.squaredRadius(); },
            "Exact squared radius (a Fraction).");
    cls.def("radius", [](const Disk &d) -> nb::object {
                // pgl keeps an exact radius only for disks built from a center and
                // radius (axis-aligned boundary witness); there radius<ERational>()
                // returns the exact value, and we hand it back as a Fraction.
                // Otherwise the radius is a square root with no exact form, and
                // radius<ERational>() throws (ERational has no std::sqrt) — fall
                // back to the floating-point value. Delegating the exact/inexact
                // decision to pgl this way keeps it in lockstep with the library.
                try {
                    return nb::cast(d.radius<Num>());
                } catch (const std::runtime_error &) {
                    return nb::cast(d.radius<double>());
                }
            },
            "Radius as an exact Fraction when the disk was built from a center and "
            "radius, otherwise a float (the radius is a square root in general). "
            "squaredRadius() is always exact.");
    cls.def("area", [](const Disk &d) { return d.area(); },
            "Area (pi * r^2) as a float. Approximate by nature; squaredRadius() is exact.");
    cls.def("diameter", [](const Disk &d) -> Segment {
                // The horizontal diameter is the chord (cx - r, cy)--(cx + r, cy).
                // pgl only offers a floating-point diameter() (a double-coordinate
                // segment we cannot represent), but when the disk was built from a
                // center and radius the endpoints are exact, so we build the exact
                // Segment ourselves. radius<ERational>() throws for an irrational
                // radius (see radius()); there is no exact diameter to return.
                Num r;
                try {
                    r = d.radius<Num>();
                } catch (const std::runtime_error &) {
                    throw std::invalid_argument(
                        "Disk.diameter() is exact only for a disk built from a center "
                        "and radius; this disk has an irrational radius. Use center() "
                        "and radius() instead.");
                }
                const Point c = d.center();
                return Segment(Point(c.x() - r, c.y()), Point(c.x() + r, c.y()));
            },
            "The horizontal diameter as an exact Segment through the center. Defined "
            "only for disks built from a center and radius (an arbitrary disk has an "
            "irrational radius and no exact diameter segment).");
    cls.def("pointInside", [](const Disk &d) { return d.pointInside(); },
            "An exact point strictly inside the disk (the midpoint of a chord).");
    cls.def("isDegenerate", [](const Disk &d) { return d.isDegenerate(); },
            "Whether the three boundary points are collinear (no finite circle).");
    cls.def("bbox", [](const Disk &d) { return d.bbox(); },
            "Exact axis-aligned bounding box (a Rectangle); tight when built from a center and radius.");

    cls.def("index", [](const Disk &d, const Point &p) -> std::optional<std::ptrdiff_t> {
                auto i = d.index(p);
                if (i < 0) return std::nullopt;
                return i;
            }, nb::arg("point"), "Index of the boundary point equal to point, or None if none.");

    bind_value_semantics<Disk>(cls);
    PGL_BIND_OPERATORS(cls, Disk);
    cls.def("rotated90", [](const Disk &d, int k) { return d.rotated90(k); }, nb::arg("k") = 1,
            "Return the disk rotated by 90*k degrees about the origin.");
    PGL_BIND_INDEXING(cls, Disk);

    // Disk is now a full member of both shared matrix macros (see common.h),
    // so these two calls also bind Disk's own self-pair.
    PGL_BIND_ALL_PREDICATES(cls, Disk);
    // squaredDistance returns a float for the disk: the gap between an exterior
    // shape and the circle is generally irrational, so pgl offers no exact form.
    PGL_BIND_ALL_SQUARED_DISTANCE(cls, Disk);
    PGL_SQDIST(cls, Disk, ::pypgl::Disk);

    // Point<->Disk is the only L1/LInf distance pair Disk supports yet (see
    // PGL_BIND_ALL_L1LINF_DISTANCE's comment in common.h -- every other pair
    // needs a closed form pgl does not implement, tracked in its doc/todo.md).
    // Computed via an angular scan refined by golden-section search, so it is
    // always a float, never templated on ResultNumber. Disk has no
    // squaredHausdorffDistance/hausdorffDistanceL1/LInf at all.
    cls.def("distanceL1", [](const Disk &d, const Point &p) { return d.distanceL1(p); }, nb::arg("other"));
    cls.def("distanceLInf", [](const Disk &d, const Point &p) { return d.distanceLInf(p); }, nb::arg("other"));

    cls.def("intersection", [](const Disk &a, const Point &b) { return a.intersection(b); }, nb::arg("other"),
            "Exact intersection with a point: the point if contained, else None.");
}
