"""pypgl - Python bindings for the Pangolin (pgl) exact geometry library.

Shapes are exact: coordinates are rationals, accepted as ``int``,
``fractions.Fraction``, or ``"a/b"`` strings, and returned as ``Fraction``.
``float`` is rejected so the exactness contract is never silently broken.
"""

from importlib.metadata import PackageNotFoundError, version as _version

from ._pgl import (
    PreconditionError,
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
    MonotoneChain,
    Polyline,
    Polygon,
    PolygonWithHoles,
    PolygonSet,
    HalfplaneIntersection,
    Disk,
    Triangulation,
    ShapeTree,
    BitMatrix,
    GridAdjacency,
    IntervalTree,
    IntervalTreeY,
    Graph,
    Arrangement,
    PointListArrangement,
    DiskArrangement,
    DiskListArrangement,
    ArrangementGraph,
    VertexId,
    HalfedgeId,
    FaceId,
    Canvas,
    Text,
    TextFit,
    Transformation,
    findIntersections,
    findCrossings,
    findInteriorIntersections,
    detectIntersections,
    detectCrossings,
    detectInteriorIntersections,
    convexHull,
    convexHullExtended,
    smallestEnclosingDisk,
    closestPair,
    regularizedUnionOf,
    sortPoints,
    sortDistinctPoints,
    sortAround,
    hilbertSort,
    polyominoes,
    polyominoesUpTo,
    polyominoRegions,
    polyominoRegionsUpTo,
    findEmptyTriangles,
    findEmptyQuadrilaterals,
    findEmptyConvexQuadrilaterals,
    innerRaster,
    outerRaster,
    voronoiDiagram,
    farthestVoronoiDiagram,
    powerDiagram,
    _valueHash,
)

try:
    __version__ = _version("pypgl")
except PackageNotFoundError:  # not installed (e.g. running from a source tree)
    __version__ = "0+unknown"

__all__ = [
    "PreconditionError",
    "Point",
    "Segment",
    "OrientedSegment",
    "Line",
    "OrientedLine",
    "Ray",
    "Halfplane",
    "Triangle",
    "Rectangle",
    "Convex",
    "MonotoneChain",
    "Polyline",
    "Polygon",
    "PolygonWithHoles",
    "PolygonSet",
    "HalfplaneIntersection",
    "Disk",
    "Triangulation",
    "ShapeTree",
    "BitMatrix",
    "GridAdjacency",
    "IntervalTree",
    "IntervalTreeY",
    "Graph",
    "Arrangement",
    "PointListArrangement",
    "DiskArrangement",
    "DiskListArrangement",
    "ArrangementGraph",
    "VertexId",
    "HalfedgeId",
    "FaceId",
    "Canvas",
    "Text",
    "TextFit",
    "Transformation",
    "findIntersections",
    "findCrossings",
    "findInteriorIntersections",
    "detectIntersections",
    "detectCrossings",
    "detectInteriorIntersections",
    "convexHull",
    "convexHullExtended",
    "smallestEnclosingDisk",
    "closestPair",
    "regularizedUnionOf",
    "sortPoints",
    "sortDistinctPoints",
    "sortAround",
    "hilbertSort",
    "polyominoes",
    "polyominoesUpTo",
    "polyominoRegions",
    "polyominoRegionsUpTo",
    "findEmptyTriangles",
    "findEmptyQuadrilaterals",
    "findEmptyConvexQuadrilaterals",
    "innerRaster",
    "outerRaster",
    "voronoiDiagram",
    "farthestVoronoiDiagram",
    "powerDiagram",
    "FrozenConvex",
    "FrozenMonotoneChain",
    "FrozenPolyline",
    "FrozenPolygon",
    "FrozenPolygonWithHoles",
    "FrozenPolygonSet",
    "FrozenHalfplaneIntersection",
]


# --- Pythonic sugar added in the thin Python layer (cheap here, not in C++) ---
#
# Triangulation, ShapeTree, BitMatrix, IntervalTree, Graph and the four
# Arrangement classes are deliberately absent from every loop below: unlike the fixed-extent shapes, none
# of them has contains(Point)/pointInside/index/get to hang `in` or indexing off
# of. The container ones bind their own has()/__contains__/__len__/__iter__ in
# C++, over what they actually hold -- stored shapes for the two trees, vertices
# for a graph, set cells for a bit matrix -- which is membership, not
# point-in-shape. (A BitMatrix does have pointInside() and a contains(), but the
# first is the center of its first set cell rather than an accessor, and the
# second takes another matrix; `point in matrix` asks whether that *cell* is
# set.) Triangulation, ShapeTree and BitMatrix do get _repr_svg_ further down,
# since Canvas.draw() accepts them like any other shape; the rest are not
# drawable.

