"""Every index pypgl takes is cyclic.

`get(i)` has always taken its index modulo the count, so a negative one counts
from the end and an out-of-range one wraps. That rule now governs every index in
the API — the accessors that reach a hole, a component, a vertex or an edge, and
the methods that name an element to erase or replace — so no index is ever out
of range and a computed one needs no bounds check.

Two cases sit outside it, both on purpose:

* an **empty** shape has no element for any index to name, so it raises
  `IndexError` (pgl's own reduction divides by the count, which is why this has
  to be checked rather than passed through); and
* `Polyline.insert(i, p)` names a position *between* vertices, of which there
  are `size() + 1` — the last being the append that a cyclic index would fold
  onto the first — so it clamps the way Python's `list.insert` does.
"""

import pytest

from pypgl import (
    Convex,
    Disk,
    Halfplane,
    HalfplaneIntersection,
    Line,
    MonotoneChain,
    OrientedLine,
    OrientedSegment,
    Point,
    Polygon,
    PolygonSet,
    PolygonWithHoles,
    Polyline,
    Ray,
    Rectangle,
    Segment,
    Triangle,
)

P = Point


def region():
    return PolygonWithHoles(
        Polygon([0, 0, 9, 0, 9, 9, 0, 9]),
        [Polygon([1, 1, 2, 1, 2, 2, 1, 2]), Polygon([5, 5, 6, 5, 6, 6, 5, 6])],
    )


def polygon_set():
    return PolygonSet(
        [
            Polygon([0, 0, 3, 0, 3, 3, 0, 3]).asPolygonWithHoles(),
            Polygon([7, 7, 9, 7, 9, 9, 7, 9]).asPolygonWithHoles(),
        ]
    )


def halfplanes():
    return Rectangle(P(0, 0), P(5, 5)).asHalfplaneIntersection()


# --- get() and [] on every shape ---------------------------------------------

EVERY_SHAPE = [
    P(1, 2),
    Segment(P(0, 0), P(4, 0)),
    OrientedSegment(P(0, 0), P(4, 0)),
    Line(P(0, 0), P(1, 1)),
    OrientedLine(P(0, 0), P(1, 1)),
    Ray(P(0, 0), P(1, 1)),
    Halfplane(P(0, 0), P(1, 0)),
    Triangle(P(0, 0), P(4, 0), P(0, 4)),
    Rectangle(P(0, 0), P(4, 4)),
    Convex([P(0, 0), P(4, 0), P(4, 4), P(0, 4)]),
    MonotoneChain([P(0, 0), P(2, 3), P(5, 1)]),
    Polyline([P(0, 0), P(2, 3), P(5, 1)]),
    Polygon([0, 0, 6, 0, 6, 6, 0, 6]),
    Disk(P(0, 0), 5),
    halfplanes(),
]


@pytest.mark.parametrize("shape", EVERY_SHAPE, ids=lambda s: type(s).__name__)
def test_get_is_cyclic_on_every_shape(shape):
    n = shape.size()
    assert n > 0
    for i in range(n):
        assert shape.get(i) == shape.get(i + n) == shape.get(i - n)
        assert shape[i] == shape.get(i)
    assert shape.get(-1) == shape.get(n - 1)
    assert shape.get(7 * n + 1) == shape.get(1)


# --- the other index accessors follow the same rule --------------------------


def test_hole_is_cyclic():
    r = region()
    n = r.holeCount()
    assert n == 2
    for i in range(n):
        assert r.hole(i) == r.hole(i + n) == r.hole(i - n)
    assert r.hole(-1) == r.hole(n - 1)
    assert r.hole(99) == r.hole(99 % n)


def test_component_is_cyclic():
    s = polygon_set()
    n = s.componentCount()
    assert n == 2
    for i in range(n):
        assert s.component(i) == s.component(i + n) == s.component(i - n)
    assert s.component(-1) == s.component(n - 1)
    assert s.component(99) == s.component(99 % n)


def test_vertex_and_edge_are_cyclic():
    k = halfplanes()
    v = k.vertexCount()
    for i in range(v):
        assert k.vertex(i) == k.vertex(i + v) == k.vertex(i - v)
    assert k.vertex(-1) == k.vertex(v - 1)
    # edge() is indexed over the half-planes, which is what it names.
    e = len(k)
    for i in range(e):
        assert k.edge(i) == k.edge(i + e) == k.edge(i - e)
    assert k.edge(-1) == k.edge(e - 1)


