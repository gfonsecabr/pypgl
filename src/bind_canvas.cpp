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
//   - configuration   — scale/width/height/size/margin/borders (all fluent: they
//                        return self), which describe the whole exported image;
//   - style           — stroke/fill/fillOpacity/strokeOpacity/strokeWidth/
//                        pointRadius, each applied to the *current* style, so
//                        (exactly like the C++ stream) only shapes drawn
//                        afterwards see it;
//   - draw(shape)      — one overload per bound shape, equivalent to `<< shape`;
//   - to*/write*       — serialize to a string (bytes, for PDF) / to a file.
//
// strokeWidth and pointRadius used to be canvas-wide configuration taking a
// number; upstream turned both into per-element stream manipulators taking a
// string (pgl::strokeWidth("2"), pgl::pointRadius("3")), so they moved into the
// style group here. Each is bound twice -- once taking the SVG length string pgl
// itself takes, once taking a plain number, which is what a caller almost always
// has (the two argument types are disjoint, so the overloads never collide).
//
// Every fluent method returns the same canvas (reference_internal keeps the
// canvas alive behind the returned handle), so `Canvas().size(...).draw(s)`
// chains as in C++. `_repr_svg_` (added in __init__.py for the canvas itself and
// for every shape) is what makes shapes render inline in Jupyter.

namespace {

// Render a number the way a hand-written SVG length would read: no trailing
// zeros (std::to_string(3.0) would give "3.000000").
std::string lengthToString(double value) {
    std::ostringstream out;
    out << value;
    return out.str();
}

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
#define CANVAS_STYLE(cls, NAME, MAKER, DOC)                                  \
    cls.def(#NAME,                                                           \
            [](pgl::Canvas &c, std::string value) -> pgl::Canvas & {        \
                c << MAKER(std::move(value));                                \
                return c;                                                    \
            },                                                               \
            nb::arg("value"), nb::rv_policy::reference_internal, DOC)

// A style command whose value is a length: the same command, additionally
// accepting a plain number (formatted into the SVG length string pgl wants).
// The two argument types are disjoint, so the overloads never collide.
#define CANVAS_STYLE_LENGTH(cls, NAME, MAKER, DOC)                           \
    CANVAS_STYLE(cls, NAME, MAKER, DOC);                                     \
    cls.def(#NAME,                                                           \
            [](pgl::Canvas &c, double value) -> pgl::Canvas & {             \
                c << MAKER(lengthToString(value));                           \
                return c;                                                    \
            },                                                               \
            nb::arg("value"), nb::rv_policy::reference_internal, DOC)

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
    cls.def("borders", [](pgl::Canvas &c, bool enabled) -> pgl::Canvas & { return c.borders(enabled); },
            nb::arg("enabled") = true, nb::rv_policy::reference_internal,
            "Enable or disable a thin frame around the whole drawing.");
    // Framing by hand instead of by the drawing's own bounding box -- what an
    // arrangement whose far-away crossings would shrink everything else needs,
    // or a drawing whose box is stretched by the two points defining a line.
    cls.def("view", [](pgl::Canvas &c, const Rectangle &window) -> pgl::Canvas & { return c.view(window); },
            nb::arg("window"), nb::rv_policy::reference_internal,
            "Fit the export to an explicit rectangle of the plane rather than to the "
            "drawing's bounding box; geometry outside it falls outside the image. "
            "Calling it again replaces the window, and scale() and margin() still apply "
            "on top of it.");