def _shape_contains(self, item):
    """``point in shape`` maps to ``shape.contains(point)``.

    Only the unambiguous point-in-shape case is exposed via ``in``; shape vs
    shape relations stay explicit method calls to avoid confusion.
    """
    if isinstance(item, Point):
        return self.contains(item)
    return NotImplemented


for _cls in (
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
    MonotoneChain,
    Polyline,
    Polygon,
    PolygonWithHoles,
    PolygonSet,
    HalfplaneIntersection,
    Disk,
):
    _cls.__contains__ = _shape_contains


# Every shape is iterable / indexable over its defining points (or, for Point,
# its two coordinates), backed by pgl's `size` and cyclic `get`. Indexing is
# cyclic: `shape[i]` wraps modulo the count (negative indices count from the
# end) instead of raising. Iteration goes through __iter__ over range(size()),
# so it terminates even though get() never raises.
def _add_indexing(cls):
    cls.__len__ = lambda self: self.size()
    cls.__getitem__ = lambda self, index: self.get(index)
    cls.__iter__ = lambda self: (self.get(i) for i in range(self.size()))


for _cls in (
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
    MonotoneChain,
    Polyline,
    Polygon,
    Disk,
    # HalfplaneIntersection's size()/get() are over its *half-planes*, not over
    # points, which is exactly what pgl indexes too -- so len(region) is the
    # constraint count and iterating yields Halfplane objects. Its implicit
    # corners, which are generally not representable in the coordinate type of
    # the half-planes that bound them, are reached through vertexCount() /
    # vertex(i) / vertices() instead.
    HalfplaneIntersection,
):
    _add_indexing(_cls)

del _cls


# PolygonWithHoles has neither size() nor get(): its vertices are spread over
# its rings rather than forming one indexable sequence, and C++ deliberately
# gives it vertexCount() instead of size() so that a name shared with a polygon
# never means two different things in generic code. Iterating one in C++ gives
# its *holes*.
#
# Python goes the other way and iterates the vertices, so a region reads like
# every other pypgl shape -- `len(shape)` is a vertex count and iterating gives
# points, here just flattened across the rings (outer boundary first). The holes
# stay reachable through holeCount() / hole(i) / holes(). Indexing is cyclic
# like every other shape's, and materializes the vertex list, so prefer
# vertices() when walking one repeatedly.
def _flattened_getitem(self, index):
    """Cyclic indexing over the flattened vertices, the same convention get()
    uses everywhere else -- including raising IndexError, rather than dividing
    by zero, when there are no vertices at all."""
    vertices = self.vertices()
    if not vertices:
        raise IndexError(f"cannot index an empty {type(self).__name__}")
    return vertices[index % len(vertices)]


PolygonWithHoles.__len__ = lambda self: self.vertexCount()
PolygonWithHoles.__getitem__ = _flattened_getitem
PolygonWithHoles.__iter__ = lambda self: iter(self.vertices())

# PolygonSet is the same story one level up: C++ iterates its *components*, the
# regions it is made of, and gives it no size()/get() either. Python flattens
# the vertices of every ring of every component, so a set reads like every other
# pypgl shape; componentCount() / component(i) / components() reach the
# components, and holes stay reachable through each of those.
PolygonSet.__len__ = lambda self: self.vertexCount()
PolygonSet.__getitem__ = _flattened_getitem
PolygonSet.__iter__ = lambda self: iter(self.vertices())


# --- Inline SVG rendering in Jupyter / IPython ---
#
# `Canvas._repr_svg_` lets a canvas display itself; wrapping a single shape in a
# one-shot Canvas gives every shape the same inline rendering, which is the main
# usability win for a geometry library in a notebook.

#: Side length, in pixels, of the one-shot canvas used to render a single shape
#: inline in a notebook. Smaller than the Canvas default (800x800) so a shape
#: does not dominate the cell. Reassign ``pypgl.REPR_SVG_SIZE = ...`` to change it; a
#: Canvas you build yourself is unaffected (it honors its own ``size``).
REPR_SVG_SIZE = 500

Canvas._repr_svg_ = lambda self: self.toSVG()


def _shape_repr_svg_(self):
    return Canvas().size(REPR_SVG_SIZE, REPR_SVG_SIZE).draw(self).toSVG()


