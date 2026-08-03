"""Canvas basics: styling and drawing.

The Python port of pgl's `examples/example2.cpp`. pgl's stream API
(`canvas << stroke("green") << shape`) has no Python equivalent, so every
stream operation is a method instead; they return the canvas, so they chain.

A style command applies to the *current* style, and only shapes drawn
afterwards pick it up -- which is what lets one canvas hold two differently
coloured triangles.

Output: example2.svg
"""

import pypgl as pgl


def main():
    canvas = pgl.Canvas()
    canvas.draw(pgl.Point(0, 0))

    tri = pgl.Triangle(-1, -1, 0, 2, 1, -2)
    canvas.stroke("green").draw(tri)
    canvas.stroke("blue").draw(2 * tri)
    canvas.writeSVG("example2.svg")


if __name__ == "__main__":
    main()
