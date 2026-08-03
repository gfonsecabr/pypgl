"""Predicates: intersects, interiorsIntersect.

The Python port of pgl's `examples/example1.cpp`.

Output:
    (1,0)--(4,7) intersects (0,8)--(2,1)
    <(0,8)(1,0)(4,7)> intersects (1,0)--(4,7)
    The interiors of <(0,8)(1,0)(4,7)> and (1,0)--(4,7) do not intersect
"""

import pypgl as pgl


def main():
    p, q = pgl.Point(1, 0), pgl.Point(4, 7)
    # The fixed-size shapes accept either points or a flat coordinate list.
    s, t = pgl.Segment(p, q), pgl.Segment(0, 8, 2, 1)
    if s.intersects(t):
        print(f"{s} intersects {t}")

    tri = pgl.Triangle(p, q, t.min())
    if tri.intersects(s):
        print(f"{tri} intersects {s}")
    # The segment runs along the triangle's boundary, so the shapes meet
    # without their interiors meeting.
    if not tri.interiorsIntersect(s):
        print(f"The interiors of {tri} and {s} do not intersect")


if __name__ == "__main__":
    main()
