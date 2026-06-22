"""pypgl - Python bindings for the Pangolin (pgl) exact geometry library.

Shapes are exact: coordinates are rationals, accepted as ``int``,
``fractions.Fraction``, or ``"a/b"`` strings, and returned as ``Fraction``.
``float`` is rejected so the exactness contract is never silently broken.
"""

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
)

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
]


# --- Pythonic sugar added in the thin Python layer (cheap here, not in C++) ---

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
):
    _add_indexing(_cls)

del _cls