    // --- Style commands (fluent; affect only shapes drawn afterwards) ---
    CANVAS_STYLE(cls, stroke, pgl::stroke, "Set the current stroke color (any SVG paint string).");
    CANVAS_STYLE(cls, fill, pgl::fill, "Set the current fill color (any SVG paint string; 'none' to disable).");
    CANVAS_STYLE(cls, fillOpacity, pgl::fillOpacity, "Set the current fill opacity ('0' to '1').");
    CANVAS_STYLE(cls, strokeOpacity, pgl::strokeOpacity, "Set the current stroke opacity ('0' to '1').");
    CANVAS_STYLE_LENGTH(cls, strokeWidth, pgl::strokeWidth,
                        "Set the current stroke width in pixels (>0); captured by shapes drawn afterwards.");
    CANVAS_STYLE_LENGTH(cls, pointRadius, pgl::pointRadius,
                        "Set the current rendered radius of Point primitives in pixels (>0); "
                        "captured by shapes drawn afterwards.");

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
    CANVAS_DRAW(cls, MonotoneChain);
    CANVAS_DRAW(cls, Polyline);
    CANVAS_DRAW(cls, Polygon);
    // A region is drawn as one path with a closed subpath per ring, so its
    // holes are punched out of the fill rather than painted over (SVG asks for
    // fill-rule=evenodd; PDF and Ipe get the same result by winding each hole
    // against the outer ring). A half-plane intersection is clipped to the
    // visible viewport, and only its real boundary edges are stroked.
    CANVAS_DRAW(cls, PolygonWithHoles);
    // A set of regions is drawn the same way, with one subpath per ring of
    // every component -- so a boolean result draws as one shape however many
    // pieces it came apart into.
    CANVAS_DRAW(cls, PolygonSet);
    CANVAS_DRAW(cls, HalfplaneIntersection);
    CANVAS_DRAW(cls, Disk);
    CANVAS_DRAW(cls, Triangulation);
    CANVAS_DRAW(cls, ShapeTree);

    // draw(collection) draws every element in order, each with the current
    // style, so a whole construction can be handed over at once:
    // canvas.draw(polygon.edges()), canvas.draw(triangulation.triangles()),
    // canvas.draw([tri, disk, point]). The elements go back through the bound
    // `draw` on the Python object, so a collection may mix shape types, may
    // hold None, and may nest (a list of lists draws flattened).
    //
    // Registered after every typed overload and before the None fallback:
    // every bound shape is iterable in the Python layer (__iter__ over its
    // defining points), so a Point handed here would otherwise be drawn as its
    // two coordinates rather than as itself. A str is iterable too and would
    // recurse forever (a one-character string iterates to itself), so it is
    // passed on to the fallback, which reports it as the type error it is.
    cls.def("draw",
            [](nb::object self, nb::iterable shapes) -> nb::object {
                if (nb::isinstance<nb::str>(shapes) || nb::isinstance<nb::bytes>(shapes))
                    throw nb::next_overload();
                nb::object draw = self.attr("draw");
                for (nb::handle shape : shapes)
                    draw(shape);
                return self;
            },
            nb::arg("shapes"),
            // The lambda returns the canvas's own Python object, so the fluent
            // chain works exactly as with the typed overloads; nb::sig says so
            // in the stub, which would otherwise promise a bare `object`.
            nb::sig("def draw(self, shapes: collections.abc.Iterable) -> Canvas"),
            "Draw every shape in a collection, in order, each with the current "
            "style, and return the canvas. Elements may be of mixed types, may be "
            "None, and may themselves be collections.");

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
    //
    // Three formats, all rendering the same fitted viewport: SVG, PDF, and Ipe
    // XML (ipe.otfried.org, a vector editor common in computational geometry).
    // toPDF returns `bytes`, not `str` -- a PDF is binary, and pgl's std::string
    // there is a byte buffer, not text (the other two are genuine text).
    //
    // None of the three write* methods is fluent: all return None, mirroring
    // pgl, where every write* returns void. (writePDF/writeIPE briefly returned
    // Canvas& upstream -- and pypgl 0.3.0 shipped them fluent because of it --
    // until pgl made the trio consistent.)
    cls.def("toSVG", [](const pgl::Canvas &c) { return c.toSVG(); },
            "Serialize the canvas to a complete SVG document string.");
    cls.def("writeSVG", [](const pgl::Canvas &c, const std::string &path) { c.writeSVG(path); },
            nb::arg("path"), "Write the SVG document to a file (raises if it cannot be opened).");
    cls.def("toPDF",
            [](const pgl::Canvas &c) {
                std::string pdf = c.toPDF();
                return nb::bytes(pdf.data(), pdf.size());
            },
            "Serialize the canvas to a complete PDF document (bytes).");
    cls.def("writePDF", [](const pgl::Canvas &c, const std::string &path) { c.writePDF(path); },
            nb::arg("path"), "Write the PDF document to a file (raises if it cannot be opened).");
    cls.def("toIPE", [](const pgl::Canvas &c) { return c.toIPE(); },
            "Serialize the canvas to a complete Ipe (.ipe) XML document string.");
    cls.def("writeIPE", [](const pgl::Canvas &c, const std::string &path) { c.writeIPE(path); },
            nb::arg("path"), "Write the Ipe XML document to a file (raises if it cannot be opened).");
}
