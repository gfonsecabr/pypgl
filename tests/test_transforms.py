"""Arithmetic operators and rigid/axis transforms.

Fixed-size shapes are immutable and hashable: their operators return new shapes,
so `+=` rebinds and never mutates a shape that is a live dict key. The
variable-size Convex is mutable (O(1) in-place translation) and therefore
unhashable, mirroring Python's list/tuple split.
"""

from fractions import Fraction

import pytest

import pypgl


FIXED_SHAPES = ("Point", "Segment", "OrientedSegment", "Line", "OrientedLine",
                "Ray", "Halfplane", "Triangle", "Rectangle")


# --- Point arithmetic ----------------------------------------------------

def test_point_arithmetic_exact():
    p = pypgl.Point(2, 3)
    q = pypgl.Point(4, 5)
    assert p + q == pypgl.Point(6, 8)
    assert p - q == pypgl.Point(-2, -2)
    assert -p == pypgl.Point(-2, -3)
    assert p * 3 == pypgl.Point(6, 9)
    assert 3 * p == pypgl.Point(6, 9)
    assert p / 2 == pypgl.Point(1, Fraction(3, 2))


# --- translation and scaling of fixed shapes -----------------------------

def test_segment_translate_and_scale():
    s = pypgl.Segment(2, 3, 4, 5)
    p = pypgl.Point(1, 2)
    assert s + p == pypgl.Segment(3, 5, 5, 7)
    assert p + s == s + p                    # both operand orders
    assert s - p == pypgl.Segment(1, 1, 3, 3)
    assert s * 10 == pypgl.Segment(20, 30, 40, 50)
    assert 10 * s == s * 10
    assert s / 2 == pypgl.Segment(1, Fraction(3, 2), 2, Fraction(5, 2))


def test_operators_present_on_every_fixed_shape():
    for name in FIXED_SHAPES:
        cls = getattr(pypgl, name)
        for op in ("__add__", "__sub__", "__mul__", "__rmul__", "__truediv__"):
            assert hasattr(cls, op), f"{name}.{op} missing"


def test_float_scalar_rejected():
    with pytest.raises(TypeError):
        pypgl.Point(1, 1) * 1.5
    with pytest.raises(TypeError):
        pypgl.Segment(0, 0, 1, 1) / 0.5


# --- value-returning transforms ------------------------------------------

def test_rotated90_and_axis_scaling():
    s = pypgl.Segment(2, 3, 4, 5)
    assert s.rotated90() == s.rotated90(1)            # default k = 1
    assert s.rotated90(4) == s                        # full turn is identity
    assert s.scaledUpX(3) == pypgl.Segment(6, 3, 12, 5)
    assert s.scaledUpY(3) == pypgl.Segment(2, 9, 4, 15)
    assert s.scaledDownX(2) == pypgl.Segment(1, 3, 2, 5)
    assert s.scaledDownY(2) == pypgl.Segment(2, Fraction(3, 2), 4, Fraction(5, 2))


def test_transforms_present_on_every_shape():
    for name in FIXED_SHAPES + ("Convex",):
        cls = getattr(pypgl, name)
        for m in ("rotated90", "scaledUpX", "scaledUpY", "scaledDownX", "scaledDownY"):
            assert hasattr(cls, m), f"{name}.{m} missing"


# --- immutability of fixed shapes ----------------------------------------

def test_fixed_shapes_are_hashable():
    assert len({pypgl.Point(1, 2), pypgl.Point(1, 2)}) == 1
    assert len({pypgl.Segment(0, 0, 1, 1), pypgl.Segment(0, 0, 1, 1)}) == 1
    assert len({pypgl.Rectangle(0, 0, 4, 3), pypgl.Rectangle(0, 0, 4, 3)}) == 1


def test_iadd_rebinds_without_corrupting_dict_key():
    s = pypgl.Segment(2, 3, 4, 5)
    d = {s: "label"}
    moved = s
    moved += pypgl.Point(1, 2)        # rebinds `moved`; the dict key is untouched
    assert s == pypgl.Segment(2, 3, 4, 5)          # original unchanged
    assert moved == pypgl.Segment(3, 5, 5, 7)      # new value
    assert d[pypgl.Segment(2, 3, 4, 5)] == "label"  # key still findable


# --- Convex: mutable and unhashable --------------------------------------

def _square():
    return pypgl.Convex([pypgl.Point(0, 0), pypgl.Point(4, 0),
                         pypgl.Point(4, 4), pypgl.Point(0, 4)])


def test_convex_in_place_translation_keeps_identity():
    c = _square()
    before = id(c)
    c += pypgl.Point(10, 10)
    assert id(c) == before                 # same object, mutated in place
    assert c == pypgl.Convex([pypgl.Point(10, 10), pypgl.Point(14, 10),
                              pypgl.Point(14, 14), pypgl.Point(10, 14)])


def test_convex_value_returning_operator_is_a_copy():
    c = _square()
    moved = c + pypgl.Point(10, 10)
    assert moved is not c
    assert c == _square()                  # original untouched


def test_convex_in_place_scale_and_transforms():
    c = _square()
    c *= 2
    assert c == pypgl.Convex([pypgl.Point(0, 0), pypgl.Point(8, 0),
                              pypgl.Point(8, 8), pypgl.Point(0, 8)])
    assert c.rotate90() is None            # in-place mutator returns None
    # rotated90 is the value-returning form
    assert isinstance(_square().rotated90(), pypgl.Convex)


def test_convex_is_unhashable():
    c = _square()
    with pytest.raises(TypeError):
        hash(c)
    with pytest.raises(TypeError):
        {c}
