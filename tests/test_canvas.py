"""Canvas rendering (milestone 3 — notebook UX).

The stream-based C++ Canvas API is exposed as methods: fluent configuration and
style setters that return the same canvas, one `draw` overload per shape, and
`toSVG`/`toPDF`/`toIPE` plus their write* counterparts. `_repr_svg_`
(canvas-wide and per shape) is what renders geometry inline in Jupyter.

strokeWidth and pointRadius are *style* commands, not canvas-wide configuration:
like stroke/fill, each is captured by the shapes drawn after it. Each accepts
either the SVG length string pgl itself takes or a plain number.
"""

import xml.etree.ElementTree as ET

import pytest

import pypgl
from pypgl import (
    Canvas,
    Point,
    Segment,
    OrientedSegment,
    Line,
    OrientedLine,
    Ray,
    Halfplane,
    Triangle,
    Rectangle,
    Convex,
    Disk,
    MonotoneChain,
    Polyline,
    Polygon,
)


ALL_SHAPES = [
    Point(1, 2),
    Segment(0, 0, 4, 3),
    OrientedSegment(Point(0, 0), Point(4, 3)),
    Line(Point(0, 0), Point(1, 1)),
    OrientedLine(Point(0, 0), Point(1, 1)),
    Ray(Point(0, 0), Point(1, 1)),
    Halfplane(Point(0, 0), Point(1, 1)),
    Triangle(Point(0, 0), Point(4, 0), Point(2, 3)),
    Rectangle(Point(0, 0), Point(3, 2)),
    Convex([Point(0, 0), Point(2, 0), Point(1, 2)]),
    Disk(Point(0, 0), 3),
    MonotoneChain([Point(0, 0), Point(2, 1), Point(4, 0)]),
    Polyline([Point(0, 0), Point(2, 3), Point(4, 0)]),
    Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]),
]


def _is_valid_svg(text):
    assert text.startswith("<svg")
    root = ET.fromstring(text)  # raises on malformed XML
    assert root.tag.endswith("svg")
    return root


# --- Construction and output ---------------------------------------------

def test_empty_canvas_is_valid_svg():
    root = _is_valid_svg(Canvas().toSVG())
    # Default viewport is 1000x1000.
    assert root.attrib["width"] == "1000"
    assert root.attrib["height"] == "1000"


def test_size_sets_viewport():
    root = _is_valid_svg(Canvas().size(400, 300).toSVG())
    assert root.attrib["width"] == "400"
    assert root.attrib["height"] == "300"


def test_configuration_methods_are_fluent_and_return_same_canvas():
    c = Canvas()
    assert c.size(400, 300) is c
    assert c.width(500) is c
    assert c.height(200) is c
    assert c.margin(10) is c
    assert c.borders(True) is c
    assert c.scale(2) is c


def test_style_methods_are_fluent():
    c = Canvas()
    assert c.stroke("red") is c
    assert c.fill("blue") is c
    assert c.fillOpacity("0.5") is c
    assert c.strokeOpacity("0.5") is c
    assert c.strokeWidth(3) is c
    assert c.pointRadius(5) is c


def test_length_styles_take_a_number_or_a_string():
    # pgl's manipulators take an SVG length string; a plain number is accepted
    # here too, since that is what a caller usually has.
    for width in (3, "3"):
        svg = Canvas().strokeWidth(width).draw(Segment(0, 0, 4, 0)).toSVG()
        assert 'stroke-width="3"' in svg
    for radius in (7, "7"):
        svg = Canvas().pointRadius(radius).draw(Point(0, 0)).toSVG()
        assert 'r="7"' in svg


def test_length_styles_are_captured_per_shape():
    # strokeWidth used to be canvas-wide configuration; upstream made it a style
    # command, so a shape keeps the width active when it was drawn.
    svg = (
        Canvas()
        .strokeWidth(1)
        .draw(Segment(0, 0, 4, 0))
        .strokeWidth(9)
        .draw(Segment(0, 1, 4, 1))
        .toSVG()
    )
    assert 'stroke-width="1"' in svg
    assert 'stroke-width="9"' in svg


@pytest.mark.parametrize("value", [0, -1])
def test_invalid_configuration_raises(value):
    with pytest.raises(Exception):
        Canvas().width(value)


# --- Drawing -------------------------------------------------------------

@pytest.mark.parametrize("shape", ALL_SHAPES, ids=lambda s: type(s).__name__)
def test_draw_every_shape_produces_valid_svg(shape):
    svg = Canvas().size(200, 200).draw(shape).toSVG()
    _is_valid_svg(svg)


def test_draw_is_fluent_and_chains():
    c = Canvas()
    assert c.draw(Point(0, 0)) is c
    assert c.draw(Point(1, 1)).draw(Point(2, 2)) is c


def test_draw_none_is_a_noop_returning_the_canvas():
    # So the result of a construction (e.g. an empty intersection -> None) can be
    # drawn directly without a None guard.
    c = Canvas()
    assert c.draw(None) is c
    before = c.toSVG()
    c.draw(None)
    assert c.toSVG() == before


