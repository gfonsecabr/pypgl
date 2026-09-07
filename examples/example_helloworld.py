"""A small "HELLO WORLD" poster drawn with geometry rather than text.

The Python port of pgl's `examples/example_helloworld.cpp`.

Every letter is built from ordinary shapes and drawn in its own style: bold
segments for the H, stacked rectangles for the E, a `Polyline` template for the
two Ls, a `PolygonWithHoles` for the two Os, a `Disk` and a `Triangle` for the
R, a `Convex` counter for the D, and a `HalfplaneIntersection` for the stroke of
the exclamation mark.

Two of the letters are templates rather than separately authored shapes: the L
and the O are each built once and translated into their two slots with `+`.

Output: example_helloworld.svg
"""

import pypgl as pgl


def main():
    canvas = pgl.Canvas()

    # HELLO ------------------------------------------------------------------
    # H is made from three bold segments.
    canvas.stroke("midnightblue").strokeWidth("4px")
    canvas.draw([
        pgl.Segment(0, 28, 0, 44),
        pgl.Segment(10, 28, 10, 44),
        pgl.Segment(0, 36, 10, 36),
    ])

    # E is a stack of rectangular brush strokes.
    canvas.stroke("none").fill("tomato")
    canvas.draw([
        pgl.Rectangle(14, 28, 17, 44),
        pgl.Rectangle(16, 41, 25, 44),
        pgl.Rectangle(16, 34, 23, 37),
        pgl.Rectangle(16, 28, 25, 31),
    ])

    # This L is a template. Its two occurrences are translated copies rather
    # than two separately authored letters.
    letter_l = pgl.Polyline([0, 16, 0, 0, 10, 0])
    canvas.stroke("seagreen").strokeWidth("4px")
    canvas.draw([letter_l + pgl.Point(29, 28), letter_l + pgl.Point(42, 28)])

    # O is a polygon with a hole, the counter cut out of the letter rather than
    # painted over it, so whatever is behind it shows through.
    letter_o = pgl.PolygonWithHoles(
        pgl.Polygon([2, 0, 9, 0, 11, 3, 11, 13, 9, 16, 2, 16, 0, 13, 0, 3]),
        [pgl.Polygon([3, 4, 8, 3, 9, 6, 9, 10, 8, 13, 3, 12, 2, 9, 2, 6])],
    )
    canvas.stroke("darkorange").strokeWidth("2px").fill("gold")
    canvas.draw(letter_o + pgl.Point(56, 28))

    # WORLD ------------------------------------------------------------------
    # W is a single zig-zag polyline; two points make the corners sparkle.
    canvas.stroke("rebeccapurple").strokeWidth("4px")
    canvas.draw(pgl.Polyline([0, 16, 2, 0, 6, 9, 10, 0, 12, 16]))
    canvas.stroke("plum").fill("plum")
    canvas.draw([pgl.Point(2, 0), pgl.Point(10, 0)])

    # Reuse the O, translated into WORLD's second slot.
    canvas.stroke("darkorange").strokeWidth("2px").fill("gold")
    canvas.draw(letter_o + pgl.Point(17, 0))

    # R combines a rectangle, disks, and a triangular kickstand.
    canvas.stroke("none").fill("steelblue")
    canvas.draw([
        pgl.Rectangle(34, 0, 37, 16),
        pgl.Disk(pgl.Point(38, 12), 6),
        pgl.Triangle(37, 8, 46, 0, 41, 0),
    ])
    canvas.fill("white").draw(pgl.Disk(pgl.Point(38, 12), 3))

    # The L comes from the same translated template used above.
    canvas.stroke("seagreen").strokeWidth("4px")
    canvas.draw(letter_l + pgl.Point(50, 0))

    # D is a faceted polygon set against a solid spine, with a convex counter.
    canvas.stroke("sienna").strokeWidth("2px").fill("peachpuff")
    canvas.draw([
        pgl.Rectangle(63, 0, 66, 16),
        pgl.Polygon([65, 0, 72, 0, 77, 4, 77, 12, 72, 16, 65, 16]),
    ])
    canvas.stroke("none").fill("white")
    canvas.draw(pgl.Convex([67, 3, 71, 3, 74, 6, 74, 10, 71, 13, 67, 13]))

    # ! is a triangle for the dot and a half-plane intersection for the stroke.
    canvas.stroke("grey").strokeWidth("2px").fill("lightyellow")
    canvas.draw(pgl.Triangle(79, 0, 82, 7, 85, 0))
    canvas.draw(pgl.HalfplaneIntersection([
        pgl.Halfplane(80, 15, 81, 10),
        pgl.Halfplane(1, 10, 10, 10),
        pgl.Halfplane(83, 10, 84, 25),
    ]))

    canvas.writeSVG("example_helloworld.svg")
    print("wrote example_helloworld.svg")


if __name__ == "__main__":
    main()
