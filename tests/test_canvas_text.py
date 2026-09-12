"""Canvas text: `Text` at a point or in a box, and the `fontSize` style command.

A Text is not a shape, only an instruction to the canvas, but it is drawn like
one and captures the style active when it is drawn. The expected SVG fragments
are the ones pgl's own canvas unit tests pin, which is what makes these a check
that the binding forwards each constructor and style command unchanged.
"""

from fractions import Fraction
import xml.etree.ElementTree as ET

import pytest

from pypgl import Canvas, Point, Rectangle, Text, TextFit


def _fitted(text, font_size=16):
    # A 100 x 100 window in a 120 x 120 image with a 10 pixel margin: one plane
    # unit is one pixel, x maps to 10 + x and y to 110 - y.
    return (Canvas().size(120, 120).margin(10).view(Rectangle(Point(0, 0), Point(100, 100)))
            .fontSize(font_size).draw(text).toSVG())


def test_text_at_a_point_takes_the_stroke_color_and_the_current_font_size():
    canvas = Canvas().size(200, 200)
    canvas.stroke("crimson").draw(Text("p", Point(3, 4))).fontSize("24").draw(Text("q", Point(3, 4)))
    svg = canvas.toSVG()
    assert ('<text x="100" y="104.088" font-family="Helvetica, Arial, sans-serif" font-size="16" '
            'text-anchor="middle" xml:space="preserve" fill="crimson" fill-opacity="1">p</text>') in svg
    assert 'font-size="24" text-anchor="middle" xml:space="preserve" fill="crimson" fill-opacity="1">q</text>' in svg
    assert "<title>" not in svg  # text is already on display


def test_font_size_accepts_a_number_or_a_length_string():
    assert _fitted(Text("A", Point(50, 50)), 24) == _fitted(Text("A", Point(50, 50)), "24")


def test_text_sized_in_pixels_widens_the_padding():
    canvas = Canvas().size(200, 200).margin(10)
    canvas.draw([Point(0, 0), Point(100, 0)]).fontSize(20).draw(Text("HHHH", Point(0, 0)))
    assert '<text x="38.88"' in canvas.toSVG()


def test_text_in_a_box_fills_it_or_shrinks_into_it():
    flat = Rectangle(Point(0, 0), Point(100, 20))
    assert ('<text x="60" y="105.524" font-family="Helvetica, Arial, sans-serif" font-size="21.6216"'
            in _fitted(Text("HH", flat)))
    assert 'font-size="69.2521"' in _fitted(Text("HH", Rectangle(Point(0, 30), Point(100, 100))))
    assert 'font-size="16"' in _fitted(Text("HH", flat, TextFit.shrink), 16)
    assert 'font-size="21.6216"' in _fitted(Text("HH", flat, TextFit.shrink), 40)


def test_nothing_is_drawn_without_room_or_without_text():
    assert "<text" not in _fitted(Text("HH", Rectangle(Point(0, 0), Point(100, 0))))
    assert "<text" not in _fitted(Text("", Rectangle(Point(0, 0), Point(100, 20))))


def test_text_sized_in_plane_units_scales_with_the_drawing():
    canvas = Canvas().size(120, 120).margin(10).view(Rectangle(Point(0, 0), Point(100, 100)))
    canvas.draw(Text("A", Point(50, 50), 5))
    assert 'font-size="5"' in canvas.toSVG()
    canvas.scale(2)
    assert 'font-size="10"' in canvas.toSVG()
    alone = Canvas().size(200, 200).margin(10).draw(Text("HH", Point(0, 0), 10.0))
    assert 'font-size="124.654"' in alone.toSVG()


@pytest.mark.parametrize("size", [0, -1, 0.0])
def test_a_size_must_be_strictly_positive(size):
    with pytest.raises(ValueError):
        Text("A", Point(0, 0), size)


def test_an_exact_position_is_accepted():
    canvas = Canvas().size(120, 120).margin(10).view(Rectangle(Point(0, 0), Point(100, 100)))
    canvas.draw(Text("A", Point(Fraction(101, 2), "1/2"), 5))
    assert '<text x="60.5"' in canvas.toSVG()


def test_without_a_stroke_text_is_painted_in_the_fill_in_every_backend():
    canvas = Canvas().size(200, 200)
    canvas.stroke("none").fill("purple").fillOpacity("0.25").draw(Text("a<b & (c) é", Point(0, 0)))
    assert 'fill="purple" fill-opacity="0.25">a&lt;b &amp; (c) é</text>' in canvas.toSVG()
    ET.fromstring(canvas.toSVG())  # still well-formed XML
    pdf = canvas.toPDF()
    assert b"/BaseFont /Helvetica\r\n" in pdf
    assert b"(a<b & \\(c\\) \xe9) Tj" in pdf  # re-encoded as the one WinAnsi byte
    assert "\\fontfamily{phv}\\selectfont a\\textless{}b \\&amp; (c) é</text>" in canvas.toIPE()

    unpainted = Canvas().stroke("none").fill("none").draw(Text("x", Point(0, 0)))
    assert b" Tj " not in unpainted.toPDF()
    assert "<text" not in unpainted.toIPE()


def test_accessors_and_repr():
    box = Rectangle(Point(0, 0), Point(4, 2))
    assert Text("p", Point(1, 2)).text() == "p"
    assert Text("p", Point(1, 2)).size() is None
    assert Text("p", Point(1, 2), 3).size() == 3.0
    assert Text("p", box).fit() is TextFit.fill
    assert Text("p", box, TextFit.shrink).fit() is TextFit.shrink
    assert repr(Text("p", Point(1, 2), 3)) == "Text('p', position=(1,2), size=3)"
    assert repr(Text("p", box, TextFit.shrink)) == "Text('p', box=[(0,0),(4,2)], fit=shrink)"


def test_text_draws_as_part_of_a_collection_and_inline():
    canvas = Canvas().draw([Point(0, 0), Text("origin", Point(0, 1)), [Text("nested", Point(0, 2))]])
    assert canvas.toSVG().count("<text") == 2
    assert "origin</text>" in Text("origin", Point(0, 0))._repr_svg_()


def test_a_string_is_still_not_drawable():
    with pytest.raises(TypeError, match="a Text"):
        Canvas().draw("hello")
