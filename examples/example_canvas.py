"""A gallery of every bounded shape, laid out on a grid.

The Python port of pgl's `examples/example_canvas.cpp`.

Each shape is built inside the box [0,8]x[0,8] and then translated into its own
10x10 cell of a 4x3 grid, so every cell keeps a one-unit gutter around its
shape. Translation is just `shape + point`, which every shape supports,
including HalfplaneIntersection (its half-planes move with the region).

The unbounded shapes (Line, OrientedLine, Ray, Halfplane) are left out. Point is
bounded but has no extent, so its cell holds a single dot at the center rather
than an 8x8 figure.

Hover over a shape in a browser to see its textual form: the canvas stores it as
the SVG <title> of the element.

Output: canvas_gallery.svg, .pdf and .ipe
"""

import pypgl as pgl

CELL_SIZE = 10   # side of a grid cell
SHAPE_SIZE = 8   # side of the box every shape is built in
GUTTER = (CELL_SIZE - SHAPE_SIZE) // 2
COLUMNS = 4
ROWS = 3

COLORS = [
    "crimson", "darkorange", "goldenrod", "seagreen",
    "teal", "steelblue", "royalblue", "slateblue",
    "purple", "magenta", "sienna", "olivedrab",
]


def points(*coords):
    """A list of Points from a flat coordinate list.

    The fixed-size shapes take flat coordinates directly (``Segment(0, 0, 8, 8)``),
    but the variable-size ones want a sequence of Points, so this spells the C++
    brace-list constructors the examples use.
    """
    return [pgl.Point(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]


def at_cell(shape, column, row):
    """The shape translated from [0,8]x[0,8] into the cell at (column, row).

    Row 0 is the top row: the canvas y-axis points up, so rows are laid out
    downwards to match reading order.
    """
    return shape + pgl.Point(
        CELL_SIZE * column + GUTTER, CELL_SIZE * (ROWS - 1 - row) + GUTTER
    )


def main():
    # The five half-planes of a square with its top-right corner cut off, each
    # traversed counterclockwise so that the region lies on its left.
    halfplanes = [
        pgl.Halfplane(0, 0, 8, 0),   # y >= 0
        pgl.Halfplane(8, 0, 8, 8),   # x <= 8
        pgl.Halfplane(8, 8, 0, 8),   # y <= 8
        pgl.Halfplane(0, 8, 0, 0),   # x >= 0
        pgl.Halfplane(7, 3, 5, 7),   # a corner cut
    ]

    shapes = [
        pgl.Point(4, 4),
        pgl.Segment(0, 0, 8, 8),
        pgl.OrientedSegment(0, 8, 8, 0),
        pgl.MonotoneChain(points(0, 0, 2, 6, 4, 1, 6, 8, 8, 3)),
        pgl.Polyline(points(0, 0, 8, 8, 0, 8, 8, 0)),          # self-crossing
        pgl.Triangle(0, 0, 8, 0, 4, 8),
        pgl.Rectangle(0, 0, 8, 8),
        pgl.Disk(pgl.Point(4, 4), 4),
        pgl.Convex(points(0, 3, 0, 5, 3, 8, 5, 8, 8, 5, 8, 3, 5, 0, 3, 0)),
        pgl.Polygon(points(0, 0, 8, 0, 8, 8, 4, 4, 0, 8)),     # non-convex
        pgl.PolygonWithHoles(
            pgl.Polygon(points(0, 0, 8, 0, 7, 5, 8, 8, 0, 8)),
            [pgl.Polygon(points(2, 2, 4, 2, 6, 6))],
        ),
        pgl.HalfplaneIntersection(halfplanes),
    ]

    canvas = pgl.Canvas().size(800, 600)
    canvas.fillOpacity("25%").strokeWidth("2px")

    for cell, shape in enumerate(shapes):
        canvas.stroke(COLORS[cell % len(COLORS)])
        canvas.fill(COLORS[(cell + 5) % len(COLORS)])
        canvas.draw(at_cell(shape, cell % COLUMNS, cell // COLUMNS))

    canvas.writeSVG("canvas_gallery.svg")
    canvas.writePDF("canvas_gallery.pdf")
    canvas.writeIPE("canvas_gallery.ipe")


if __name__ == "__main__":
    main()
