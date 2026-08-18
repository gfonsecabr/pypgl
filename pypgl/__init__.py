"""pypgl - Python bindings for the Pangolin (pgl) exact geometry library.

Shapes are exact: coordinates are rationals, accepted as ``int``,
``fractions.Fraction``, or ``"a/b"`` strings, and returned as ``Fraction``.
``float`` is rejected so the exactness contract is never silently broken.
"""

from importlib.metadata import PackageNotFoundError, version as _version

from ._pgl import (
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
    IntervalTree,
    IntervalTreeY,
    Graph,
    Arrangement,
    ArrangementGraph,
    VertexId,
    HalfedgeId,
    FaceId,
    Canvas,
    Transformation,
    findIntersections,
    findCrossings,
    bruteForceIntersections,
    bruteForceCrossings,
    detectIntersections,
    detectCrossings,
    convexHull,
    convexHullExtended,
    smallestEnclosingDisk,
    closestPair,
    regularizedUnionOf,
    sortAround,
    hilbertSort,
    polyominoes,
    polyominoesUpTo,
    polyominoRegions,
    polyominoRegionsUpTo,
)

try:
    __version__ = _version("pypgl")
except PackageNotFoundError:  # not installed (e.g. running from a source tree)
    __version__ = "0+unknown"

__all__ = [
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
    "IntervalTree",
    "IntervalTreeY",
    "Graph",
    "Arrangement",
    "ArrangementGraph",
    "VertexId",
    "HalfedgeId",
    "FaceId",
    "Canvas",
    "Transformation",
    "findIntersections",
    "findCrossings",
    "bruteForceIntersections",
    "bruteForceCrossings",
    "detectIntersections",
    "detectCrossings",
    "convexHull",
    "convexHullExtended",
    "smallestEnclosingDisk",
    "closestPair",
    "regularizedUnionOf",
    "sortAround",
    "hilbertSort",
    "polyominoes",
    "polyominoesUpTo",
    "polyominoRegions",
    "polyominoRegionsUpTo",
]


# --- Pythonic sugar added in the thin Python layer (cheap here, not in C++) ---
#
# Triangulation, ShapeTree, IntervalTree, Graph and Arrangement are deliberately
# absent from every loop below: unlike the fixed-extent shapes, none of them has
# contains(Point)/pointInside/index/get to hang `in` or indexing off of. The
# container ones bind their own has()/__contains__/__len__/__iter__ in C++, over
# what they actually hold -- stored shapes for the two trees, vertices for a
# graph -- which is membership, not point-in-shape. Triangulation and ShapeTree
# do get _repr_svg_ further down, since Canvas.draw() accepts them like any
# other shape; the rest are not drawable.

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
PolygonWithHoles.__len__ = lambda self: self.vertexCount()
PolygonWithHoles.__getitem__ = lambda self, index: self.vertices()[index % self.vertexCount()]
PolygonWithHoles.__iter__ = lambda self: iter(self.vertices())

# PolygonSet is the same story one level up: C++ iterates its *components*, the
# regions it is made of, and gives it no size()/get() either. Python flattens
# the vertices of every ring of every component, so a set reads like every other
# pypgl shape; componentCount() / component(i) / components() reach the
# components, and holes stay reachable through each of those.
PolygonSet.__len__ = lambda self: self.vertexCount()
PolygonSet.__getitem__ = lambda self, index: self.vertices()[index % self.vertexCount()]
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
    # Triangulation and ShapeTree are not "shapes" (see the loops above), but
    # Canvas.draw() accepts them just like every bound shape, so the same
    # one-shot rendering applies here too.
    Triangulation,
    ShapeTree,
):
    _cls._repr_svg_ = _shape_repr_svg_

del _cls
