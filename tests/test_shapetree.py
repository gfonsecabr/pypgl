"""ShapeTree: a static spatial index over a mix of shapes.

Unlike every other bound type, ShapeTree stores pgl's type-erased Shape
wrapper internally (see the casters.h caster and the "Load-bearing design
decisions" note in CLAUDE.md) so that a single tree can mix, say, a Triangle
and a Disk -- but that wrapper never reaches Python: every method here takes
and returns ordinary pypgl shape objects. It is also not a fixed-extent
"shape" (no contains(Point)/pointInside/index/get), so -- like Triangulation
-- it opts out of the point-in-shape/indexing sugar and instead gets its own
container semantics (__len__/__iter__/__contains__ as exact membership).

Only bounded shapes (Point, Segment, OrientedSegment, Triangle, Rectangle,
Convex, Polygon, Disk) can be stored; Line/OrientedLine/Ray/Halfplane have no
bbox() and raise on insert, but remain valid as *queries*.
"""

import pytest

import pypgl
from pypgl import (
    Canvas,
    Convex,
    Disk,
    Halfplane,
    Line,
    Point,
    Rectangle,
    Segment,
    ShapeTree,
    Triangle,
)


def _triangle():
    return Triangle(Point(0, 0), Point(10, 0), Point(0, 10))


def _mixed_shapes():
    return [
        Point(0, 0),
        Point(10, 0),
        Point(0, 10),
        _triangle(),
        Disk(Point(20, 20), 5),
    ]


# --- importability, construction --------------------------------------------

def test_shapetree_importable_and_in_all():
    assert hasattr(pypgl, "ShapeTree")
    assert "ShapeTree" in pypgl.__all__


def test_empty_tree():
    t = ShapeTree()
    assert t.empty()
    assert t.size() == 0
    assert len(t) == 0
    assert t.shapes() == []
    assert list(t) == []
    assert t.boundingBoxes() == []


def test_construct_from_mixed_shapes():
    t = ShapeTree(_mixed_shapes(), leaf_size=2)
    assert t.size() == 5
    assert not t.empty()
    assert len(t) == 5


def test_construct_default_leaf_size():
    t = ShapeTree(_mixed_shapes())
    assert t.size() == 5


# --- storage / container semantics ------------------------------------------

def test_shapes_returns_stored_shapes_with_concrete_types():
    t = ShapeTree(_mixed_shapes())
    kinds = sorted(type(s).__name__ for s in t.shapes())
    assert kinds == ["Disk", "Point", "Point", "Point", "Triangle"]


def test_iteration_yields_concrete_shapes():
    t = ShapeTree(_mixed_shapes())
    kinds = sorted(type(s).__name__ for s in t)
    assert kinds == ["Disk", "Point", "Point", "Point", "Triangle"]


def test_contains_is_exact_membership_not_geometric():
    tri = _triangle()
    t = ShapeTree([tri, Point(20, 20)])
    assert tri in t
    assert t.contains(tri)
    # A point that lies inside the triangle is not a *stored* triangle.
    assert Point(1, 1) not in t
    assert not t.contains(Point(1, 1))


def test_repr():
    t = ShapeTree(_mixed_shapes())
    assert repr(t) == "ShapeTree(size=5)"


# --- mutation ----------------------------------------------------------------

def test_insert_and_erase():
    t = ShapeTree([Point(0, 0)])
    seg = Segment(Point(1, 1), Point(2, 2))
    t.insert(seg)
    assert t.size() == 2
    assert seg in t

    assert t.erase(seg)
    assert t.size() == 1
    assert seg not in t

    # Erasing something not stored reports False and leaves the tree alone.
    assert not t.erase(seg)
    assert t.size() == 1


def test_rebuild_preserves_shapes():
    t = ShapeTree(_mixed_shapes(), leaf_size=1)
    before = sorted(map(repr, t.shapes()))
    t.rebuild()
    assert sorted(map(repr, t.shapes())) == before
    t.rebuild(leaf_size=3)
    assert sorted(map(repr, t.shapes())) == before


def test_insert_unbounded_shape_raises():
    t = ShapeTree([Point(0, 0)])
    with pytest.raises(RuntimeError):
        t.insert(Line(Point(0, 0), Point(1, 1)))
    # The failed insert must not have left a partial element behind.
    assert t.size() == 1


# --- spatial queries -----------------------------------------------------------

