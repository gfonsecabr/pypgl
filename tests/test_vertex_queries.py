"""pointInside, verticesContain, and index.

pointInside returns an exact interior point; verticesContain / index search a
shape's defining points. They are bound on every shape that defines them — all
but Point, which has no interior and whose `index` searches its two coordinates.
"""

import pypgl


# Shapes that expose the vertex/interior queries (everything but Point).
QUERY_SHAPES = ("Segment", "OrientedSegment", "Line", "OrientedLine", "Ray",
                "Halfplane", "Triangle", "Rectangle", "Convex")


def test_query_methods_present_where_expected():
    for name in QUERY_SHAPES:
        cls = getattr(pypgl, name)
        for m in ("pointInside", "verticesContain", "index"):
            assert hasattr(cls, m), f"{name}.{m} missing"
    # Point has index (over coordinates) but no interior / vertex membership.
    assert hasattr(pypgl.Point, "index")
    assert not hasattr(pypgl.Point, "pointInside")
    assert not hasattr(pypgl.Point, "verticesContain")


def test_point_inside_is_exact_and_contained():
    t = pypgl.Triangle(0, 0, 4, 0, 0, 3)
    inside = t.pointInside()
    assert t.contains(inside)
    assert t.interiorContains(inside)
    c = pypgl.Convex([pypgl.Point(0, 0), pypgl.Point(4, 0),
                      pypgl.Point(4, 4), pypgl.Point(0, 4)])
    assert c.interiorContains(c.pointInside())


def test_point_inside_of_a_non_convex_polygon():
    # pgl gained a non-convex pointInside (it cuts a diagonal or an ear at a
    # convex vertex), so an L-shaped polygon -- whose vertex average falls in the
    # notch, outside the polygon -- still gets an exact interior witness.
    P = pypgl.Point
    L = pypgl.Polygon([P(0, 0), P(4, 0), P(4, 1), P(1, 1), P(1, 4), P(0, 4)])
    assert not L.isConvex()
    assert L.interiorContains(L.pointInside())
    # Polygon still has no verticesContain (pgl does not define it there).
    assert not hasattr(pypgl.Polygon, "verticesContain")


def test_vertices_contain():
    s = pypgl.Segment(0, 0, 4, 6)
    assert s.verticesContain(pypgl.Point(0, 0))
    assert s.verticesContain(pypgl.Point(4, 6))
    assert not s.verticesContain(pypgl.Point(2, 3))   # midpoint is not a vertex
    tri = pypgl.Triangle(0, 0, 4, 0, 0, 3)
    assert tri.verticesContain(pypgl.Point(4, 0))
    assert not tri.verticesContain(pypgl.Point(1, 1))


def test_index_of_defining_point():
    s = pypgl.Segment(0, 0, 4, 6)
    assert s.index(pypgl.Point(0, 0)) == 0
    assert s.index(pypgl.Point(4, 6)) == 1
    assert s.index(pypgl.Point(9, 9)) is None
    c = pypgl.Convex([pypgl.Point(0, 0), pypgl.Point(4, 0),
                      pypgl.Point(4, 4), pypgl.Point(0, 4)])
    assert c.index(pypgl.Point(4, 4)) == 2
    assert c.index(pypgl.Point(5, 5)) is None


def test_point_index_searches_coordinates():
    p = pypgl.Point(3, 7)
    assert p.index(3) == 0
    assert p.index(7) == 1
    assert p.index(5) is None


# --- cyclic indexing: shape[i] delegates to pgl's get -----------------------

def test_cyclic_indexing_wraps_modulo_size():
    t = pypgl.Triangle(0, 0, 4, 0, 0, 3)
    assert t[0] == pypgl.Point(0, 0)
    assert t[-1] == pypgl.Point(0, 3)        # negative wraps from the end
    assert t[3] == t[0]                       # large index wraps modulo 3
    assert t[7] == t[1]
    assert t.get(4) == t[1]                   # get is what [] calls


def test_cyclic_indexing_on_convex():
    c = pypgl.Convex([pypgl.Point(0, 0), pypgl.Point(4, 0),
                      pypgl.Point(4, 3), pypgl.Point(0, 3)])
    assert c[5] == c[1]
    assert c[-1] == pypgl.Point(0, 3)
    assert c.get(6) == c[2]


def test_iteration_still_terminates():
    # `get` never raises, so iteration must come from __iter__, not __getitem__.
    t = pypgl.Triangle(0, 0, 4, 0, 0, 3)
    assert list(t) == [pypgl.Point(0, 0), pypgl.Point(4, 0), pypgl.Point(0, 3)]
    assert len(list(iter(t))) == 3


# --- every shape is indexable ----------------------------------------------

ALL_SHAPES = ("Point", "Segment", "OrientedSegment", "Line", "OrientedLine",
              "Ray", "Halfplane", "Triangle", "Rectangle", "Convex")


def test_all_shapes_have_size_get_and_are_iterable():
    instances = {
        "Point": pypgl.Point(2, 3),
        "Segment": pypgl.Segment(0, 0, 4, 6),
        "OrientedSegment": pypgl.OrientedSegment(0, 0, 4, 6),
        "Line": pypgl.Line(0, 0, 4, 6),
        "OrientedLine": pypgl.OrientedLine(0, 0, 4, 6),
        "Ray": pypgl.Ray(0, 0, 4, 6),
        "Halfplane": pypgl.Halfplane(0, 0, 4, 6),
        "Triangle": pypgl.Triangle(0, 0, 4, 0, 0, 3),
        "Rectangle": pypgl.Rectangle(0, 0, 4, 3),
        "Convex": pypgl.Convex([pypgl.Point(0, 0), pypgl.Point(4, 0),
                                pypgl.Point(4, 3), pypgl.Point(0, 3)]),
    }
    for name, s in instances.items():
        n = s.size()
        assert n == len(s) > 0, name
        assert list(s) == [s[i] for i in range(n)], name   # iteration matches indexing
        assert s[n] == s[0], name                           # cyclic wrap


def test_point_indexes_its_coordinates():
    from fractions import Fraction
    p = pypgl.Point(2, 3)
    assert len(p) == 2
    assert p[0] == Fraction(2)
    assert p[1] == Fraction(3)
    assert p[-1] == Fraction(3)
    assert list(p) == [Fraction(2), Fraction(3)]


def test_line_family_indexes_defining_points():
    ln = pypgl.Line(0, 0, 4, 6)
    assert len(ln) == 2
    assert ln[0] == pypgl.Point(0, 0)
    assert ln[1] == pypgl.Point(4, 6)
    ray = pypgl.Ray(1, 1, 5, 5)
    assert list(ray) == [pypgl.Point(1, 1), pypgl.Point(5, 5)]