for _cls in (
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
    MonotoneChain,
    Polyline,
    Polygon,
    PolygonWithHoles,
    PolygonSet,
    HalfplaneIntersection,
    Disk,
    # Triangulation, ShapeTree and BitMatrix are not "shapes" (see the loops
    # above), but Canvas.draw() accepts them just like every bound shape, so the
    # same one-shot rendering applies here too -- and to a Text, which a canvas
    # draws the same way.
    Triangulation,
    ShapeTree,
    BitMatrix,
    Text,
):
    _cls._repr_svg_ = _shape_repr_svg_

del _cls



# --- Frozen shapes: the hashable counterparts of the seven mutable ones ---
#
# Convex, MonotoneChain, Polyline, Polygon, PolygonWithHoles, PolygonSet and
# HalfplaneIntersection all mutate in place (`shape += point`, `insert`,
# `rotate90`, ...), so none of them binds __hash__: Python requires a key's hash
# to stay put while it is a key, and a shape that can change value underneath a
# dict cannot promise that.
#
# `shape.frozen()` answers with an independent *copy* whose class refuses every
# mutator, so its value is fixed for its whole lifetime and it can be hashed.
# Each frozen class is a Python **subclass** of the shape it freezes, which is
# what keeps it a first-class shape rather than a wrapper: the underlying C++
# object is unchanged, so `isinstance(frozen, Polygon)` holds, every bound
# method takes one as an argument (`triangle.contains(frozen)`), and
# `canvas.draw(frozen)` works. Equality, ordering and repr are inherited, so a
# frozen shape compares equal to the mutable one it came from -- exactly as
# `frozenset({1}) == {1}`, the unhashable counterpart being the mutable one.
#
# The hash is pgl's own std::hash, reached through the private `_valueHash`
# (src/bind_frozen.cpp). That is the hash which agrees with pgl's operator==,
# and the agreement is the whole contract: a Polyline equals its own reverse, a
# closed one equals its own rotations, a Convex and a MonotoneChain ignore the
# order they were given, and a PolygonWithHoles and a PolygonSet canonicalize
# their rings and components. Hashing the vertex list in Python would have to
# re-derive every one of those canonical forms, and getting a single one wrong
# would silently lose dict entries.
#
# Everything a frozen shape computes comes back as the ordinary mutable type --
# `frozen.convexHull()` is a Convex, `frozen + point` a Polygon. Freezing is
# about being a key, not a parallel algebra to compute in; freeze a result again
# when you want to key on that too.

#: Mutating methods shared by all seven: the five in-place transforms and the
#: four in-place operators.
_FROZEN_SHARED_MUTATORS = (
    "rotate90",
    "scaleUpX",
    "scaleUpY",
    "scaleDownX",
    "scaleDownY",
    "__iadd__",
    "__isub__",
    "__imul__",
    "__itruediv__",
)

#: Each shape's own mutators, beyond the shared ones. This mapping is what makes
#: the frozen classes safe, so tests/test_frozen.py pins it from both sides: every
#: name here must really mutate, and every *other* public method must leave the
#: value alone. A mutator added upstream and missed here would not raise -- it
#: would silently change a live dict key.
_FROZEN_OWN_MUTATORS = {
    "Convex": ("insert",),
    "MonotoneChain": ("insert", "erase"),
    "Polyline": ("insert", "set", "pushBack", "flip"),
    "Polygon": ("untangle",),
    "PolygonWithHoles": ("addHole", "eraseHole"),
    "PolygonSet": ("addComponent", "eraseComponent"),
    "HalfplaneIntersection": ("insert",),
}

#: The non-mutating way to say the same thing, named in the error message.
_FROZEN_ALTERNATIVES = {
    "rotate90": "rotated90()",
    "scaleUpX": "scaledUpX()",
    "scaleUpY": "scaledUpY()",
    "scaleDownX": "scaledDownX()",
    "scaleDownY": "scaledDownY()",
    "__iadd__": "a + b",
    "__isub__": "a - b",
    "__imul__": "a * k",
    "__itruediv__": "a / k",
}


def _frozen_hash(self):
    """The value hash, from pgl's std::hash for this shape type.

    A plain Python function rather than ``__hash__ = _valueHash``: a nanobind
    function is not a descriptor, so assigning one straight to ``__hash__``
    would call it with no arguments.
    """
    return _valueHash(self)


def _frozen_refuse(cls_name, method):
    """Build the replacement for one mutating method on one frozen class."""
    alternative = _FROZEN_ALTERNATIVES.get(method)
    hint = (
        f" Use {alternative}, which returns a new shape."
        if alternative
        else " Call it on thawed(), which is a mutable copy."
    )

    def refuse(self, *args, **kwargs):
        raise TypeError(f"{cls_name} is immutable: {method}() would change it.{hint}")

    refuse.__name__ = method
    refuse.__qualname__ = f"{cls_name}.{method}"
    refuse.__doc__ = f"Unsupported on a frozen shape: {method}() mutates.{hint}"
    return refuse


