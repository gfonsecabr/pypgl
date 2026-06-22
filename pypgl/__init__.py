"""pypgl - Python bindings for the Pangolin (pgl) exact geometry library.

Shapes are exact: coordinates are rationals, accepted as ``int``,
``fractions.Fraction``, or ``"a/b"`` strings, and returned as ``Fraction``.
``float`` is rejected so the exactness contract is never silently broken.
"""

from ._pgl import Point, Segment

__all__ = ["Point", "Segment"]


# --- Pythonic sugar added in the thin Python layer (cheap here, not in C++) ---

def _shape_contains(self, item):
    """``point in shape`` maps to ``shape.contains(point)``.

    Only the unambiguous point-in-shape case is exposed via ``in``; shape vs
    shape relations stay explicit method calls to avoid confusion.
    """
    if isinstance(item, Point):
        return self.contains(item)
    return NotImplemented


for _cls in (Point, Segment):
    _cls.__contains__ = _shape_contains


# A segment is iterable / indexable over its two endpoints.
Segment.__iter__ = lambda self: iter(self.vertices())
Segment.__len__ = lambda self: 2
Segment.__getitem__ = lambda self, index: self.vertices()[index]

del _cls
