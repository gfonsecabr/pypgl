"""Transformation: an affine map of the plane applied to a shape via `*`.

Unlike every shape, Transformation carries no point/label type of its own --
only the matrix-entry type, bound over the module's single numeric
instantiation (ERational) like everything else. `t * shape` applies t
(transformation always on the left, matching pgl's own operator*); `t1 * t2`
composes two transformations, t2 first. Rectangle and Disk have no `*`
overload (a general affine map turns a rectangle into a parallelogram and a
disk into an ellipse, which those classes cannot represent), so applying one
raises TypeError -- the runtime equivalent of pgl's compile error.
"""

from fractions import Fraction

import pytest

import pypgl
from pypgl import (
    Convex,
    Disk,
    Halfplane,
    Line,
    OrientedLine,
    OrientedSegment,
    Point,
    Polygon,
    Ray,
    Rectangle,
    Segment,
    Transformation,
    Triangle,
)


def test_transformation_importable_and_in_all():
    assert hasattr(pypgl, "Transformation")
    assert "Transformation" in pypgl.__all__


# --- construction / factories ------------------------------------------------

def test_default_is_identity():
    assert Transformation() == Transformation.identity()
    t = Transformation()
    assert (t.a(), t.b(), t.c(), t.d(), t.tx(), t.ty()) == (1, 0, 0, 1, 0, 0)


def test_explicit_matrix_entries():
    t = Transformation(1, 2, 3, 4, 5, 6)
    assert (t.a(), t.b(), t.c(), t.d(), t.tx(), t.ty()) == (1, 2, 3, 4, 5, 6)
    # tx/ty default to 0.
    t2 = Transformation(1, 0, 0, 1)
    assert (t2.tx(), t2.ty()) == (0, 0)


def test_translation():
    t = Transformation.translation(3, 4)
    assert t * Point(1, 1) == Point(4, 5)


def test_scaling_uniform_and_nonuniform():
    assert Transformation.scaling(2) * Point(3, 4) == Point(6, 8)
    assert Transformation.scaling(2, 3) * Point(1, 1) == Point(2, 3)


def test_rotation90_matches_shape_rotated90():
    p = Point(3, 4)
    for k in range(-3, 5):
        assert Transformation.rotation90(k) * p == p.rotated90(k)
    assert Transformation.rotation90() * p == p.rotated90(1)  # default k=1


def test_shear_and_reflection():
    assert Transformation.shearX(2) * Point(1, 3) == Point(7, 3)     # x + 2*y
    assert Transformation.shearY(2) * Point(3, 1) == Point(3, 7)     # y + 2*x
    assert Transformation.reflectionX() * Point(2, 5) == Point(2, -5)
    assert Transformation.reflectionY() * Point(2, 5) == Point(-2, 5)


def test_float_scalar_rejected():
    with pytest.raises(TypeError):
        Transformation.translation(1.5, 0)
    with pytest.raises(TypeError):
        Transformation(1.0, 0, 0, 1)


# --- determinant / invertibility / inverse -----------------------------------

def test_determinant_and_invertibility():
    assert Transformation.identity().determinant() == 1
    assert Transformation.identity().isInvertible()
    singular = Transformation(1, 1, 2, 2)  # rows dependent -> det 0
    assert singular.determinant() == 0
    assert not singular.isInvertible()


def test_inverse_undoes_transformation():
    t = Transformation(2, 1, 1, 3, 5, -2)
    p = Point(7, -3)
    assert t.inverse() * (t * p) == p
    assert t.inverse().a() == Fraction(3, 5)  # sanity: exact Fraction result


def test_inverse_of_singular_raises():
    # pgl's own zero-determinant guard is only an assert() (compiled out in
    # the release build pypgl ships), so this is checked explicitly in the
    # binding rather than left to pgl -- see bind_transformation.cpp.
    singular = Transformation(1, 1, 2, 2)
    assert not singular.isInvertible()
    with pytest.raises(ValueError):
        singular.inverse()


# --- composition --------------------------------------------------------------

def test_composition_order_matches_sequential_application():
    t1 = Transformation.translation(10, 0)
    t2 = Transformation.rotation90(1)
    p = Point(1, 0)
    assert (t1 * t2) * p == t1 * (t2 * p)
    assert isinstance(t1 * t2, Transformation)


def test_identity_is_composition_neutral():
    t = Transformation(2, 0, 0, 3, 1, 1)
    identity = Transformation.identity()
    assert t * identity == t
    assert identity * t == t


# --- equality / repr -----------------------------------------------------------

def test_equality():
    assert Transformation(1, 0, 0, 1) == Transformation.identity()
    assert Transformation(1, 0, 0, 1) != Transformation.translation(1, 0)


def test_repr_contains_matrix_entries():
    t = Transformation.translation(3, 4)
    r = repr(t)
    assert "3" in r and "4" in r


# --- application to every supported shape -------------------------------------

def _shapes():
    return {
        "Point": Point(1, 2),
        "Segment": Segment(Point(0, 0), Point(2, 2)),
        "OrientedSegment": OrientedSegment(Point(0, 0), Point(2, 2)),
        "Line": Line(Point(0, 0), Point(1, 1)),
        "OrientedLine": OrientedLine(Point(0, 0), Point(1, 1)),
        "Ray": Ray(Point(0, 0), Point(1, 1)),
        "Halfplane": Halfplane(Point(0, 0), Point(1, 0)),
        "Triangle": Triangle(Point(0, 0), Point(4, 0), Point(0, 4)),
        "Convex": Convex([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]),
        "Polygon": Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)]),
    }


@pytest.mark.parametrize("name", list(_shapes().keys()))
def test_transformation_applies_to_every_supported_shape(name):
    shape = _shapes()[name]
    t = Transformation.translation(10, 0)
    result = t * shape
    assert type(result).__name__ == name


def test_transformation_translation_moves_triangle_vertices():
    tri = Triangle(Point(0, 0), Point(4, 0), Point(0, 4))
    moved = Transformation.translation(1, 1) * tri
    assert set(moved.vertices()) == {Point(1, 1), Point(5, 1), Point(1, 5)}


def test_transformation_rotation_on_halfplane_preserves_orientation():
    h = Halfplane(Point(0, 0), Point(1, 0))
    assert h.contains(Point(0, 1))
    rotated = Transformation.rotation90(1) * h
    # A 90-degree rotation has positive determinant, so it should not need to
    # swap source/target to preserve the interior side.
    assert rotated.contains(Transformation.rotation90(1) * Point(0, 1))


# --- Rectangle / Disk are excluded ---------------------------------------------

def test_rectangle_and_disk_raise_type_error():
    t = Transformation.translation(1, 1)
    with pytest.raises(TypeError):
        t * Rectangle(Point(0, 0), Point(1, 1))
    with pytest.raises(TypeError):
        t * Disk(Point(0, 0), 1)


def test_shape_times_transformation_is_not_supported():
    # Only Transformation * shape is defined (transformation on the left),
    # mirroring pgl's own operator* -- the reflected order is not bound.
    t = Transformation.translation(1, 1)
    with pytest.raises(TypeError):
        Point(0, 0) * t