def test_intersecting_and_contained_in_a_window():
    t = ShapeTree(_mixed_shapes())
    window = Rectangle(Point(-1, -1), Point(11, 11))

    assert t.countIntersecting(window) == 4  # the 3 points + the triangle
    assert not t.emptyIntersecting(window)
    assert {repr(s) for s in t.reportIntersecting(window)} == {
        repr(s) for s in [Point(0, 0), Point(10, 0), Point(0, 10), _triangle()]
    }

    assert t.countContainedIn(window) == 4
    assert not t.emptyContainedIn(window)

    far = Rectangle(Point(500, 500), Point(600, 600))
    assert t.countIntersecting(far) == 0
    assert t.emptyIntersecting(far)
    assert t.countContainedIn(far) == 0
    assert t.emptyContainedIn(far)


def test_query_by_unbounded_shape():
    t = ShapeTree(_mixed_shapes())
    # A horizontal line through y=0 crosses the two points on that line and
    # the triangle (which has an edge on it), but not the far-away disk.
    line = Line(Point(-100, 0), Point(100, 0))
    hit_kinds = sorted(type(s).__name__ for s in t.reportIntersecting(line))
    assert hit_kinds == ["Point", "Point", "Triangle"]


def test_nearest_neighbor():
    t = ShapeTree(_mixed_shapes())
    nearest = t.nearestNeighbor(Point(0, 0))
    assert nearest is not None
    # (0,0) is itself stored (as both a Point and a Triangle vertex), so the
    # nearest shape must be at squared distance 0.
    assert nearest.squaredDistance(Point(0, 0)) == 0


def test_nearest_neighbor_on_empty_tree_is_none():
    t = ShapeTree()
    assert t.nearestNeighbor(Point(0, 0)) is None


def test_nearest_neighbor_can_be_a_disk():
    # Disk's squaredDistance isn't templated on ResultNumber like every other
    # shape's, so nearestNeighbor exercises the wrapper's double-returning
    # fallback whenever the closest stored element happens to be a Disk.
    t = ShapeTree([Point(100, 100), Disk(Point(0, 0), 2)])
    nearest = t.nearestNeighbor(Point(0, 0))
    assert isinstance(nearest, Disk)


def test_nearest_neighbor_l1_and_linf():
    t = ShapeTree([Point(0, 0), Point(10, 0), Point(0, 10)])
    # (1, 1) is closer to the origin under every one of the three metrics here.
    assert t.nearestNeighborL1(Point(1, 1)) == Point(0, 0)
    assert t.nearestNeighborLInf(Point(1, 1)) == Point(0, 0)


def test_nearest_neighbor_l1_and_linf_can_differ_from_squared():
    # Under L1, (10, 0) and (0, 10) are equidistant (10) from (5, 5), both
    # farther than under a metric that favors axis-aligned proximity; pick
    # points where L1 and Euclidean nearest-neighbor actually disagree.
    t = ShapeTree([Point(9, 9), Point(0, 12)])
    q = Point(0, 0)
    # squaredDistance: 9²+9²=162 vs 0²+12²=144 -> (0,12) wins.
    assert t.nearestNeighbor(q) == Point(0, 12)
    # L1: 9+9=18 vs 0+12=12 -> (0,12) wins too here, so use LInf instead.
    # LInf: max(9,9)=9 vs max(0,12)=12 -> (9,9) wins under LInf.
    assert t.nearestNeighborLInf(q) == Point(9, 9)


def test_nearest_neighbor_l1_linf_on_empty_tree_is_none():
    t = ShapeTree()
    assert t.nearestNeighborL1(Point(0, 0)) is None
    assert t.nearestNeighborLInf(Point(0, 0)) is None


def test_bounding_boxes_nonempty_for_nonempty_tree():
    t = ShapeTree(_mixed_shapes(), leaf_size=1)
    boxes = t.boundingBoxes()
    assert boxes
    assert all(isinstance(b, Rectangle) for b in boxes)
    # The first (root) box encloses every stored shape's own bbox.
    root = boxes[0]
    for s in t.shapes():
        assert root.contains(s.bbox())


# --- argument type checking ---------------------------------------------------

def test_non_shape_argument_raises_type_error():
    t = ShapeTree([Point(0, 0)])
    with pytest.raises(TypeError):
        t.insert("not a shape")
    with pytest.raises(TypeError):
        t.countIntersecting(42)


# --- Canvas / inline rendering --------------------------------------------------

def test_canvas_draw():
    t = ShapeTree(_mixed_shapes(), leaf_size=1)
    svg = Canvas().draw(t).toSVG()
    assert "<rect" in svg


def test_repr_svg():
    t = ShapeTree(_mixed_shapes())
    svg = t._repr_svg_()
    assert svg.startswith("<?xml") or "<svg" in svg