def test_erase_and_set_take_a_cyclic_index():
    # An out-of-range index names a real element rather than running off the end.
    r = region()
    r.eraseHole(2)  # == eraseHole(0), there being two holes
    assert r.holeCount() == 1 and r.hole(0) == region().hole(1)

    s = polygon_set()
    s.eraseComponent(-1)
    assert s.componentCount() == 1 and s.component(0) == polygon_set().component(0)

    chain = MonotoneChain([P(0, 0), P(2, 3), P(5, 1)])
    chain.erase(3)  # == erase(0)
    assert list(chain.vertices()) == [P(2, 3), P(5, 1)]

    line = Polyline([P(0, 0), P(3, 0), P(5, 5)])
    line.set(-1, P(9, 9))
    assert list(line.vertices()) == [P(0, 0), P(3, 0), P(9, 9)]
    line.set(3, P(1, 1))  # == set(0)
    assert list(line.vertices()) == [P(1, 1), P(3, 0), P(9, 9)]


# --- an empty shape has nothing to name --------------------------------------

EMPTY_CALLS = [
    ("Polygon.get", lambda: Polygon().get(0)),
    ("Polygon[]", lambda: Polygon()[0]),
    ("Convex.get", lambda: Convex().get(0)),
    ("Polyline.get", lambda: Polyline().get(0)),
    ("MonotoneChain.get", lambda: MonotoneChain().get(0)),
    ("PolygonWithHoles[]", lambda: PolygonWithHoles()[0]),
    ("PolygonSet[]", lambda: PolygonSet()[0]),
    ("hole", lambda: PolygonWithHoles(Polygon([0, 0, 9, 0, 9, 9, 0, 9])).hole(0)),
    ("eraseHole", lambda: PolygonWithHoles(Polygon([0, 0, 9, 0, 9, 9, 0, 9])).eraseHole(0)),
    ("component", lambda: PolygonSet().component(0)),
    ("eraseComponent", lambda: PolygonSet().eraseComponent(0)),
    ("MonotoneChain.erase", lambda: MonotoneChain().erase(0)),
    ("Polyline.set", lambda: Polyline().set(0, P(1, 1))),
    ("HalfplaneIntersection.vertex", lambda: HalfplaneIntersection().vertex(0)),
    ("HalfplaneIntersection.get", lambda: HalfplaneIntersection().get(0)),
]


@pytest.mark.parametrize("label, call", EMPTY_CALLS, ids=[c[0] for c in EMPTY_CALLS])
def test_indexing_an_empty_shape_raises_index_error(label, call):
    # The one case a cyclic index cannot answer: pgl's own reduction divides by
    # the count, so this has to be checked rather than passed through.
    with pytest.raises(IndexError, match="empty"):
        call()


# --- insert names a position, not an element ---------------------------------


def test_polyline_insert_clamps_like_list_insert():
    def after(index):
        line = Polyline([P(0, 0), P(3, 0), P(5, 5)])
        line.insert(index, P(9, 9))
        return list(line.vertices())

    def reference(index):
        items = [P(0, 0), P(3, 0), P(5, 5)]
        items.insert(index, P(9, 9))
        return items

    # The position range is [0, size()], and both ends clamp -- exactly as a
    # Python list behaves, including for a negative index.
    for index in (-99, -3, -2, -1, 0, 1, 2, 3, 4, 99):
        assert after(index) == reference(index), index
    # In particular size() still appends, which a cyclic index would have folded
    # onto the front.
    assert after(3)[-1] == P(9, 9)
    assert after(99)[-1] == P(9, 9)


def test_polyline_insert_works_on_an_empty_polyline():
    # There is one valid position in an empty polyline, and it is reachable from
    # any index -- unlike the accessors, which have no element to name.
    for index in (-5, 0, 5):
        line = Polyline()
        line.insert(index, P(1, 1))
        assert list(line.vertices()) == [P(1, 1)]


def test_polyline_insert_of_several_vertices_clamps_too():
    line = Polyline([P(0, 0), P(3, 0)])
    line.insert(99, [P(9, 9), P(10, 10)])
    assert list(line.vertices()) == [P(0, 0), P(3, 0), P(9, 9), P(10, 10)]
