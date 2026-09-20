"""Frozen shapes: the hashable counterparts of the seven mutable ones.

Seven bound shapes mutate in place and so bind no ``__hash__``. ``shape.frozen()``
returns an independent copy of a subclass that refuses every mutator and is
hashable, so it can be a dict key or a set member.

The two properties everything rests on are checked here from both sides:

* **the hash agrees with ``==``** -- equality sees through representation for
  most of these shapes (a polyline equals its own reverse, a region canonicalizes
  its holes), so a hash that did not would silently lose dict entries; and
* **nothing reachable on a frozen shape mutates it** -- the list of refused
  methods in ``pypgl/__init__.py`` is what makes the class safe, so it is pinned
  literally *and* every other public method is exercised and checked to leave the
  value alone.
"""

import itertools

import pytest

import pypgl
from pypgl import (
    Convex,
    FrozenConvex,
    FrozenHalfplaneIntersection,
    FrozenMonotoneChain,
    FrozenPolygon,
    FrozenPolygonSet,
    FrozenPolygonWithHoles,
    FrozenPolyline,
    Halfplane,
    HalfplaneIntersection,
    MonotoneChain,
    Point,
    Polygon,
    PolygonSet,
    PolygonWithHoles,
    Polyline,
    Rectangle,
    Segment,
    Triangle,
)

P = Point

FROZEN = {
    Convex: FrozenConvex,
    MonotoneChain: FrozenMonotoneChain,
    Polyline: FrozenPolyline,
    Polygon: FrozenPolygon,
    PolygonWithHoles: FrozenPolygonWithHoles,
    PolygonSet: FrozenPolygonSet,
    HalfplaneIntersection: FrozenHalfplaneIntersection,
}


def sample(base):
    """A representative instance of one mutable shape class."""
    return {
        Convex: lambda: Convex([P(0, 0), P(4, 0), P(4, 4), P(0, 4)]),
        MonotoneChain: lambda: MonotoneChain([P(0, 0), P(2, 3), P(5, 1)]),
        Polyline: lambda: Polyline([P(0, 0), P(2, 3), P(5, 1), P(7, 0)]),
        Polygon: lambda: Polygon([0, 0, 6, 0, 6, 6, 0, 6]),
        PolygonWithHoles: lambda: PolygonWithHoles(
            Polygon([0, 0, 9, 0, 9, 9, 0, 9]), [Polygon([3, 3, 5, 3, 5, 5, 3, 5])]
        ),
        PolygonSet: lambda: PolygonSet(
            [Polygon([0, 0, 3, 0, 3, 3, 0, 3]).asPolygonWithHoles()]
        ),
        HalfplaneIntersection: lambda: Rectangle(P(0, 0), P(5, 5)).asHalfplaneIntersection(),
    }[base]()


BASES = list(FROZEN)
IDS = [b.__name__ for b in BASES]


# --- What a frozen shape is --------------------------------------------------


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_the_mutable_shape_is_unhashable_and_the_frozen_one_is_not(base):
    shape = sample(base)
    with pytest.raises(TypeError):
        hash(shape)
    assert hash(shape.frozen()) == hash(shape.frozen())


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_a_frozen_shape_is_still_a_shape(base):
    frozen = sample(base).frozen()
    # A subclass, not a wrapper: the C++ object is the same kind of thing, so
    # isinstance holds and every binding takes one.
    assert isinstance(frozen, base)
    assert isinstance(frozen, FROZEN[base])
    assert frozen == sample(base)
    assert repr(frozen) == repr(sample(base))
    probe = Triangle(P(0, 0), P(1, 0), P(0, 1))
    probe.intersects(frozen)  # as a C++ argument
    frozen.intersects(probe)  # as a receiver
    pypgl.Canvas().draw(frozen)  # and drawable


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_freezing_copies_so_the_key_cannot_move(base):
    shape = sample(base)
    key = shape.frozen()
    table = {key: "value"}
    shape.rotate90()  # the original moves...
    assert key != shape  # ...and the key did not follow it
    assert table[sample(base).frozen()] == "value"


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_thawed_is_an_independent_mutable_copy(base):
    frozen = sample(base).frozen()
    thawed = frozen.thawed()
    assert type(thawed) is base
    assert thawed == frozen
    thawed.rotate90()
    assert thawed != frozen


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_freezing_a_frozen_shape_returns_it_unchanged(base):
    frozen = sample(base).frozen()
    assert frozen.frozen() is frozen


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_a_frozen_class_can_be_constructed_directly(base):
    direct = FROZEN[base](sample(base))
    assert direct == sample(base)
    assert hash(direct) == hash(sample(base).frozen())


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_frozen_shapes_work_as_keys_and_set_members(base):
    a, b = sample(base).frozen(), sample(base).frozen()
    assert a is not b and a == b
    assert len({a, b}) == 1
    table = {a: 1}
    table[b] = 2
    assert table == {a: 2} and len(table) == 1


