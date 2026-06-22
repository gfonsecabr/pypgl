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


# Shapes with a fixed or enumerable vertex set are iterable / indexable over
# their vertices (segments expose their two endpoints).
def _add_vertex_iteration(cls, count=None):
    cls.__iter__ = lambda self: iter(self.vertices())
    cls.__getitem__ = lambda self, index: self.vertices()[index]
    cls.__len__ = (lambda self: count) if count is not None \
        else (lambda self: len(self.vertices()))


_add_vertex_iteration(Segment, 2)
_add_vertex_iteration(OrientedSegment, 2)
_add_vertex_iteration(Triangle, 3)
_add_vertex_iteration(Rectangle, 4)
_add_vertex_iteration(Convex)

del _cls
