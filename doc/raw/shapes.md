<img align="left" src="figures/logo.png" width="23%"/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/logotextdark.svg"/>
  <img alt="Pangolin: Plane Geometry Library" src="figures/logotext.svg" width="65%"/>
</picture>

<!-- [![Tests](https://github.com/gfonsecabr/pgl/actions/workflows/tests.yml/badge.svg)](https://github.com/gfonsecabr/pgl/actions/workflows/tests.yml)
[![Standard](https://img.shields.io/badge/C%2B%2B-20/23/26-rgb(10,66,158).svg)](https://en.wikipedia.org/wiki/C%2B%2B#Standardization) -->
[![License](https://img.shields.io/badge/license-MIT-rgb(216,134,42).svg)](https://opensource.org/licenses/MIT)
<!-- [![Benchmarks](https://img.shields.io/badge/benchmarks-online-rgb(21,153,135).svg)](https://gfonsecabr.github.io/pgl/benchmarks/index.html) -->


⚠️ **Work in Progress**: This library is still under construction and contains **bugs and missing features**. Use in production environments is not recommended.


## Shapes

The following shapes are supported by Pangolin:

##### 0-dimensional shapes:
- [`Point`](#point): A point in the plane.

##### 1-dimensional shapes:
- [`Segment`](#segment): Unoriented straight line segment.
- [`OrientedSegment`](#oriented-segment): Oriented straight line segment.
- [`Line`](#line) Infinite straight line.
- [`OrientedLine`](#oriented-line) Infinite oriented straight line.
- [`Ray`](#ray) Half-line.
- [`Polyline`](#polyline) Open polygonal chain, possibly self-intersecting.
- [`MonotoneChain`](#monotonechain) Weakly x-monotone polygonal chain.

##### 2-dimensional shapes:
- [`Halfplane`](#half-plane) A straight line and all points on one side of it.
- [`Triangle`](#triangle) Unoriented triangle.
- [`Rectangle`](#rectangle) Axis-aligned rectangle.
- [`Disk`](#disk) A circle with its interior.
- [`Polygon`](#polygon) Simple polygon.
- [`Convex`](#convex) Convex polygon.
- [`PolygonWithHoles`](#polygon-with-holes) Simple polygon minus a set of disjoint polygonal holes.
- [`PolygonSet`](#polygon-set) A set of regions with pairwise disjoint interiors.
- [`HalfplaneIntersection`](#halfplane-intersection) Intersection of half-planes; convex but possibly unbounded or empty.


There are many [predicates](shape_methods.md#predicates) and [other methods](shape_methods.md) supported by all shapes, such as `intersects`, `contains`, `squaredDistance`, `distanceL1`, translation, and scaling.
Shapes may be degenerate, for example when some of their defining points are equal. Degenerate shapes may safely be constructed, and are often constructed by the default constructor that sets all points to the origin. See [Degeneracies](#degeneracies) for what they then mean.

Every shape can be built straight from coordinates, with no `Point` per vertex. The fixed-size shapes take them as arguments — `pgl.Segment(1, 2, 3, 4)`, `pgl.Triangle(0, 0, 8, 0, 4, 8)` — and the four variable-size ones ([`Polyline`](#polyline), [`MonotoneChain`](#monotonechain), [`Polygon`](#polygon) and [`Convex`](#convex)) take one flat list, read in `(x, y)` pairs:

```python
pgl.Polygon([0, 0, 8, 0, 8, 8, 4, 4, 0, 8])   # same as the list of five Points
```

A sequence of `Point` is accepted just as well, which is what a computed vertex list usually is; a coordinate list of odd length raises a `ValueError`. Coordinates are exact everywhere: `int`, `fractions.Fraction`, or `"a/b"` strings, never `float`.

All shapes contain their boundaries (that is, they are closed in the topological sense). The boundary of a shape is the *manifold boundary*, that is:

- A point has no boundary.
- The boundary of a 1-dimensional shape is the set of (at most two) extreme points of the curve. The boundary of a segment are its two vertices. The boundary of a ray is its one vertex. A line has no boundary.
- The boundary of a 2-dimensional shape is defined in the usual way. The boundary of a triangle is its perimeter, the boundary of a halfplane is the line that defines it.


### Degeneracies

There are two kinds of degenerate shape, and it matters which one you have.

Some are **well defined**: a triangle with three collinear vertices really is a
segment, a disk of radius 0 really is a point, and every operation on them
answers the limit case. Others are **undefined**: a line through two equal points
has no direction, and a disk through three distinct collinear points could be
either of two half-planes. On an undefined shape every geometric operation is
undefined behavior — any value may come back, though never a crash or a hang.

`isUndefined()` tells the two apart, and every shape has it. The well-defined
collapses are named by:

- `s.isPoint()` / `s.getIfPoint()`: whether the shape covers exactly one point,
  and that point (or `None`).
- `s.isSegment()` / `s.getIfSegment()`: whether it covers exactly one segment of
  positive length, and that segment (or `None`).

Not every shape can collapse in every way, so not every shape has all four.
`Line`, `OrientedLine`, `Ray` and `Halfplane` have nothing to collapse *to* — a
degenerate one is undefined outright — so they carry only `isUndefined()`. A
`Segment`, `OrientedSegment` or `Disk` can only ever become a point, so they have
no `isSegment`. `PolygonWithHoles` has `isPoint`/`isSegment` but no `getIf` pair.

A shape that has dropped **below its natural dimension** is entirely boundary
with empty interior. So on it `boundaryContains` coincides with `contains`, while
`interiorContains` and `interiorsIntersect` are always `False`.

```python
t = pgl.Triangle(pgl.Point(0,0), pgl.Point(2,2), pgl.Point(4,4))
t.isSegment()                      # True
t.getIfSegment()                   # (0,0)--(4,4)
t.interiorContains(pgl.Point(2,2)) # False: no interior left
```

A `MonotoneChain` or `Polyline` is the exception worth knowing: a straight one
*is* a segment, so `isSegment()` holds, but a chain is one-dimensional to begin
with and has dropped nothing. It keeps its own boundary (its two extreme
vertices) and its relative interior, and `isDegenerate()` is `False`.

### Point

The `Point` class template defines a point with x and y coordinates. A point has no boundary and has the point itself as the interior.

```python
p = pgl.Point(7,9)
```

You can read the coordinates of a point `p` as `p[0]` and `p[1]` or `p.x()` and `p.y()`. You can also iterate through the coordinates.

```python
for coord in p:
    print(coord, end = ' ')
print(p)
# Output: 7 9 (7,9)
```

A point has methods:
- `p.swapped()`: Returns the point with x and y coordinates swapped.
- `p.dual()`: Returns the dual line $y = ax - b$ for a point $(a,b)$.
- `p.polar()`: Returns the polar line $ax + by = 1$ for a point $(a,b)$. Throws an exception for the origin.

- Other methods:

### Segment

The `Segment` class template defines an unoriented straight line segment. The segment always stores the endpoints in increasing order.

```python
s = pgl.Segment(1,2,3,4)
t = pgl.Segment(3,4,1,2)
if s == t:
    print(s, "==", t)
# Output: (1,2)--(3,4) == (1,2)--(3,4)
```

You can read the two endpoints of a segment `s` as `s[0]` and `s[1]` or `s.min()` and `s.max()`. You can also iterate through the endpoints.

```python
s = pgl.Segment(3,4,1,2)
for i in (0,1):
    print(s[i], end = ' ')
for p in s:
    print(p, end = ' ')
# Output: (1,2) (3,4) (1,2) (3,4)
```

The interior of a segment is all the segment except the two endpoints.
```python
s = pgl.Segment(1,0,5,0)
t = pgl.Segment(2,0,2,3)
if s.intersects(t):
    print("Intersect!")
if not s.interiorsIntersect(t):
    print("Interiors do not intersect!")
# Output: Intersect! Interiors do not intersect!
```

A segment `s` has methods such as:

- `s.midpoint()`: Returns the midpoint.
- `s.length()`: Returns `s[0].distance(s[1])` as `float`.
- `s.squaredLength()`: Returns `s[0].squaredDistance(s[1])`.
- `s.isDegenerate()`: Returns `s.length() == 0`.
- `s.isVertical()`: Returns `s[0].x() == s[1].x()`.
- `s.isHorizontal()`: Returns `s[0].y() == s[1].y()`.
- `s.containsEndpoint(p)`: Returns `s[0] == p or s[1] == p`.
- `s.collinear(t)`: Returns whether `s` and `t` are on the same line.
- `s.slope()`: Returns `(s[1].y()-s[0].y()) / (s[1].x()-s[0].x())`.
- `s.parallel(t)`: Returns whether `s` and `t` have the same slope value.
- `s.yAtX(x)`: Returns the value of the segment y coordinate at the given coordinate `x` or `None`.
- `s.xAtY(y)`: Returns the value of the segment x coordinate at the given coordinate `y` or `None`.
- `s.asLine()`: Returns the line that contains `s`.

- Other methods:


### Oriented Segment

The `OrientedSegment` class template defines an oriented straight line segment. The user chooses the order of the two endpoints, which are named `source` and `target`, respectively.

```python
s = pgl.OrientedSegment(1,2,3,4)
t = pgl.OrientedSegment(3,4,1,2)
if s != t:
    print(s, "!=", t)
# Output: (1,2)->(3,4) != (3,4)->(1,2)
```

You can read the two endpoints of an oriented segment `s` as `s[0]` and `s[1]` or `s.source()` and `s.target()`. You can also iterate through the endpoints.

```python
s = pgl.OrientedSegment(1,2,3,4)
print(s)
# Output: (1,2)->(3,4)
```

An oriented segment `s` has all methods of the `Segment` class:

- `s.midpoint()`: Returns the midpoint.
- `s.length()`: Returns `s[0].distance(s[1])` as `float`.
- `s.squaredLength()`: Returns `s[0].squaredDistance(s[1])`.
- `s.isDegenerate()`: Returns `s.length() == 0`.
- `s.isVertical()`: Returns `s[0].x() == s[1].x()`.
- `s.isHorizontal()`: Returns `s[0].y() == s[1].y()`.
- `s.containsEndpoint(p)`: Returns `s[0] == p or s[1] == p`.
- `s.collinear(t)`: Returns whether `s` and `t` are on the same line.
- `s.slope()`: Returns `(s[1].y()-s[0].y()) / (s[1].x()-s[0].x())`.
- `s.parallel(t)`: Returns whether `s` and `t` have the same slope value.
- `s.yAtX(x)`: Returns the value of the segment y coordinate at the given coordinate `x` or `None`.
- `s.xAtY(y)`: Returns the value of the segment x coordinate at the given coordinate `y` or `None`.
- `s.asLine()`: Returns the line that contains `s`.


It also has:

- `s.opposite()`: Returns the segment with source and target interchanged.
- `s.orientation(p)`: Given a point `p`, returns the orientation sign of `s[0],s[1],p` as an `int`: `0` when they are collinear, `-1` when `s` sees `p` to its right, and `+1` when `s` sees `p` to its left.
- `s.rightHalfplane()`: Returns the half-plane defined by all points `p` such that `s.orientation(p) <= 0`.
- `s.leftHalfplane()`: Returns the half-plane defined by all points `p` such that `s.orientation(p) >= 0`.

It knows how to convert itself with an explicit cast to:
- `s.asOrientedLine()`: Returns the line that contains `s` and has the same orientation.
- `s.asRay()`: Returns the half-line that contains `s` and has the same source.

- Other methods:


### Line

The class template `Line` represents an infinite unoriented straight line. A line is stored as any two points it contains, but two lines defined by two distinct collinear points always compare equal. The two points are stored in increasing order.

```python
l1 = pgl.Line(1,2,3,4)
l2 = pgl.Line(2,3,1,2)
if l1 == l2:
    print(l1, "==", l2)
# Output: -(1,2)--(3,4)- == -(1,2)--(2,3)-
```

The defining points may be accessed as in a segment. The interior of a line is the whole line, so `contains` and `interiorContains` are equivalent.

A line `l` has some additional methods such as:

- `l.isDegenerate()`: Returns `l[0] == l[1]`.
- `l.isVertical()`: Returns `l[0].x() == l[1].x()`.
- `l.isHorizontal()`: Returns `l[0].y() == l[1].y()`.
- `l.slope()`: Returns `(l[1].y()-l[0].y()) / (l[1].x()-l[0].x())`.
- `l.parallel(t)`: Returns whether `l` and `t` have the same slope value.
- `l.halfplaneAbove()`: Returns the half-plane defined by all points `p` that are above the line (larger y-coordinate). If the line is vertical, then it returns the half-plane with smaller x-coordinate. In other words, it returns the half-plane defined by all points `p` such that `pgl.OrientedSegment(l[0],l[1]).orientation(p) >= 0`, noticing that `l[0] < l[1]`.
- `l.halfplaneBelow()`: Returns the half-plane containing `l` and not `halfplaneAbove`.
- `l.dual()`: Returns the point $(a,b)$ such that `l` is defined by $y = ax - b$. Throws an exception for vertical lines.
- `l.polar()`: Returns the point $(a,b)$ such that `l` is defined by $ax + by = 1$. Throws an exception for lines through the origin.
- `l.yAtX(x)`: Returns the value of the line y coordinate at the given coordinate `x`.
- `l.xAtY(y)`: Returns the value of the line x coordinate at the given coordinate `y`.

- Other methods:


### Oriented Line

The class template `OrientedLine` represents an infinite oriented straight line. An oriented line is stored as any two points it contains but the order matters as the line is oriented from the source to the target point. Two lines defined by two distinct collinear points compare equal if the points are in the same lexicographical order.

```python
l1 = pgl.OrientedLine(1,2,3,4)
l2 = pgl.OrientedLine(2,3,1,2)
if l1 != l2:
    print(l1, "!=", l2)
l2 = l2.opposite()
if l1 == l2:
    print(l1, "==", l2)
# Output: -(1,2)--(3,4)-> != -(2,3)--(1,2)->
#         -(1,2)--(3,4)-> == -(1,2)--(2,3)->
```

The defining points may be accessed as in an oriented segment. The interior of an oriented line is the whole oriented line, so `contains` and `interiorContains` are equivalent.

An oriented line `l` has methods such as:

- `l.isDegenerate()`: Returns `l[0] == l[1]`.
- `l.isVertical()`: Returns `l[0].x() == l[1].x()`.
- `l.isHorizontal()`: Returns `l[0].y() == l[1].y()`.
- `l.opposite()`: Returns the oriented line with source and target interchanged.
- `l.slope()`: Returns `(l[1].y()-l[0].y()) / (l[1].x()-l[0].x())`.
- `l.parallel(t)`: Returns whether `l` and `t` have the same slope value.
- `l.halfplaneAbove()`: Returns the half-plane defined by all points `p` that are above the line (larger y-coordinate). If the line is vertical, then it returns the half-plane with smaller x-coordinate. In other words, it returns the half-plane defined by all points `p` such that `pgl.OrientedSegment(l[0],l[1]).orientation(p) >= 0`, noticing that `l[0] < l[1]`.
- `l.halfplaneBelow()`: Returns the half-plane containing `l` and not `halfplaneAbove`.
- `l.orientation(p)`: Given a point `p`, returns the orientation sign of `l[0],l[1],p` as an `int`: `0` when they are collinear, `-1` when `l` sees `p` to its right, and `+1` when `l` sees `p` to its left.
- `l.rightHalfplane()`: Returns the half-plane defined by all points `p` such that `l.orientation(p) <= 0`.
- `l.leftHalfplane()`: Returns the half-plane defined by all points `p` such that `l.orientation(p) >= 0`.
- `l.yAtX(x)`: Returns the value of the line y coordinate at the given coordinate `x`.
- `l.xAtY(y)`: Returns the value of the line x coordinate at the given coordinate `y`.

It knows how to convert itself with an explicit cast to:
- `l.asLine()`: Returns the line without the orientation.

- Other methods:


### Ray

The class template `Ray` represents a half-line. A ray is stored as its source endpoint and any other point it contains. Two rays `l1`,`l2` are equal if they have the same source and the other defining point of `l1` is contained in `l2`.

```python
l1 = pgl.Ray(1,2,3,4)
l2 = pgl.Ray(2,3,1,2)
if l1 != l2:
    print(l1, "!=", l2)
l2 = l2.opposite()
if l1 == l2:
    print(l1, "==", l2)
# Output: (1,2)--(3,4)-> != (2,3)--(1,2)->
#         (1,2)--(3,4)-> == (1,2)--(2,3)->
```

The defining points may be accessed as in an oriented segment and may be changed directly. The boundary of a ray is its source.

A ray `l` has methods such as:

- `l.isDegenerate()`: Returns `l[0] == l[1]`.
- `l.isVertical()`: Returns `l[0].x() == l[1].x()`.
- `l.isHorizontal()`: Returns `l[0].y() == l[1].y()`.
- `l.opposite()`: Returns the ray with source and target interchanged.
- `l.slope()`: Returns `(l[1].y()-l[0].y()) / (l[1].x()-l[0].x())`.
- `l.parallel(t)`: Returns whether `l` and `t` have the same slope value.
- `l.halfplaneAbove()`: Returns the half-plane defined by all points `p` that are above the line (larger y-coordinate). If the line is vertical, then it returns the half-plane with smaller x-coordinate. In other words, it returns the half-plane defined by all points `p` such that `pgl.OrientedSegment(l[0],l[1]).orientation(p) >= 0`, noticing that `l[0] < l[1]`.
- `l.halfplaneBelow()`: Returns the half-plane containing `l` and not `halfplaneAbove`.
- `l.orientation(p)`: Given a point `p`, returns the orientation sign of `l[0],l[1],p` as an `int`: `0` when they are collinear, `-1` when `l` sees `p` to its right, and `+1` when `l` sees `p` to its left.
- `l.rightHalfplane()`: Returns the half-plane defined by all points `p` such that `l.orientation(p) <= 0`.
- `l.leftHalfplane()`: Returns the half-plane defined by all points `p` such that `l.orientation(p) >= 0`.
- `l.yAtX(x)`: Returns the ray's y coordinate at the given coordinate `x`, or `None` if the ray has no point there.
- `l.xAtY(y)`: Returns the ray's x coordinate at the given coordinate `y`, or `None` if the ray has no point there.

It knows how to convert itself with an explicit cast to:
- `l.asLine()`: Returns the line containing the ray.
- `l.asOrientedLine()`: Returns the oriented line containing the ray and the same orientation.

- Other methods:


### Polyline

The class `Polyline` represents an open polygonal chain: a sequence of vertices joined in traversal order, with $n - 1$ edges for $n$ vertices and no closing edge back to the first vertex. Unlike a `Polygon`, it may cross itself.

The constructor keeps the vertex order you give it, canonicalizing only the *direction* (the sequence is reversed when the reversal compares lexicographically smaller), so a polyline equals its own reverse but not a different traversal of the same vertices:

```python
p = pgl.Polyline([0, 0, 2, 2, 2, 0])
print(p)
# Output: Polyline[(0,0),(2,2),(2,0)]
print(p == pgl.Polyline([2, 0, 2, 2, 0, 0]))
# Output: True  (the same chain, traversed backwards)
```

Like `Polygon` and `Convex`, a polyline stores a lazy translation, so translating it is $O(1)$; it is mutable and therefore unhashable.

A polyline `p` has methods such as:

- `p.isSimple()`: Returns true if the chain does not touch or cross itself. A *closed* polyline (last vertex equal to the first) is not simple.
- `p.isDegenerate()`: Returns true if every vertex coincides.
- `p.length()`: Returns the Euclidean length (a `float`: a sum of square roots is irrational in general).
- `p.lengthL1()` / `p.lengthLInf()`: Return the exact Manhattan / Chebyshev length.
- `p.pointInside()`: Returns an exact point in the relative interior (the midpoint of the first edge).

As a 1-dimensional shape, its boundary is its two extreme vertices and its relative interior is everything else — the same convention as `Segment`. `p.intersection(s)` returns a *list* of `Point` and `Segment` pieces, since a chain can meet even a line in arbitrarily many disjoint places. It is not defined against `Disk` or `Polygon`.

- Other methods:


### MonotoneChain

The class `MonotoneChain` represents a weakly x-monotone polygonal chain. Its vertices are stored sorted lexicographically (smaller x first, ties broken by smaller y), which means the constructor treats its input as a **point set**, not as a pre-linked chain: the points are sorted and deduplicated, so any input order yields the same chain, and the chain is automatically simple.

Consecutive vertices may share an x-coordinate, producing a vertical edge — that is what makes it only *weakly* monotone.

```python
c = pgl.MonotoneChain([2, 2, 0, 0, 1, 3])
print(c)
# Output: MonotoneChain[(0,0),(1,3),(2,2)]  # sorted, whatever the input order
print(c.isStrictlyMonotone())
# Output: True  # no two vertices share an x, so the chain is the graph of a function
```

The sorted order buys $O(\log n)$ vertical queries, which no other shape has. Each returns `None` when the query x lies outside the chain's x-extent:

- `c.indexAtX(x)`: The index of the vertex at `x`, or of the vertex starting the edge spanning `x`.
- `c.yAtX(x)`: The exact y-coordinate of the chain at `x`.
- `c.isBelow(p)` / `c.isAbove(p)`: Engaged when a ray shot straight down / up from `p` hits the chain. A point *on* the chain satisfies both.
- `c.isStrictlyBelow(p)` / `c.isStrictlyAbove(p)`: The strict variants. A point on the chain satisfies neither.

It is also the only chain that can grow: `c.insert(point)` or `c.insert(points)` splices new vertices into the sorted sequence (a duplicate is ignored).

Otherwise it behaves exactly like a [`Polyline`](#polyline): $n - 1$ edges, `Segment`'s boundary convention, a lazy $O(1)$ translation, mutable and therefore unhashable, `length`/`lengthL1`/`lengthLInf`/`pointInside`, and a list-valued `intersection` that is not defined against `Disk` or `Polygon`.

- Other methods:


### Half-Plane

The class template `Halfplane` is stored as an oriented line, but represents a completely different geometric object that contains all points on its left half-plane. The boundary of the half-plane is the line that defines it. Two half-planes are equal if the corresponding oriented lines are equal:

```python
h1 = pgl.Halfplane(1,2,3,4)
h2 = pgl.Halfplane(2,3,1,2)
if h1 != h2:
    print(h1, "!=", h2)
# Output: ^-(1,2)--(3,4)-^ != ^-(2,3)--(1,2)-^

h2 = h2.opposite()
if h1 == h2:
    print(h1, "==", h2)
# Output: ^-(1,2)--(3,4)-^ == ^-(1,2)--(2,3)-^
```

Halfplane does not have an `intersection` method. The defining points may be accessed as in an oriented segment and may be changed directly.

A half-plane `h` has methods such as:

- `h.isDegenerate()`: Returns `h[0] == h[1]`.
- `h.isVertical()`: Returns `h[0].x() == h[1].x()`.
- `h.isHorizontal()`: Returns `h[0].y() == h[1].y()`.
- `h.opposite()`: Returns the half-plane with source and target interchanged.
- `h.slope()`: Returns `(h[1].y()-h[0].y()) / (h[1].x()-h[0].x())`, possibly negative.

It knows how to convert itself with an explicit cast to:
- `l.asLine()`: Returns the line bounding the half-plane.
- `l.asOrientedLine()`: Returns the oriented line bounding the half-plane.

- Other methods:


### Triangle

The class template `Triangle` is stored as three points, called vertices, which are kept in the following order. The first vertex is the smallest lexicographically and the other two vertices are ordered such that the triangle is oriented counterclockwise (positive orientation test). Two triangles are equal if they have the same vertices.

```python
t = pgl.Triangle(3,3,4,1,1,1)
print(t)
# Output: <(1,1)(4,1)(3,3)>
for i in {0,1,2}:
    print(t[i], end=' ')
# Output: (1,1) (4,1) (3,3)
for p in t:
    print(p, end=' ')
# Output: (1,1) (4,1) (3,3)
for s in t.edges():
    print(s, end=' ')
# Output: (1,1)--(4,1) (3,3)--(4,1) (1,1)--(3,3)
for s in t.orientedEdges():
    print(s, end=' ')
# Output: (1,1)->(4,1) (4,1)->(3,3) (3,3)->(1,1)
```

A triangle `t` has methods such as:

- `t.isDegenerate()`: Returns true if there are equal vertices or all vertices are collinear.
- `t.centroid()`: Returns the centroid.
- `t.circumcircle()`: Returns the circumcircle.
- `t.isRectangle()`: Returns whether one angle is 90 degrees.
- `t.isObtuse()`: Returns whether one angle is greater than 90 degrees.
- `t.isIsosceles()`: Returns whether two sides have the same length.

It knows how to convert itself with an explicit cast to:
- `(pgl.Polygon) t` or `t.asPolygon()`: Returns the polygon representation of the triangle.
- `(pgl.Convex) t` or `t.asConvex()`: Returns the convex polygon representation of the triangle.

- Other methods:


### Rectangle

The class template `Rectangle` represents an axis-aligned rectangle. While it is stored internally as only two vertices (minimum and maximum x and y coordinates), it behaves as a polygon with four vertices. It can be constructed from two opposite corners (given as two `Point`s or four coordinates), from an iterable of points (it computes their bounding box), or from an iterable of bounded shapes — even of mixed types — in which case it computes the bounding box enclosing them all. Unbounded shapes (`Line`, `OrientedLine`, `Ray`, `Halfplane`) have no bounding box and are rejected.

```python
r = pgl.Rectangle([pgl.Point(1,3),pgl.Point(2,4),pgl.Point(3,1),pgl.Point(5,4),pgl.Point(2,3)])
# Same as pgl.Rectangle(pgl.Point(1,1), pgl.Point(5,4)) or pgl.Rectangle(pgl.Point(1,4), pgl.Point(5,1))
print(r)
# Output: [(1,1),(5,4)]
print(r.min(), r.max())
# Output: (1,1) (5,4)
for i in {0,1,2,3}:
    print(r[i], end=' ')
# Output: (1,1) (5,1) (5,4) (1,4)
for p in r:
    print(p, end=' ')
# Output: (1,1) (5,1) (5,4) (1,4)
for s in r.edges():
    print(s, end=' ')
# Output: (1,1)--(5,1) (5,1)--(5,4) (1,4)--(5,4) (1,1)--(1,4)
for s in r.orientedEdges():
    print(s, end=' ')
# Output: (1,1)->(5,1) (5,1)->(5,4) (5,4)->(1,4) (1,4)->(1,1)
```

A rectangle `r` has methods such as:

- `r.isDegenerate()`: Returns true if the rectangle has null area.
- `r.centroid()`: Returns the centroid.
- `r.circumcircle()`: Returns the circumcircle.

It knows how to convert itself with an explicit cast to:
- `r.asPolygon()`: Returns the polygon representation of the rectangle.
- `r.asConvex()`: Returns the convex polygon representation of the rectangle.

- Other methods:


### Disk

The class template `Disk` represents a circle with its interior. Disks are stored internally as three boundary points, in the same way as a `Triangle`. This choice may be surprising, as the standard representation for disks is a center point and a radius. The main motivation is that the circumcircle of a triangle may be represented exactly for integers. Nevertheless, the constructor accepts both forms:

```python
d1 = pgl.Disk(pgl.Point(1,1), pgl.Point(2,5), pgl.Point(4,3))  # Disk from 3 points
d2 = pgl.Disk(pgl.Point(2,3), 4)             # Disk from a point and a radius
print(d2)
# Output: Disk((-2,3)(6,3)(2,7))  # Output always uses 3 points
```

Disk does not have the `intersection` method and cannot be scaled on a single axis. A disk `d` has methods such as:

- `d.isDegenerate()`: Returns true if the points are collinear or equal.
- `d.radius()`: Returns the radius length.
- `d.squaredRadius()`: Returns the squared radius.
- `d.center()`: Returns the center point.
- `d.diameter()`: As always returns a diameter `Segment`, but for disks the segment is always horizontal.

- Other methods:


### Polygon

The class template `Polygon` represents a simple polygon. It can be constructed for any number of points in a container that must be given in the order they appear on the polygon. The vertices are accessed in counterclockwise order starting from the minimum vertex (minimum x, breaking ties by minimum y). ~~Internally, the polygon is stored as multiple x-monotone polylines for improved performance.~~

A polygon `P` has methods such as:

- `P.isDegenerate()`: Returns true if the polygon has null area.
- `P.isSimple()`: Returns true if the edges only intersect at the endpoints of consecutive edges. Takes $O(n \log n)$ time for $n$ edges.
- `P.isConvex()`: Returns true if the polygon is convex, possibly with vertices subdividing convex hull edges. Takes $O(n)$ time.
- `P.chainCount()`: The number of lexicographically monotone chains the boundary breaks into — 2 for a convex ring, and more the more often the boundary reverses direction in $x$. It is what the containment and intersection tests price themselves on: they run chain against chain when there are few and fall back to a plane sweep when there are many.
- `P.untangle()`: Makes the polygon simple in place, returning `None`. Edges that cross are flipped, and when a flip is blocked by collinear vertices the offending vertex is removed instead, so the vertex set may shrink. On return `P.isSimple()` holds. Worst-case complexity is high.
- `P.pointInside()`: Returns an exact point strictly inside the polygon, even a non-convex one (the vertex average would not do: it can fall in a notch, outside the polygon).
- `P.triangulation()` / `P.triangulation(segments)`: Returns the constrained Delaunay [`Triangulation`](data_structures.md#triangulation) of the polygon, optionally with extra constrained edges.
- `P.isStarShaped()`: Returns true if some point of the polygon sees every other point of it.
- `P.getStarShapedKernel()`: Returns the *kernel* — every point that sees the whole polygon — as a [`HalfplaneIntersection`](#halfplane-intersection), or `None` when the polygon is not star-shaped. For a convex polygon the kernel is the polygon itself.
- `P.asPolygonWithHoles()`: Returns the polygon as a hole-free [`PolygonWithHoles`](#polygon-with-holes) region.

A `Polygon` also carries the [boolean operations](shape_methods.md#boolean-operations) `difference`, `regularizedUnion` and `symmetricDifference` — each answering with a [`PolygonSet`](#polygon-set) — and the region-returning [Minkowski sum](shape_methods.md#minkowski-sum). It has `regularizedIntersection` only against a shape that can hold the answer, a `PolygonWithHoles` or a `PolygonSet`.

- `P.empty()`: Returns true if the polygon has no vertex at all, which is the empty set. Distinct from `isDegenerate()`, which is a polygon with vertices but no area.
- `P.convexPartition()`: Cuts the polygon into [`Convex`](#convex) pieces with pairwise disjoint interiors whose union is the polygon, using at most four times the fewest pieces possible. Shorthand for `P.triangulation().convexPartition()`.
- `P.convexCovering()`: Covers the polygon with `Convex` pieces, which may overlap. Irredundant but not necessarily minimum.
- `P.visibilityGraph()`, `P.clearVisibilityGraph()`, `P.reducedVisibilityGraph()`, `P.visibleVertices(q)`, `P.clearlyVisibleVertices(q)`, `P.regularizedVisiblePolygon(q)`: [Visibility](algorithms.md#visibility) inside the polygon.

`P` is not convex in general, so it has neither a Hausdorff distance nor
`verticesContain` (use `P.index(point) is not None` for the latter).

- Other methods:


### Convex

The class template `Convex` represents a convex polygon. It can be constructed for any number of points in a container and will construct the convex hull. The vertices are stored in counterclockwise order starting from the minimum vertex (minimum x, breaking ties by minimum y). If the container already has the vertices in order, a second constructor parameter can be set to true to avoid computing the convex hull.

A convex polygon `c` has methods such as:

- `c.isDegenerate()`: Returns true if the convex polygon has null area.
- `c.centroid()`: Returns the centroid.
- `c.insert(point)` / `c.insert(points)` / `c.insert(shape)`: Enlarges the hull in place so that it contains the given point, points, or shape. A shape must have vertices to take the hull of, so a `Disk` and the unbounded shapes raise a `TypeError`. (They are refused explicitly rather than by omission: every shape is iterable over its defining points, so without the guard `c.insert(disk)` would quietly insert the disk's three *boundary* points, whose hull the disk bulges straight past.)
- `c.upperHull()` / `c.lowerHull()`: Return the upper and lower boundary chains as a [`MonotoneChain`](#monotonechain). Both run between the leftmost and rightmost vertices, and together they cover the boundary.
- `c.smallestEnclosingDisk()` / `c.smallestEnclosingRectangle()`: The smallest enclosing [`Disk`](#disk), and the smallest-**area** enclosing rectangle — which comes back as a [`HalfplaneIntersection`](#halfplane-intersection), since the tightest one is generally tilted and a `Rectangle` is axis-aligned by definition. Both read a convex boundary, which is why they live here; every other shape reaches them through its own `convexHull()`. See [algorithms](algorithms.md#smallest-enclosing-shapes-of-a-convex-hull).

It knows how to convert itself to:
- `c.asPolygon()`: Returns the polygon representation of the convex polygon.
- `c.asPolygonWithHoles()`: Returns the hull as a hole-free [`PolygonWithHoles`](#polygon-with-holes) region.
- `c.asHalfplaneIntersection()`: Returns the hull as a [`HalfplaneIntersection`](#halfplane-intersection), one half-plane per edge.

If the convex polygon `c` has $n$ vertices, then:

- `c.diameter()` takes $O(n)$ time.
- `c.intersects(s)` takes $O(\log n)$ time if `s` is a shape with $O(1)$ vertices (not including Disk).
- `s.intersects(c)` takes $O(\log n)$ time if `s` is a shape with $O(1)$ vertices (not including Disk).
- `c.intersects(c2)` takes $O(\min(n+m) \log(n+m))$ time if `c2` is a convex polygon with $m$ vertices.
- Other predicates take the same time as `intersects`.
- `c.intersection(c2)` takes $O((n+m) log (n+m))$ time if `c2` is a convex polygon with $m$ vertices.

- Other methods:


### Polygon with Holes

The class `PolygonWithHoles` represents a closed region: a simple outer polygon
minus the **interiors** of a set of polygonal holes. Writing $P$ for the outer
polygon and $H_i^\circ$ for the interior of hole $H_i$,

$$A = P \setminus \bigcup_i H_i^\circ.$$

Every hole must satisfy $H_i \subseteq P$, and distinct holes must have disjoint
interiors — their boundaries may meet. The boundary of $A$ is the boundary of $P$
together with the boundary of every hole. Note that $A$ is connected but its
interior may not be.

This is the shape whose intersections can keep holes, and that is what it exists
for: removing a shape from the middle of another leaves a hole, and no other
shape but a [`PolygonSet`](#polygon-set) — which is made of these — can say so.
Every [boolean operation](shape_methods.md#boolean-operations) answers with a set
of them, and a non-convex [Minkowski sum](shape_methods.md#minkowski-sum) with
one of them or with a set.

```python
outer = pgl.Polygon([0,0, 10,0, 10,10, 0,10])
hole = pgl.Polygon([4,4, 6,4, 6,6, 4,6])
region = pgl.PolygonWithHoles(outer, [hole])
print(region.area(), region.holeCount(), region.vertexCount())
# Output: 96 1 8
```

The outer boundary and every hole are ordinary [`Polygon`](#polygon) values, each
in `Polygon`'s own canonical form (counterclockwise, lexicographically smallest
vertex first) — holes are *not* stored reversed. Equality, ordering and hashing do
not depend on the order the holes were given in.

As with `Polygon`, whose constructor does not check simplicity, structural
validity is a documented precondition rather than an enforced invariant.
`isValid()` checks the whole contract on demand.

A region `A` has methods such as:

- `A.outer()`: Returns the outer boundary polygon.
- `A.holeCount()` / `A.hasHoles()` / `A.hole(i)` / `A.holes()`: The holes, in canonical (sorted) order.
- `A.addHole(h)`: Adds a hole in place, keeping the canonical order. A zero-area ring removes nothing and is ignored.
- `A.eraseHole(i)` / `A.eraseHole(h)`: Fills a hole back in, by index or by the polygon itself; the second returns whether it found one.
- `A.vertexCount()`: The total number of vertices over all rings.
- `A.vertices()` / `A.edges()`: The vertices and boundary edges of every ring, outer boundary first.
- `A.orientedEdges()`: The boundary edges directed so the region lies to the left: the outer ring counterclockwise as stored, the hole rings **reversed**.
- `A.empty()`: Returns true if the region has no outer boundary at all, and hence covers no point.
- `A.isSimple()`: Returns true if every ring is simple. A per-ring check only: it says nothing about how the rings sit relative to one another.
- `A.isValid()`: Tests the whole structural contract above.
- `A.chainCount()`: The monotone chains of every ring added up, outer boundary and holes together — the same cost measure `Polygon.chainCount()` reports.
- `A.isRegular()`: Returns true if the region is the closure of its own interior. Since the contract constrains interiors only, a valid region may pinch shut along a whole stretch of edge — a **slit**, region material with no area on either side of it, as when a hole shares an edge with another hole or with the outer boundary. A region with area is regular exactly when it has no slit. Pinching at an isolated *point* is not a slit: the interior still reaches the point from every side.
- `A.regularized()`: Returns $\mathrm{closure}(A^\circ)$ — the region without its slits — as a [`PolygonSet`](#polygon-set), the same regularization every boolean operation applies to its own result. Dropping the slits can disconnect what they were holding together, which is why the result is a set: a region whose slits are its only connective tissue comes back as several components, and one with no area comes back empty.
- `A.convexPartition()` / `A.convexCovering()`: Cut or cover the part of the region that has area with [`Convex`](#convex) pieces. The holes are where there is no piece, and a slit, having no area, appears in none of them.
- `A.visibilityGraph()` and the rest of the [visibility](algorithms.md#visibility) family: sight is stopped by the outer boundary and by every hole.
- `A.twiceArea()` / `A.area()`: Twice the area exactly and without division, and the area itself.
- `A.centroid()`: The area-weighted centroid, the holes entering with negative weight. When the net area is zero the centroid of the vertex set is returned instead.
- `A.verticesCentroid()`: The centroid of the vertex set over all rings.
- `A.pointInside()`: A point strictly inside the region, so inside the outer boundary and outside every hole. Undefined for a region with no area.
- `A.triangulation()` / `A.triangulation(segments)`: The constrained Delaunay [triangulation](data_structures.md#triangulation) of the region. Every ring becomes constrained edges and the hole interiors are left out of the domain, so the in-domain triangles cover exactly the part of the region that has area — a slit, having none, carries no triangle.
- `A.diameter()` / `A.bbox()`: The holes lie inside the outer boundary and cannot contribute, so both are the outer polygon's.

`len(A)`, `A[i]` and iteration run over the region's **vertices**, flattened
across the rings with the outer boundary first, so a region reads like every
other shape. The holes stay reachable through `holeCount()`, `hole(i)` and
`holes()`, and `point in A` is point containment as everywhere else.

- Other methods:


### Polygon Set

The class `PolygonSet` represents a set of
[`PolygonWithHoles`](#polygon-with-holes) components with pairwise disjoint
interiors. The point set is simply their union:

$$A = A_0 \cup A_1 \cup \dots$$

This is the shape that **closes** the regularized
[boolean operations](shape_methods.md#boolean-operations). A difference, a union
or a symmetric difference of two regions can come apart into several pieces, and
an island stranded inside a hole of the answer is a piece like any other — so
before this shape existed those operations had to answer with a bare list, which
could not be fed back in, compared, hashed, drawn or measured.

```python
square = pgl.Polygon([0,0, 10,0, 10,10, 0,10])
holed  = square.difference(pgl.Rectangle(pgl.Point(3,3), pgl.Point(7,7)))
again  = holed.difference(pgl.Rectangle(pgl.Point(0,0), pgl.Point(2,2)))
merged = again.regularizedUnion(holed)
```

It is also the only pypgl shape whose point set **need not be connected**, and
its components are deliberately **not nested**: a component stranded inside
another's hole is stored beside it, not within it.

The components are kept in canonical (sorted) order, so equality, ordering and
hashing do not depend on the order they were supplied in; components of zero area
cover nothing that survives and are dropped, and duplicates are erased. As with
`Polygon` and `PolygonWithHoles`, structural validity — every component valid,
component interiors pairwise disjoint, and no two components sharing a stretch of
edge — is a documented precondition rather than an enforced invariant, and
`isValid()` checks it on demand.

A set `A` has methods such as:

- `A.componentCount()` / `A.component(i)` / `A.components()`: The components, in canonical order.
- `A.addComponent(r)` / `A.eraseComponent(i)` / `A.eraseComponent(r)`: Add or remove a component in place; the last returns whether it found one.
- `A.empty()`: Returns true if the set has no components at all.
- `A.isConnected()`: Returns true if the set is connected as a point set. Two components that never touch are two pieces; the empty set is connected by convention, having nothing to come apart.
- `A.isPinched()`: Returns true if two components touch each other anywhere. `False` is the cheap exact case: components that stay apart make every relation fold componentwise.
- `A.isRegular()` / `A.regularized()`: A set is regular exactly when every component is, since no slit can run between two components. `regularized()` returns a `PolygonSet`, so the regularization is idempotent in the type system and not only in the mathematics.
- `A.isValid()` / `A.isSimple()`: The structural contract above, and the per-ring simplicity check.
- `A.holeCount()` / `A.hasHoles()` / `A.vertexCount()` / `A.vertices()` / `A.edges()` / `A.orientedEdges()`: Counted and collected over every ring of every component.
- `A.area()` / `A.twiceArea()` / `A.centroid()` / `A.verticesCentroid()` / `A.pointInside()` / `A.diameter()` / `A.bbox()`: The components have disjoint interiors, so the area is simply their sum; the diameter may join two different components.
- `A.triangulation()` / `A.convexPartition()` / `A.convexCovering()`: The gaps between components are left out of the domain, exactly as a region's holes are.

`len(A)`, `A[i]` and iteration run over the set's **vertices**, flattened across
every ring of every component, so a set reads like every other shape — the same
choice [`PolygonWithHoles`](#polygon-with-holes) makes. The components stay
reachable through `componentCount()`, `component(i)` and `components()`, and
`point in A` is point containment as everywhere else.

Like `Convex`, `Polygon` and `PolygonWithHoles`, a set is **mutable and therefore
unhashable**. It can be stored in a [`ShapeTree`](data_structures.md#shape-tree)
and drawn on a [canvas](canvas.md), where it is drawn as one shape however many
pieces it came apart into.

- Other methods:


### Halfplane Intersection

The class `HalfplaneIntersection` represents the intersection of a finite set of
closed half-planes: a convex region that, unlike [`Convex`](#convex), may be
unbounded (a wedge, a strip, a half-plane, or the whole plane) and may be empty.

Two conventions are worth pinning down before anything else.

A **default-constructed region is the whole plane** — the intersection of no
half-planes — which is the opposite of `Convex()`, the empty set.

Its **stored elements are half-planes, not points**. The region's corners are
implicit, and generally not representable in the coordinate type of the
half-planes that bound them: integer half-planes routinely bound regions with
rational vertices. That is exactly the case pypgl's single exact rational
instantiation handles without rounding, so `vertices()` is exact rather than a
rounding step.

```python
k = pgl.HalfplaneIntersection(pgl.Rectangle(pgl.Point(0,0), pgl.Point(4,4)))
len(k), k.vertexCount()      # 4 half-planes, 4 corners
k.intersection(pgl.Rectangle(pgl.Point(2,2), pgl.Point(9,9))).area()
# Output: 4
```

A half-plane intersection `k` has methods such as:

- `k.insert(h)`: Intersects the region with one more half-plane, in place. Returns `False` when the half-plane is discarded — because it is redundant, or undefined (a degenerate half-plane bounds no side, so it carries no constraint). When it empties the region, the region switches to a sticky empty state; otherwise it is stored and the stored half-planes it makes redundant are removed.
- `k.empty()`, `k.isPlane()`, `k.isBounded()`, `k.isDegenerate()`: State queries. A degenerate region has empty interior — a line, ray, segment, or point built from touching constraints — and remains fully supported by the predicates.
- `k.isUndefined()`: Always `False`: `insert` ignores undefined half-planes, so every region is well defined.
- `k.isHalfplane()` / `k.getIfHalfplane()`: Whether the region is exactly one closed half-plane, and that half-plane. Exact, no division.
- `k.isLine()` / `k.getIfLine()`: Whether the region is exactly one line, and that line. Needs no coordinate arithmetic: a degenerate region is a point, segment, ray, or line, and only the line has no vertex.
- `k.isRay()` / `k.getIfRay()`: Whether the region is a ray, and that ray.
- `k.isPoint()` / `k.getIfPoint()` and `k.isSegment()` / `k.getIfSegment()`: The remaining degenerate cases. The tests are exact whatever the region's own coordinate type, so a point whose coordinates are not integral is still recognized.
- Together with `empty` and `isPlane` these name every region a half-plane intersection can be, except a full-dimensional one other than a half-plane.
- `k.vertexCount()`, `k.vertex(i)`, `k.vertices()`: The implicit corners, counterclockwise for a bounded region, and exact.
- `k.edge(i)`: The boundary contribution of half-plane `i`: a [`Segment`](#segment) when both neighbouring vertices exist, a [`Ray`](#ray) when only one does, and the whole boundary [`Line`](#line) otherwise.
- `k.halfplanes()`: The stored half-planes, in boundary order.
- `k.bbox()`, `k.asConvex()`, `k.area()`, `k.twiceArea()`, `k.centroid()`: Raise when the region is empty or unbounded — none of them exists then.
- `k.intersection(other)`: Intersecting with a `Halfplane`, `Rectangle`, `Triangle`, `Convex`, or another `HalfplaneIntersection` returns another `HalfplaneIntersection`, so the type is closed under these and the result is exact, with no coordinate divisions. Against the 0D/1D shapes it returns the usual concrete piece.

`len(k)`, `k[i]` and iteration run over the **half-planes**, which are what the
region stores; the corners are reached through `vertexCount()`, `vertex(i)` and
`vertices()`. `point in k` is point containment as everywhere
else.

Equality compares the stored half-planes. For full-dimensional regions the
non-redundant half-planes are a canonical function of the point set, so that is
geometric equality; for degenerate regions the representation is not unique and
equality is representational.

A **bounded** `HalfplaneIntersection` can be stored in a
[`ShapeTree`](data_structures.md#shapetree) and drawn on a
[canvas](canvas.md); an unbounded one has no `bbox()` and so cannot be stored,
though it remains a perfectly good *query* shape.

- Other methods:

