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
    Disk,
    Triangulation,
    ShapeTree,
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
    sortAround,
    hilbertSort,
    polyominoes,
    polyominoesUpTo,
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
    "Disk",
    "Triangulation",
    "ShapeTree",
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
    "sortAround",
    "hilbertSort",
    "polyominoes",
    "polyominoesUpTo",
]


# --- Pythonic sugar added in the thin Python layer (cheap here, not in C++) ---
#
# Triangulation and ShapeTree are deliberately absent from every loop below:
# unlike the fixed-extent shapes, neither has contains(Point)/pointInside/
# index/get to hang `in` or indexing off of -- ShapeTree's own has()/
# __contains__/__len__/__iter__ (bound directly in bind_shapetree.cpp) already
# give it container semantics (membership, not point-in-shape). Both do get
# _repr_svg_ further down, since Canvas.draw() accepts them like any other
# shape.

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
):
    _add_indexing(_cls)

del _cls


# --- Inline SVG rendering in Jupyter / IPython ---
#
# `Canvas._repr_svg_` lets a canvas display itself; wrapping a single shape in a
# one-shot Canvas gives every shape the same inline rendering, which is the main
# usability win for a geometry library in a notebook.

#: Side length, in pixels, of the one-shot canvas used to render a single shape
#: inline in a notebook. Half of pgl's 1000x1000 default so a shape does not
#: dominate the cell. Reassign ``pypgl.REPR_SVG_SIZE = ...`` to change it; a
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
    Disk,
    # Triangulation and ShapeTree are not "shapes" (see the loops above), but
    # Canvas.draw() accepts them just like every bound shape, so the same
    # one-shot rendering applies here too.
    Triangulation,
    ShapeTree,
):
    _cls._repr_svg_ = _shape_repr_svg_

del _cls