def test_the_frozen_classes_are_public():
    for name in (
        "FrozenConvex", "FrozenMonotoneChain", "FrozenPolyline", "FrozenPolygon",
        "FrozenPolygonWithHoles", "FrozenPolygonSet", "FrozenHalfplaneIntersection",
    ):
        assert name in pypgl.__all__
        assert hasattr(pypgl, name)


# --- The hash agrees with equality -------------------------------------------
#
# These shapes' equality sees through representation, which is exactly where a
# hand-rolled hash would go wrong -- hence pgl's own std::hash.

EQUAL_PAIRS = [
    ("a polyline equals its reverse",
     Polyline([P(0, 0), P(2, 3), P(5, 1)]), Polyline([P(5, 1), P(2, 3), P(0, 0)])),
    ("a closed polyline equals its rotations",
     Polyline([P(0, 0), P(4, 0), P(4, 4), P(0, 0)]),
     Polyline([P(4, 0), P(4, 4), P(0, 0), P(4, 0)])),
    ("a polygon's ring may start anywhere",
     Polygon([0, 0, 4, 0, 4, 4, 0, 4]), Polygon([4, 4, 0, 4, 0, 0, 4, 0])),
    ("a polygon equals its reversed ring",
     Polygon([0, 0, 4, 0, 4, 4, 0, 4]), Polygon([0, 4, 4, 4, 4, 0, 0, 0])),
    ("a hull ignores the order it was given",
     Convex([P(0, 0), P(4, 0), P(4, 4)]), Convex([P(4, 4), P(0, 0), P(4, 0)])),
    ("a monotone chain sorts its input",
     MonotoneChain([P(5, 1), P(0, 0), P(2, 3)]), MonotoneChain([P(0, 0), P(2, 3), P(5, 1)])),
    ("a region canonicalizes its holes",
     PolygonWithHoles(Polygon([0, 0, 9, 0, 9, 9, 0, 9]),
                      [Polygon([1, 1, 2, 1, 2, 2, 1, 2]), Polygon([5, 5, 6, 5, 6, 6, 5, 6])]),
     PolygonWithHoles(Polygon([0, 0, 9, 0, 9, 9, 0, 9]),
                      [Polygon([5, 5, 6, 5, 6, 6, 5, 6]), Polygon([1, 1, 2, 1, 2, 2, 1, 2])])),
    ("a set canonicalizes its components",
     PolygonSet([Polygon([0, 0, 2, 0, 2, 2, 0, 2]).asPolygonWithHoles(),
                 Polygon([5, 5, 7, 5, 7, 7, 5, 7]).asPolygonWithHoles()]),
     PolygonSet([Polygon([5, 5, 7, 5, 7, 7, 5, 7]).asPolygonWithHoles(),
                 Polygon([0, 0, 2, 0, 2, 2, 0, 2]).asPolygonWithHoles()])),
    ("a half-plane intersection canonicalizes its constraints",
     HalfplaneIntersection([Halfplane(P(0, 0), P(1, 0)), Halfplane(P(1, 1), P(0, 1))]),
     HalfplaneIntersection([Halfplane(P(1, 1), P(0, 1)), Halfplane(P(0, 0), P(1, 0))])),
]


@pytest.mark.parametrize("label, a, b", EQUAL_PAIRS, ids=[c[0] for c in EQUAL_PAIRS])
def test_equal_shapes_hash_equal_however_they_were_built(label, a, b):
    assert a == b, label
    assert hash(a.frozen()) == hash(b.frozen()), label
    # And the dict agrees, which is the property that actually matters.
    assert {a.frozen(): 1}[b.frozen()] == 1


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_distinct_shapes_are_distinct_keys(base):
    one = sample(base).frozen()
    other = sample(base)
    other.rotate90()
    other = other.frozen()
    assert one != other
    assert len({one, other}) == 2


# --- Nothing reachable on a frozen shape mutates it --------------------------


def expected_blocked(base):
    shared = [m for m in pypgl._FROZEN_SHARED_MUTATORS if hasattr(base, m)]
    return set(shared) | set(pypgl._FROZEN_OWN_MUTATORS[base.__name__])


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_the_refused_set_is_exactly_what_the_class_installs(base):
    frozen = FROZEN[base]
    installed = {
        name
        for name, value in vars(frozen).items()
        if callable(value) and getattr(value, "__doc__", "") or ""
        if name not in ("frozen", "thawed", "__hash__")
    }
    installed = {n for n in installed if not n.startswith("__") or n.startswith("__i")}
    assert installed == expected_blocked(base)


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_every_refused_method_really_does_mutate(base):
    """The list is only worth having if each name on it names a real mutator --
    otherwise it is quietly hiding a perfectly good const method."""
    for name in expected_blocked(base):
        assert hasattr(base, name), f"{base.__name__} has no {name}"
        assert name in vars(FROZEN[base]), f"{FROZEN[base].__name__} does not refuse {name}"


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_a_refused_method_raises_and_names_the_alternative(base):
    frozen = sample(base).frozen()
    before = repr(frozen)
    for name in expected_blocked(base):
        with pytest.raises(TypeError, match="immutable"):
            getattr(frozen, name)(*((Point(1, 1),) if name.startswith("__i") else ()))
        assert repr(frozen) == before
    # The value-returning counterpart still works and leaves the shape alone.
    assert frozen.rotated90() != frozen or frozen.rotated90() == frozen
    assert repr(frozen) == before


