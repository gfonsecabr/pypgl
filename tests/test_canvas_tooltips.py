"""Canvas tooltips: the `tooltips` style command and `draw(shape, tooltip)`.

A shape's tooltip is its textual form unless tooltips are off or the shape is
drawn with its own. The expected fragments are the ones pgl's own canvas unit
tests pin: an SVG `<title>`, and in PDF an annotation that paints nothing, its
text in UTF-16BE behind a byte order mark.
"""

import pytest

from pypgl import Canvas, Point, Segment, Text, Triangle, Triangulation

SEGMENT = Segment(0, 0, 40, 30)
TRIANGLE = Triangle(Point(10, 10), Point(30, 15), Point(20, 35))
POINT = Point(5, 5)


def test_tooltips_turn_off_and_back_on_for_shapes_drawn_later():
    canvas = Canvas()
    canvas.draw(SEGMENT).tooltips(False).draw(TRIANGLE).draw(Text("t", POINT)).tooltips().draw(POINT)

    # The triangle was drawn with tooltips off, and turning them back on does
    # not give it one.
    svg = canvas.toSVG()
    assert svg.count("<title") == 2
    assert "<title>(0,0)--(40,30)</title>" in svg
    assert "<title>(5,5)</title>" in svg

    pdf = canvas.toPDF()
    assert pdf.count(b"/Type /Annot\r\n") == 2
    assert b"/Subtype /Line" in pdf
    assert b"/Subtype /Circle" in pdf
    assert b"/Subtype /Polygon" not in pdf
    assert b"/Contents <FEFF00280035002C00350029>" in pdf  # "(5,5)"


def test_with_tooltips_off_from_the_start_nothing_carries_one():
    silent = Canvas().tooltips(False).draw([SEGMENT, TRIANGLE, POINT])
    assert "<title" not in silent.toSVG()
    assert b"/Annot" not in silent.toPDF()


def test_a_shape_drawn_with_its_own_tooltip_keeps_it_even_while_tooltips_are_off():
    canvas = Canvas()
    (canvas.draw(SEGMENT, "a<b")
           .tooltips(False)
           .draw(Point(1, 2), "literal")
           .draw([(Point(7, 8), "first"), (Point(9, 10), "second")])
           .draw((Point(11, 12), ""))
           .draw(Point(15, 16)))

    # The tooltip lasts for its shape only: the last point, drawn with tooltips
    # off, has none, and neither does the empty tooltip.
    svg = canvas.toSVG()
    assert svg.count("<title") == 4
    for title in ("a&lt;b", "literal", "first", "second"):
        assert f"<title>{title}</title>" in svg
    assert "(0,0)--(40,30)" not in svg

    pdf = canvas.toPDF()
    assert pdf.count(b"/Type /Annot\r\n") == 4
    assert b"/Contents <FEFF0061003C0062>" in pdf  # "a<b"


def test_a_tooltip_pair_nests_in_a_collection():
    canvas = Canvas().tooltips(False).draw([[(POINT, "deep")], None, SEGMENT])
    svg = canvas.toSVG()
    assert svg.count("<title") == 1
    assert "<title>deep</title>" in svg


def test_only_a_shape_takes_a_tooltip():
    canvas = Canvas()
    with pytest.raises(TypeError, match="Text"):
        canvas.draw(Text("t", POINT), "tip")
    with pytest.raises(TypeError, match="Triangulation"):
        canvas.draw(Triangulation([POINT, Point(1, 0), Point(0, 1)]), "tip")
    with pytest.raises(TypeError):
        canvas.draw(POINT, 3)
    # None is still a no-op, with or without a tooltip.
    assert canvas.draw(None, "tip") is canvas
    assert "<title" not in canvas.toSVG()
