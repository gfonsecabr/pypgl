#include "common.h"

using namespace pypgl;

// Canvas: pgl's lightweight SVG renderer (visualization/canvas.hpp). It stores
// drawn shapes in insertion order, each capturing the style active at the moment
// it was drawn, and fits the whole drawing into the exported image (preserving
// aspect ratio, clipping the infinite primitives to the viewport).
//
// The C++ API is stream-based (`canvas << pgl::stroke("red") << shape`). That
// does not map to Python, so the binding exposes the same operations as methods:
//
//   - configuration   — scale/width/height/size/margin/pointRadius/borders and
//                        the numeric strokeWidth (all fluent: they return self);
//   - style           — stroke/fill/fillOpacity/strokeOpacity, each taking an SVG
//                        string and applied to the *current* style, so (exactly
//                        like the C++ stream) only shapes drawn afterwards see it;
//   - draw(shape)      — one overload per bound shape, equivalent to `<< shape`;
//   - toSVG/writeSVG   — serialize to a string / a file.
//
// Every fluent method returns the same canvas (reference_internal keeps the
// canvas alive behind the returned handle), so `Canvas().size(...).draw(s)`
// chains as in C++. `_repr_svg_` (added in __init__.py for the canvas itself and
// for every shape) is what makes shapes render inline in Jupyter.

namespace {

// One `draw` overload per shape, forwarding to the canvas stream operator. The
// shape captures the canvas's current style, matching `canvas << shape`.
#define CANVAS_DRAW(cls, T)                                                  \
    cls.def("draw",                                                          \
            [](pgl::Canvas &c, const T &s) -> pgl::Canvas & {               \
                c << s;                                                       \
                return c;                                                     \
            },                                                               \
            nb::arg("shape"), nb::rv_policy::reference_internal,             \
            "Draw a shape with the current style and return the canvas.")

// One style command (stroke/fill/...) applied to the current style, returning
// self. `Maker` is the pgl free function (pgl::stroke, pgl::fill, ...).
#define CANVAS_STYLE(cls, NAME, MAKER)                                       \
    cls.def(#NAME,                                                           \
            [](pgl::Canvas &c, std::string value) -> pgl::Canvas & {        \
                c << MAKER(std::move(value));                                \
                return c;                                                    \
            },                                                               \
            nb::arg("value"), nb::rv_policy::reference_internal)

}  // namespace

void bind_canvas(nb::module_ &m) {
    nb::class_<pgl::Canvas> cls(m, "Canvas");
    cls.def(nb::init<>(), "Create an empty canvas with the default style and viewport.");

    // --- Configuration (fluent) ---
    cls.def("scale", [](pgl::Canvas &c, double f) -> pgl::Canvas & { return c.scale(f); },
            nb::arg("factor"), nb::rv_policy::reference_internal,
            "Multiply the auto-fitted scale by factor (>0). >1 zooms in, <1 out.");
    cls.def("width", [](pgl::Canvas &c, double w) -> pgl::Canvas & { return c.width(w); },
            nb::arg("pixels"), nb::rv_policy::reference_internal,
            "Set the exported SVG width in pixels (>0).");
    cls.def("height", [](pgl::Canvas &c, double h) -> pgl::Canvas & { return c.height(h); },
            nb::arg("pixels"), nb::rv_policy::reference_internal,
            "Set the exported SVG height in pixels (>0).");
    cls.def("size", [](pgl::Canvas &c, double w, double h) -> pgl::Canvas & { return c.size(w, h); },
            nb::arg("width"), nb::arg("height"), nb::rv_policy::reference_internal,
            "Set the exported SVG width and height in pixels (>0).");
    cls.def("margin", [](pgl::Canvas &c, double px) -> pgl::Canvas & { return c.margin(px); },
            nb::arg("pixels"), nb::rv_policy::reference_internal,
            "Reserve blank space (>=0) around the fitted drawing.");
    cls.def("pointRadius", [](pgl::Canvas &c, double r) -> pgl::Canvas & { return c.pointRadius(r); },
            nb::arg("pixels"), nb::rv_policy::reference_internal,
            "Set the rendered radius of Point primitives in pixels (>0).");
    cls.def("strokeWidth", [](pgl::Canvas &c, double w) -> pgl::Canvas & { return c.strokeWidth(w); },
            nb::arg("pixels"), nb::rv_policy::reference_internal,
            "Set the current stroke width in pixels (>0); captured by later shapes.");
    cls.def("borders", [](pgl::Canvas &c, bool enabled) -> pgl::Canvas & { return c.borders(enabled); },
            nb::arg("enabled") = true, nb::rv_policy::reference_internal,
            "Enable or disable a thin frame around the whole SVG.");

    // --- Style commands (fluent; affect only shapes drawn afterwards) ---
    CANVAS_STYLE(cls, stroke, pgl::stroke);
    CANVAS_STYLE(cls, fill, pgl::fill);
    CANVAS_STYLE(cls, fillOpacity, pgl::fillOpacity);
    CANVAS_STYLE(cls, strokeOpacity, pgl::strokeOpacity);

    // --- Draw (one overload per bound shape) ---
    CANVAS_DRAW(cls, Point);
    CANVAS_DRAW(cls, Segment);
    CANVAS_DRAW(cls, OrientedSegment);
    CANVAS_DRAW(cls, Line);
    CANVAS_DRAW(cls, OrientedLine);
    CANVAS_DRAW(cls, Ray);
    CANVAS_DRAW(cls, Halfplane);
    CANVAS_DRAW(cls, Triangle);
    CANVAS_DRAW(cls, Rectangle);
    CANVAS_DRAW(cls, Convex);
    CANVAS_DRAW(cls, Disk);

    // draw(None) is a no-op that still returns the canvas, so the result of a
    // construction (e.g. an `intersection` that may be empty -> None) can be
    // drawn directly without a None guard. Registered last: nanobind tries the
    // typed shape overloads first, so a real shape never reaches this; only None
    // (and otherwise-unmatched arguments) does. Anything that is not None is a
    // genuine type error and is reported as one.
    cls.def("draw",
            [](pgl::Canvas &c, nb::object shape) -> pgl::Canvas & {
                if (shape.is_none())
                    return c;
                std::string name = nb::cast<std::string>(nb::str(shape.type().attr("__name__")));
                throw nb::type_error(
                    ("Canvas.draw() expects a pypgl shape or None, got " + name).c_str());
            },
            nb::arg("shape").none(), nb::rv_policy::reference_internal,
            "Drawing None is a no-op (returns the canvas), so an empty construction "
            "result can be drawn without a None check.");

    // --- Output ---
    cls.def("toSVG", [](const pgl::Canvas &c) { return c.toSVG(); },
            "Serialize the canvas to a complete SVG document string.");
    cls.def("writeSVG", [](const pgl::Canvas &c, const std::string &path) { c.writeSVG(path); },
            nb::arg("path"), "Write the SVG document to a file (raises if it cannot be opened).");
}