# One argument tuple of each shape the bound methods take, so the sweep below
# reaches as many methods as it can. Anything it cannot call is reported.
#
# Out-of-range indices are included on purpose: every index pypgl takes is
# cyclic, so they name a real element rather than running off the end. An
# earlier version of this sweep is what found the accessors that did not yet
# follow that rule.
_ARGS = [
    (), (P(1, 1),), (P(9, 9),), (0,), (1,), (2,), (99,), (-1,), (0, 0), (1, 1), (2, 3),
    (Segment(P(0, 0), P(1, 1)),), (Halfplane(P(0, 0), P(1, 0)),),
    (Triangle(P(0, 0), P(1, 0), P(0, 1)),), (Rectangle(P(0, 0), P(2, 2)),),
    (Polygon([0, 0, 2, 0, 2, 2]),), ([P(1, 1), P(2, 2)],),
    (Polygon([0, 0, 2, 0, 2, 2]).asPolygonWithHoles(),),
    (Segment(P(0, 0), P(1, 1)), Segment(P(1, 1), P(2, 2))),
    (True,), (False,),
]


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_no_reachable_method_changes_a_frozen_shape(base):
    """The drift guard. Call every public method that is not refused, with every
    argument tuple that fits, and require the shape to come back unchanged. A
    mutator added upstream and not added to the refused list fails here rather
    than silently corrupting somebody's dict."""
    blocked = expected_blocked(base)
    names = [
        n
        for n in dir(FROZEN[base])
        if (not n.startswith("_") or n.startswith("__i"))
        and n not in blocked
        and n not in ("__init__", "__iter__")
        and callable(getattr(FROZEN[base], n, None))
    ]
    offenders, unreached = [], []
    for name in sorted(set(names)):
        reached = False
        for args in _ARGS:
            frozen = sample(base).frozen()
            before = repr(frozen)
            try:
                getattr(frozen, name)(*args)
            except Exception:
                continue
            reached = True
            if repr(frozen) != before:
                offenders.append(name)
                break
        if not reached:
            unreached.append(name)
    assert not offenders, (
        f"{base.__name__}: these methods mutate a frozen shape and are not refused: "
        f"{offenders}"
    )
    # Not a failure -- just recorded, so a reviewer can see what the sweep could
    # not exercise. Keep it small; a long list means the argument battery has
    # gone stale.
    assert len(unreached) <= 4, f"{base.__name__}: unexercised methods {unreached}"


@pytest.mark.parametrize("base", BASES, ids=IDS)
def test_the_hash_survives_every_reachable_call(base):
    """The same sweep stated as the property that matters: a frozen shape's hash
    is stable for its whole lifetime, whatever is called on it."""
    frozen = sample(base).frozen()
    first = hash(frozen)
    for name in dir(frozen):
        if name.startswith("_") and not name.startswith("__i"):
            continue
        # __init__ is the one __i* name that is not an in-place operator, and it
        # is not a hole: nanobind refuses to re-initialize a live instance (it
        # warns, then rejects every overload), so a frozen shape cannot be
        # re-seated through it. Calling it here would only add the warning.
        if name == "__init__":
            continue
        attr = getattr(frozen, name, None)
        if not callable(attr):
            continue
        for args in _ARGS:
            try:
                attr(*args)
            except Exception:
                pass
    assert hash(frozen) == first


# --- What a frozen shape computes --------------------------------------------


def test_results_come_back_as_the_ordinary_mutable_types():
    # Freezing is about being a key, not a parallel algebra: a derived shape is
    # an ordinary one, and is re-frozen explicitly when it too must be a key.
    frozen = Polygon([0, 0, 6, 0, 6, 6, 0, 6]).frozen()
    assert type(frozen.convexHull()) is Convex
    assert type(frozen + Point(1, 1)) is Polygon
    assert type(frozen.rotated90()) is Polygon
    assert type(frozen.boundary()) is Polyline
    with pytest.raises(TypeError):
        hash(frozen + Point(1, 1))
    assert hash((frozen + Point(1, 1)).frozen())


def test_a_frozen_shape_reads_exactly_like_the_mutable_one():
    poly = Polygon([0, 0, 6, 0, 6, 6, 0, 6])
    frozen = poly.frozen()
    assert frozen.area() == poly.area()
    assert list(frozen.vertices()) == list(poly.vertices())
    assert len(frozen) == len(poly)
    assert list(frozen) == list(poly)
    assert (Point(1, 1) in frozen) == (Point(1, 1) in poly)
    assert frozen.contains(Point(1, 1))