def test_draw_empty_intersection_directly():
    disjoint = Segment(0, 0, 1, 1).intersection(Segment(5, 5, 6, 6))
    assert disjoint is None
    # No guard needed: drawing the None result is a no-op.
    svg = Canvas().draw(Segment(0, 0, 4, 0)).draw(disjoint).toSVG()
    _is_valid_svg(svg)


def test_draw_rejects_non_shape():
    with pytest.raises(TypeError):
        Canvas().draw(5)


def test_point_renders_as_circle():
    svg = Canvas().draw(Point(1, 1)).toSVG()
    assert "<circle" in svg


def test_segment_renders_as_line():
    svg = Canvas().draw(Segment(0, 0, 4, 3)).toSVG()
    assert "<line" in svg


def test_triangle_renders_as_polygon():
    svg = Canvas().draw(Triangle(Point(0, 0), Point(4, 0), Point(2, 3))).toSVG()
    assert "<polygon" in svg


def test_borders_adds_a_frame_rect():
    with_border = Canvas().size(100, 100).borders(True).toSVG()
    without_border = Canvas().size(100, 100).borders(False).toSVG()
    assert "<rect" in with_border
    assert "<rect" not in without_border


def test_style_is_captured_at_draw_time():
    # A shape keeps the style active when it was drawn; changing the style
    # afterwards only affects later shapes (mirrors the C++ stream).
    svg = (
        Canvas()
        .stroke("royalblue")
        .draw(Segment(0, 0, 4, 0))
        .stroke("crimson")
        .draw(Segment(0, 1, 4, 1))
        .toSVG()
    )
    assert 'stroke="royalblue"' in svg
    assert 'stroke="crimson"' in svg


def test_oriented_shapes_emit_arrowhead_marker():
    svg = Canvas().size(200, 200).draw(OrientedSegment(Point(0, 0), Point(4, 3))).toSVG()
    assert "pgl-arrowhead" in svg


# --- writeSVG ------------------------------------------------------------

def test_write_svg_to_file(tmp_path):
    path = tmp_path / "out.svg"
    Canvas().size(100, 100).draw(Point(0, 0)).writeSVG(str(path))
    text = path.read_text()
    _is_valid_svg(text)


# --- PDF and Ipe export --------------------------------------------------

def test_to_pdf_returns_bytes():
    # A PDF is binary, so it comes back as bytes rather than str.
    pdf = Canvas().size(100, 100).draw(Triangle(Point(0, 0), Point(4, 0), Point(2, 3))).toPDF()
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF-")


def test_write_pdf_to_file(tmp_path):
    path = tmp_path / "out.pdf"
    Canvas().size(100, 100).draw(Point(0, 0)).writePDF(str(path))
    assert path.read_bytes().startswith(b"%PDF-")


def test_to_ipe_is_valid_xml():
    ipe = Canvas().size(100, 100).draw(Segment(0, 0, 4, 3)).toIPE()
    assert isinstance(ipe, str)
    root = ET.fromstring(ipe)  # raises on malformed XML
    assert root.tag == "ipe"


def test_write_ipe_to_file(tmp_path):
    path = tmp_path / "out.ipe"
    Canvas().size(100, 100).draw(Point(0, 0)).writeIPE(str(path))
    assert ET.fromstring(path.read_text()).tag == "ipe"


@pytest.mark.parametrize("method", ["writeSVG", "writePDF", "writeIPE"])
def test_write_methods_are_not_fluent(tmp_path, method):
    # Every write* returns None, mirroring pgl, where each returns void.
    c = Canvas().size(100, 100).draw(Point(0, 0))
    assert getattr(c, method)(str(tmp_path / "out")) is None


# --- _repr_svg_ (inline notebook rendering) ------------------------------

def test_canvas_repr_svg_matches_to_svg():
    c = Canvas().size(120, 120).draw(Point(0, 0))
    assert c._repr_svg_() == c.toSVG()


@pytest.mark.parametrize("shape", ALL_SHAPES, ids=lambda s: type(s).__name__)
def test_every_shape_has_inline_svg(shape):
    _is_valid_svg(shape._repr_svg_())


def test_inline_shape_size_defaults_to_repr_svg_size():
    # Shapes render on a one-shot canvas half pgl's 1000x1000 default.
    assert pypgl.REPR_SVG_SIZE == 500
    root = _is_valid_svg(Point(0, 0)._repr_svg_())
    assert root.attrib["width"] == "500"
    assert root.attrib["height"] == "500"


def test_repr_svg_size_is_configurable():
    original = pypgl.REPR_SVG_SIZE
    try:
        pypgl.REPR_SVG_SIZE = 250
        root = _is_valid_svg(Point(0, 0)._repr_svg_())
        assert root.attrib["width"] == "250"
    finally:
        pypgl.REPR_SVG_SIZE = original


def test_explicit_canvas_size_is_unaffected_by_repr_svg_size():
    # A canvas the user sizes honors its own size, not REPR_SVG_SIZE.
    root = _is_valid_svg(Canvas().size(800, 600).draw(Point(0, 0))._repr_svg_())
    assert root.attrib["width"] == "800"
    assert root.attrib["height"] == "600"