class FrozenConvex(Convex):
    """An immutable, hashable :class:`Convex`, usable as a dict key or set member."""

    __hash__ = _frozen_hash

    def frozen(self):
        """Return self: the shape is already frozen."""
        return self

    def thawed(self):
        """An independent, mutable :class:`Convex` copy of this shape."""
        return Convex(self)


class FrozenMonotoneChain(MonotoneChain):
    """An immutable, hashable :class:`MonotoneChain`, usable as a dict key."""

    __hash__ = _frozen_hash

    def frozen(self):
        """Return self: the shape is already frozen."""
        return self

    def thawed(self):
        """An independent, mutable :class:`MonotoneChain` copy of this shape."""
        return MonotoneChain(self)


class FrozenPolyline(Polyline):
    """An immutable, hashable :class:`Polyline`, usable as a dict key."""

    __hash__ = _frozen_hash

    def frozen(self):
        """Return self: the shape is already frozen."""
        return self

    def thawed(self):
        """An independent, mutable :class:`Polyline` copy of this shape."""
        return Polyline(self)


class FrozenPolygon(Polygon):
    """An immutable, hashable :class:`Polygon`, usable as a dict key."""

    __hash__ = _frozen_hash

    def frozen(self):
        """Return self: the shape is already frozen."""
        return self

    def thawed(self):
        """An independent, mutable :class:`Polygon` copy of this shape."""
        return Polygon(self)


class FrozenPolygonWithHoles(PolygonWithHoles):
    """An immutable, hashable :class:`PolygonWithHoles`, usable as a dict key."""

    __hash__ = _frozen_hash

    def frozen(self):
        """Return self: the shape is already frozen."""
        return self

    def thawed(self):
        """An independent, mutable :class:`PolygonWithHoles` copy of this shape."""
        return PolygonWithHoles(self)


class FrozenPolygonSet(PolygonSet):
    """An immutable, hashable :class:`PolygonSet`, usable as a dict key."""

    __hash__ = _frozen_hash

    def frozen(self):
        """Return self: the shape is already frozen."""
        return self

    def thawed(self):
        """An independent, mutable :class:`PolygonSet` copy of this shape."""
        return PolygonSet(self)


class FrozenHalfplaneIntersection(HalfplaneIntersection):
    """An immutable, hashable :class:`HalfplaneIntersection`, usable as a dict key."""

    __hash__ = _frozen_hash

    def frozen(self):
        """Return self: the shape is already frozen."""
        return self

    def thawed(self):
        """An independent, mutable :class:`HalfplaneIntersection` copy."""
        return HalfplaneIntersection(self)


#: Each mutable shape paired with the class that freezes it.
_FROZEN_CLASSES = {
    Convex: FrozenConvex,
    MonotoneChain: FrozenMonotoneChain,
    Polyline: FrozenPolyline,
    Polygon: FrozenPolygon,
    PolygonWithHoles: FrozenPolygonWithHoles,
    PolygonSet: FrozenPolygonSet,
    HalfplaneIntersection: FrozenHalfplaneIntersection,
}


def _install_frozen(base, frozen):
    # Refuse every mutator on the frozen subclass. The C++ object underneath is
    # an ordinary mutable one -- these overrides are the whole of what makes it
    # immutable, which is why the name list is tested rather than trusted.
    #
    # The shared list is filtered by what the base actually has: a
    # HalfplaneIntersection scales but does not take `*=` or `/=`, so two of the
    # nine are absent there. The shape's own mutators must all exist, since a
    # typo in that list would leave a real mutator reachable.
    for _method in _FROZEN_SHARED_MUTATORS:
        if hasattr(base, _method):
            setattr(frozen, _method, _frozen_refuse(frozen.__name__, _method))
    for _method in _FROZEN_OWN_MUTATORS[base.__name__]:
        assert hasattr(base, _method), f"{base.__name__} has no {_method} to refuse"
        setattr(frozen, _method, _frozen_refuse(frozen.__name__, _method))

    def _frozen_of(self):
        return frozen(self)

    _frozen_of.__doc__ = (
        f"An independent, immutable {frozen.__name__} copy of this shape: hashable, "
        "and so usable as a dict key or set member. Later changes to this shape do "
        "not affect it."
    )
    _frozen_of.__name__ = "frozen"
    _frozen_of.__qualname__ = f"{base.__name__}.frozen"
    base.frozen = _frozen_of


for _base, _frozen in _FROZEN_CLASSES.items():
    _install_frozen(_base, _frozen)

del _base, _frozen
