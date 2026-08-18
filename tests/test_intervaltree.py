"""IntervalTree: a mutable one-dimensional index over bounded shapes.

It stores each shape's bounding-box projection onto one axis. That buys two
things a ShapeTree does not have: insert/erase keep the tree balanced, and the
*projection* query family answers from the intervals alone -- a different
question from the exact two-dimensional one, not a faster approximation of it.
The unprefixed family prunes on the projection and then applies the exact
predicate, so it agrees with ShapeTree shape for shape.
"""

import pytest

from pypgl import (
    IntervalTree,
    IntervalTreeY,
    Line,
    Point,
    Rectangle,
    Segment,
    ShapeTree,
    Triangle,
)


def _shapes():
    return [
        Rectangle(Point(0, 0), Point(2, 2)),
        Rectangle(Point(1, 10), Point(3, 12)),      # x overlaps, y far away
        Triangle(Point(8, 0), Point(9, 0), Point(8, 1)),
    ]


# --- container behavior -----------------------------------------------------

def test_a_tree_stores_a_mix_of_shapes():
    tree = IntervalTree(_shapes())
    assert len(tree) == tree.size() == 3
    assert not tree.empty()
    assert Rectangle(Point(0, 0), Point(2, 2)) in tree
    assert tree.has(Rectangle(Point(0, 0), Point(2, 2)))
    assert Rectangle(Point(5, 5), Point(6, 6)) not in tree
    assert sorted(map(repr, tree.shapes())) == sorted(map(repr, tree))


def test_insert_and_erase_keep_it_balanced_and_correct():
    tree = IntervalTree()
    assert tree.empty()
    tree.insert(Segment(0, 0, 1, 1))
    tree.insert(Segment(0, 0, 1, 1))            # equal intervals stored apart
    assert tree.size() == 2
    assert tree.erase(Segment(0, 0, 1, 1))
    assert tree.size() == 1
    assert not tree.erase(Segment(5, 5, 6, 6))


def test_an_unbounded_shape_has_no_interval_either_way():
    tree = IntervalTree()
    with pytest.raises(Exception):
        tree.insert(Line(Point(0, 0), Point(1, 1)))
    # Unlike a ShapeTree, which prunes a query against stored boxes and so
    # accepts an unbounded one, every query here is *projected* first -- and an
    # unbounded shape has no box to project.
    assert ShapeTree(_shapes()).countIntersecting(Line(Point(0, 0), Point(1, 1))) == 1
    with pytest.raises(Exception):
        IntervalTree(_shapes()).countIntersecting(Line(Point(0, 0), Point(1, 1)))


# --- the projection family answers a one-dimensional question ---------------

def test_projection_queries_ignore_the_other_axis():
    tree = IntervalTree(_shapes())
    query = Rectangle(Point(0, 0), Point(2, 2))
    # Two shapes' x-ranges meet the query's, even though one of them is ten
    # units above it and does not touch it in the plane.
    assert tree.countProjectionsIntersecting(query) == 2
    assert len(tree.reportProjectionsIntersecting(query)) == 2
    assert not tree.emptyProjectionsIntersecting(query)
    assert tree.countIntersecting(query) == 1            # the exact answer


def test_the_axis_is_a_choice_of_class():
    shapes = _shapes()
    query = Rectangle(Point(0, 0), Point(2, 2))
    # The same pair of shapes overlaps on x but not on y.
    assert IntervalTree(shapes).countProjectionsIntersecting(query) == 2
    assert IntervalTreeY(shapes).countProjectionsIntersecting(query) == 2


def test_containment_of_projections_needs_the_whole_interval_inside():
    tree = IntervalTree(_shapes())
    wide = Rectangle(Point(-1, -1), Point(4, 20))
    assert tree.countProjectionsContainedIn(wide) == 2
    assert len(tree.reportProjectionsContainedIn(wide)) == 2
    assert tree.emptyProjectionsContainedIn(Rectangle(Point(100, 100), Point(101, 101)))


def test_touching_at_an_endpoint_counts_as_meeting():
    tree = IntervalTree([Rectangle(Point(0, 0), Point(2, 2))])
    assert tree.countProjectionsIntersecting(Rectangle(Point(2, 50), Point(3, 51))) == 1


# --- the exact family agrees with ShapeTree ---------------------------------

@pytest.mark.parametrize(
    "query",
    [
        Rectangle(Point(0, 0), Point(2, 2)),
        Rectangle(Point(-1, -1), Point(20, 20)),
        Point(1, 1),
        Segment(0, 0, 9, 9),
    ],
)
def test_the_unprefixed_family_matches_a_shapetree(query):
    shapes = _shapes()
    interval, spatial = IntervalTree(shapes), ShapeTree(shapes)
    assert interval.countIntersecting(query) == spatial.countIntersecting(query)
    assert interval.countContainedIn(query) == spatial.countContainedIn(query)
    assert interval.emptyIntersecting(query) == spatial.emptyIntersecting(query)
    assert interval.emptyContainedIn(query) == spatial.emptyContainedIn(query)
    assert sorted(map(repr, interval.reportIntersecting(query))) == sorted(
        map(repr, spatial.reportIntersecting(query))
    )
    assert sorted(map(repr, interval.reportContainedIn(query))) == sorted(
        map(repr, spatial.reportContainedIn(query))
    )
