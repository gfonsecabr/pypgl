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

## Data Structures


### Shape Tree

`ShapeTree` is a container for bounded shapes. The tree is built once and answers range queries against an arbitrary query shape. Unlike every other pypgl class, a single tree can mix shape types — a `Triangle` and a `Disk` can be stored side by side. If the tree stores $n$ points, then it behaves like a kd-tree, with $O(\sqrt{n})$ query time for orthogonal range counting and $O(\log n)$ height. For large intersecting shapes, the tree performs similarly to storing the shapes in a list and examining all of them, but with a much larger construction time.

- `ShapeTree(shapes, leaf_size=6)` builds the tree over `shapes` (any iterable of shapes, which may mix types). `leaf_size` is the maximum number of shapes kept at a leaf before it is split.

The query methods come in two families. The *intersecting* family matches stored shapes `s` with `s.intersects(query)`; the *contained* family matches stored shapes `s` with `query.contains(s)`. Each family offers three operations:

- `countIntersecting(query)` / `countContainedIn(query)` return the number of matching stored shapes.

- `reportIntersecting(query)` / `reportContainedIn(query)` return a list with a copy of each matching stored shape.

- `emptyIntersecting(query)` / `emptyContainedIn(query)` return `True` if no stored shape matches.

The query shape may be any shape pypgl binds, including one that cannot itself be stored in a tree (e.g. a `Line`).

Other methods: `size()` and `empty()` report the tree's size; `shapes()` returns all stored shapes, in internal order; `has(shape)` reports whether a shape equal to `shape` is stored (exact membership, not a geometric test — which is why it is not called `contains`); `insert(shape)` adds a shape without rebalancing the tree (raises if `shape` cannot be stored — see below); `erase(shape)` removes one matching shape and reports whether one was found; `rebuild(leaf_size=0)` restores tree quality after many `insert`/`erase` calls (`0` keeps the current leaf size); `nearestNeighbor(query)` returns the stored shape nearest to `query`, or `None` if the tree is empty (`nearestNeighborL1` / `nearestNeighborLInf` minimize the Manhattan / Chebyshev distance instead); `kNearestNeighbors(query, k)` returns up to `k` of them, nearest first, and has no `None` case — an empty answer is an empty list; `boundingBoxes()` returns every node's bounding box, in pre-order.

- Other methods:

A tree also behaves like a Python container: `len(tree)`, `for shape in tree`, and `shape in tree` (exact membership, same as `has`).

Only bounded shapes can be stored — `Point`, `Segment`, `OrientedSegment`, `Triangle`, `Rectangle`, `Convex`, `MonotoneChain`, `Polyline`, `Polygon`, `PolygonWithHoles`, `PolygonSet`, `Disk`. An unbounded shape (`Line`, `OrientedLine`, `Ray`, `Halfplane`) raises if passed to the constructor or to `insert`, but remains valid as a query shape. A `HalfplaneIntersection` is the one shape that falls on both sides: a bounded one stores like any other, an unbounded one raises, so which it is depends on the value rather than the type.

Drawing a tree with `canvas.draw(tree)` (or its inline rendering in a notebook) renders every node's bounding box.

<p align="center">
  <img src="figures/example_shapetree_triangles.svg" alt="Shape tree range query over random triangles" width="50%"/>
  <br/>
  <em>A shape tree over 100 random triangles: the query triangle with the triangles it contains and intersects, plus the node bounding boxes.</em>
</p>


### Triangulation

`Triangulation` stores a mutable triangulation of a polygon or of a point set: the connectivity changes with every `flip`, and `insert` adds vertices, but a vertex is never moved.

- `Triangulation()` creates an empty triangulation.
- `Triangulation(points)` builds the Delaunay triangulation of a list of points.
- `Triangulation(points, segments)` builds the conforming constrained Delaunay triangulation of a point set with constraint segments: the vertices are the points together with the segments' endpoints, every segment appears as a constrained edge, and — unlike the polygon constructors — nothing is carved away, so the domain is the whole convex hull. The segments must be pairwise non-crossing (sharing an endpoint is fine).
- `Triangulation(triangles)` builds a triangulation from an explicit set of triangles tiling a region without overlaps.
- `Triangulation(edges)` builds a triangulation from an explicit set of edges (every bounded face must be a triangle).
- `Triangulation(polygon, points=[], segments=[])` builds the constrained Delaunay triangulation of a simple polygon (convex or not), optionally adding interior points as extra vertices and/or interior segments as constrained edges — both are assumed, not checked, to lie inside `polygon`. `polygon.triangulation()` and `polygon.triangulation(segments)` are shortcuts for this.
- `Triangulation(region, points=[], segments=[])` does the same for a [`PolygonWithHoles`](shapes.md#polygon-with-holes), with `region.triangulation()` and `region.triangulation(segments)` as the shortcuts. Every ring becomes constrained edges and the hole interiors are left out of the domain, so the in-domain triangles cover exactly the part of the region that has area — a slit, having none, carries no triangle.

Construction and predicates are exact. For a polygon, the triangles between it and its convex hull are excluded, so the public view — sizes, `triangles()`, `edges()`, `locate`, … — describes exactly the polygon, including non-convex ones.

- `numVertices()`, `numTriangles()`, `numEdges()`, `empty()` report the triangulation's size.

- `has(triangle)` / `has(edge)` report whether a `Triangle`/`Segment` belongs to the triangulation (exact membership, not a geometric test — which is why it is not called `contains`).

- `triangles()` / `edges()` return all triangles / edges, sorted.

- `locate(point)` returns the triangle containing `point`, or `None` if `point` lies outside the triangulated region (or the triangulation is empty). The walk that answers it starts where the previous query ended, which is fast for queries that follow one another.

- `buildPointLocation()` gives that walk a better start instead: an index over a coarsening of the mesh, which the query descends to a cell before walking out of it. It changes what a query costs and never what it answers — a point strictly inside a triangle gets that triangle indexed or not, and one on an edge or a vertex gets an incident triangle either way. Expected $O(V \log V)$ time to build and $O(V / \log V)$ space. **The index survives every edit**: it only picks where the walk starts, so it stays correct across an `insert` or a `flip` and merely loses seed quality as the mesh grows away from it. Rebuilding is therefore the caller's decision — call it again to redraw the index against the mesh as it now stands, and `hasCurrentPointLocation()` says whether that would find anything new. `hasPointLocation()` says whether an index is in place at all, and `clearPointLocation()` gives it up, which is the only thing that does.

- Navigation: `otherTriangle(triangle, shared)` returns the triangle on the other side of the shared edge, or `None` on a boundary edge; `edgeAdjacentTriangles(triangle)` returns the (up to three) triangles sharing an edge with `triangle`; `vertexAdjacentTriangles(triangle)` returns the triangles sharing at least one vertex with `triangle` (excluding it); `incidentTriangles(edge)` returns the (up to two) triangles incident to `edge`, and `incidentTriangles(vertex)` returns every triangle around a vertex, in rotational order.

- Range searching: `trianglesIntersecting(query)` returns the triangles `t` with `t.intersects(query)`{Triangle}; `trianglesInteriorIntersecting(query)` filters with `t.interiorsIntersect(query)`{Triangle} instead. `edgesIntersecting(query)` / `edgesInteriorIntersecting(query)` return matching edges instead of triangles. `query` may be a `Segment`, `OrientedSegment`, `Line`, `OrientedLine`, `Ray`, `MonotoneChain`, `Polyline`, `Point`, `Triangle`, `Rectangle`, `Convex`, `Disk`, or `Halfplane`. If `query` is one of the five straight shapes (`Segment`, `OrientedSegment`, `Line`, `OrientedLine`, `Ray`) the result is ordered along the query, and if it is a chain (`MonotoneChain`, `Polyline`) the result is ordered edge by edge along the chain; otherwise the order is unspecified.

- `isConstrained(edge)` reports whether an edge is flagged as constrained; `setConstrained(edge, value=True)` sets or clears that flag.

- `flip(edge)` replaces `edge` by the opposite diagonal, returning the new edge, or `None` if the flip cannot be performed (non-convex quadrilateral or a constrained edge). `flippable(edge)` reports whether the flip is possible, without performing it. Both also accept a list of edges, flipping them all at once if the whole set is simultaneously flippable (all-or-nothing), or returning `None`/`False` otherwise.

- `insert(point)` adds `point` as a new vertex, subdividing the triangle or edge that contains it; a point outside the convex hull grows the hull, joining `point` to every hull edge it sees (a constrained hull edge stays constrained and becomes interior). It returns `False`, leaving the triangulation unchanged, only if `point` is already a vertex or the triangulation is empty. `insertDelaunay(point)` does the same and then restores the constrained Delaunay property around the new vertex by Lawson flips (never flipping a constrained edge), so a triangulation that was constrained Delaunay stays constrained Delaunay.

  For a triangulation built from a polygon, `point` **must lie in the closed polygon** — exactly like the constructor's extra points. Inserting one outside it (in the region carved away between the polygon and its hull, or beyond the hull) is undefined behavior, and it is *not* checked: a bad point silently corrupts the mesh rather than raising.

`flip`, `insert`, `insertDelaunay` and `setConstrained` are the only methods that mutate the triangulation; the vertex coordinates themselves are fixed at construction, except that `insert`/`insertDelaunay` add new ones.

- Predicates against the **domain** — the region the triangulation covers, which is the polygon for the polygon constructors and the convex hull otherwise. `contains(shape)`, `interiorContains(shape)`, `intersects(shape)` and `interiorsIntersect(shape)` give exactly the answers the shape predicates of the same name give for that region as a `Polygon`, boundary and all: a segment running along a boundary edge is contained and met, but neither interior-contained nor interior-intersecting. They work on the mesh, so the cost follows the triangles the query meets rather than the size of the boundary. They ask a different question from `has()`, which is about being a *cell* of the mesh.

- `asGraph()` returns the 1-skeleton as a [`Graph`](#graph): its vertices are the `numVertices()` stored points and its edges the `numEdges()` edges of the visible mesh. A point identifies a vertex here, so the graph is keyed by the points themselves. A vertex with no in-domain edge comes back isolated; the ghost vertex closing the mesh at infinity is internal and is not one of them.

- `voronoiDiagram()` returns the unbounded [`Arrangement`](#arrangement) dual to the triangulation, which must be non-empty and Delaunay. Each face is labelled with the point that generated its Voronoi cell, so `diagram.label(diagram.locateFace(q))` is the site nearest to `q`. At a Voronoi edge or vertex `locateFace` picks one tied site by its infinitesimal-perturbation rule; `locateCell` plus the incident faces recovers all of them. Exact: the vertices are rationals.

- `convexPartition()` cuts the domain into [`Convex`](shapes.md#convex) pieces with pairwise disjoint interiors, each the union of one or more triangles, within a factor of four of the fewest possible. A constrained edge is never deleted, so the constraints shape the partition. `convexCovering()` instead grows one candidate per triangle and greedily selects and thins them, so the pieces may overlap. `Polygon` and `PolygonWithHoles` have both as shorthands.

- Visibility: `visibilityGraph()`, `clearVisibilityGraph()`, `reducedVisibilityGraph()`, `visibleVertices(q)`, `clearlyVisibleVertices(q)` and `regularizedVisiblePolygon(q)`, all described under [Visibility](algorithms.md#visibility). Sight is stopped by the boundary of the domain *and by every constrained edge*, which is what makes `polygon.triangulation(walls).visibilityGraph()` visibility inside `polygon` among the obstacles `walls`.

- `checkInvariants()` checks the structural invariants (orientation and neighbor symmetry); intended for debugging.

- Other methods:

Drawing a triangulation with `canvas.draw(triangulation)` (or its inline rendering in a notebook) renders every triangle.

<p align="center">
  <img src="figures/example_polygon_triangulation.svg" alt="Triangulation with a segment traversal highlighted" width="50%"/>
  <br/>
  <em>The constrained Delaunay triangulation of a polygon with points inside. Highlighting the triangles a segment meets and those whose interior it actually intersects.</em>
</p>


### Interval Tree

`IntervalTree` is a **mutable** one-dimensional index over bounded shapes. It
stores, for each shape, the closed interval its bounding box projects to on one
axis, and keeps the shapes themselves, so a query can go back to exact
two-dimensional geometry once the projection has pruned the candidates.

- `IntervalTree(shapes)` builds a tree over any iterable of bounded shapes, which
  may mix types; `IntervalTree()` starts empty. `IntervalTreeY` is the same class
  projecting on the y axis instead of on x.
- `insert(shape)` and `erase(shape)` add and remove one shape while keeping the
  tree balanced, so unlike a [`ShapeTree`](#shape-tree) it stays efficient after
  heavy mutation. Equal projected intervals are stored independently.

The queries come in two families, and they answer different questions.

The **projection** family decides from the intervals alone, never looking at the
shapes: `countProjectionsIntersecting(query)`,
`reportProjectionsIntersecting(query)`, `emptyProjectionsIntersecting(query)`,
and the three `…ProjectionsContainedIn` counterparts. Touching at an endpoint
counts as meeting, and containment includes shared endpoints. Two shapes whose
x-ranges overlap may be nowhere near each other in the plane, so this is a
coarser question rather than a faster answer to the exact one.

The **exact** family prunes by the projection and then applies the
two-dimensional predicate: `countIntersecting(query)`,
`reportIntersecting(query)`, `emptyIntersecting(query)` and the three
`…ContainedIn` counterparts return exactly what a `ShapeTree` returns over the
same stored shapes.

Every query is projected before anything else happens, so — unlike a
`ShapeTree`, which prunes the query against stored boxes — an unbounded shape is
rejected as a *query* as well as as an element.

Other methods: `size()`, `empty()`, `shapes()`, `has(shape)`, and the container
sugar `len(tree)`, `for shape in tree`, `shape in tree`.

- Other methods:


### Arrangement

`Arrangement` is the subdivision of the plane induced by segments, rays and
lines. Its finite **vertices** are finite input endpoints, isolated input points,
crossings and the ends of overlaps; its **edges** are the atomic pieces between
them; and its **faces** are the connected components of the complement. Every
finite point of the plane belongs to exactly one cell.

Construction is exact and there is nothing to configure: two segments with
integer endpoints generally cross at a *rational* point, and coordinates here are
exact rationals, so every crossing is representable.

```python
a = pgl.Arrangement([pgl.Segment(0,0, 4,4), pgl.Segment(0,4, 4,0)])
a.vertexCount(), a.edgeCount(), a.faceCount()
# Output: (5, 4, 1)
```

- `Arrangement(shapes)` builds the arrangement of any iterable of shapes: points, segments and oriented segments, polylines and monotone chains, the boundaries of triangles, rectangles, convexes, polygons and regions, and lines, oriented lines and rays. The input may cross, overlap collinearly, repeat, share endpoints, or dangle with a free end; overlapping stretches are merged into one edge that remembers every shape covering it.
- `Arrangement(shapes, points)` additionally makes every given point a vertex wherever it falls: a point on a shape splits it there, and a point on nothing becomes a vertex incident to no edge, in the interior of the face holding it.

The structure is a doubly connected edge list, and the face of a halfedge is
always the one on its **left**, so a bounded face is enclosed by a
counterclockwise cycle and the outer boundary of a connected piece of the input
runs clockwise. All unbounded ends meet at one symbolic vertex at infinity,
ordered by their exact escape direction; there is no clipping frame, and every
halfedge really is part of some input shape.

Cells are named by three handle types — `VertexId`, `HalfedgeId` and `FaceId` —
which are distinct classes rather than plain integers, so a face handle cannot be
passed where a vertex handle is meant. Each has `index()` and `valid()`, and a
default-constructed one is the invalid handle.

- `vertexCount()`, `edgeCount()`, `halfedgeCount()`, `faceCount()`: the numbers of finite vertices, geometric edges, halfedges and faces, every unbounded face included. Face 0 is unbounded, though a line or a pair of rays can create several unbounded faces. The vertex at infinity is not counted, and its handle index is exactly `vertexCount()`.
- `vertices()` returns the finite vertices' positions, `edges()` one `Segment`, `Line` or `Ray` per edge, and `boundedEdges()` only the segments.
- `position(v)` is a finite vertex's position — it raises for the vertex at infinity — and `halfedge(h)` is a halfedge's geometry, directed along it: an `OrientedSegment`, an `OrientedLine` or a `Ray`.
- `witness(v)` / `witness(h)` / `witness(f)` return a point of a cell: the vertex itself, a point inside an edge, and a point strictly inside a bounded face.
- Topology: `twin(h)`, `next(h)`, `source(h)`, `target(h)`, `face(h)`, `outgoing(v)`, `outgoingHalfedges(v)` (clockwise around a vertex, and accepting the infinity handle), and `degree(v)` — one halfedge per incident edge end, so a vertex where $k$ lines cross has degree $2k$.
- `isUnbounded()` reports whether the arrangement has any unbounded edge; `isUnbounded(h)` and `isUnbounded(f)` ask about one edge or face, and `isFictitious(v)` identifies the vertex at infinity.
- Faces: `outerCycle(f)`, `innerCycles(f)`, `outerBoundaryOf(f)`, `innerBoundariesOf(f)`, `boundaryOf(f)` and `hasSimpleBoundary(f)`.
- `polygonWithHoles(f)` returns the closure of a bounded face as a [`PolygonWithHoles`](shapes.md#polygon-with-holes), regularized: a dangling edge sticking into the face is dropped, and a cycle pinching shut at a vertex is cut there into one ring per side. It raises for an unbounded face.
- `halfplaneIntersection(f)` returns the intersection of the supporting half-planes of the face's outer boundary, for a bounded or an unbounded face alike. It equals the face with its holes filled when that boundary is convex.
- `label(cell)` and `setLabel(cell, value)` read and write a `Point` label per edge or per face — what to use to record a classification per cell. `originsOf(h)` and `originsOf(v)` list the positions, in the input list, of every shape that produced a cell.
- Point location: `locateFace(point)` returns the face containing a point (for a point on an edge or a vertex, the face an infinitesimal displacement lands in), and `locateCell(point)` returns the cell that actually contains it, as a `VertexId`, a `HalfedgeId` or a `FaceId` — tell them apart with `isinstance`. `buildPointLocation()` builds an exact trapezoidal map and search DAG, after which queries take expected logarithmic time instead of scanning the edges; `hasPointLocation()` and `clearPointLocation()` complete the trio.
- Tracing a directed curve: `reportIntersecting(curve)` returns the cells the curve meets, in order along it, `firstIntersecting(curve)` only the first, and `emptyIntersecting(curve)` whether it meets none. The curve may be an `OrientedSegment`, `OrientedLine`, `Ray`, `MonotoneChain` or `Polyline`. Where the curve meets an edge only at one of its endpoints, the vertex there stands for the contact.
- `asGraph()` returns the vertex-edge incidence structure as an `ArrangementGraph`, a [`Graph`](#graph) over vertex handles rather than points — the vertex at infinity has no position, so it could not be keyed by one.

A [Voronoi diagram](#triangulation) is an `Arrangement` whose faces carry their
generating site as a label, so the two share this whole interface.

- Other methods:


### Graph

`Graph` is an undirected simple graph over points, the combinatorial companion of
the geometric structures: it is what the [visibility](algorithms.md#visibility)
methods return, and what `Triangulation.asGraph()` hands back.

- `Graph()` builds an empty graph, `Graph(edges)` one from a list of `(u, v)` endpoint pairs. `addVertex(v)` adds an isolated vertex and `addEdge(u, v)` adds an edge along with any endpoint still missing; `removeEdge(u, v)` leaves the endpoints in place, `removeVertex(v)` deletes every incident edge with the vertex, and `clear()` empties the graph. A self-loop is ignored.
- `containsVertex(v)`, `containsEdge(u, v)`, `vertexCount()`, `edgeCount()`, `maxDegree()`, and `degree(v)` — which returns `None` for an absent vertex.
- `vertices()`, `edges()`, `neighbors(v)` and `closedNeighbors(v)` return **sorted** lists, so a program's output never depends on hashing. `edges()` gives each undirected edge once, as a `(u, v)` pair in increasing order. Asking about an absent vertex raises.
- `bfs(v)` returns the connected component of `v` in breadth-first order and `bfs(v, k)` stops after `k` vertices; `components()` returns the connected components, largest first.
- `biconnectedComponents()` returns the vertex sets of the vertex-biconnected blocks, largest first: a bridge is a two-vertex block, an articulation vertex belongs to more than one, and an isolated vertex to none.
- `cliqueCover()` partitions the vertices into cliques, largest first, by DSATUR coloring of the complement graph. The number of cliques is not guaranteed minimum.
- `independentSet()` returns a **sorted** maximal set of pairwise non-adjacent vertices, chosen greedily from the lowest-degree vertex up. Maximal, not maximum: every vertex left out is adjacent to one inside, but a larger independent set may exist. Vertices of equal degree are considered in an unspecified order, so which of several equally good sets comes back may vary between runs — only the ordering of the answer is fixed.
- `spanningTree(weight)` returns a minimum spanning tree as another graph, by Prim's algorithm in $O(m \log m)$. `weight(u, v)` may return any comparable number — `Fraction` to stay exact, `float` for Euclidean lengths — and must be symmetric. A disconnected graph gives one tree per component, so the result always has the same vertices and components.
- `shortestPath(source, target, weight)` returns the vertices of a shortest path, both ends included, by Dijkstra's algorithm. Weights must be non-negative and add up with `+`, neither of which is checked. A vertex to itself is that vertex alone, and an empty result means there is no path — different components, or an absent endpoint.
- `shortestPath(source, target, weight, lowerBound)` finds the same path by A* instead: `lowerBound(v, target)` estimates what is left to travel and prioritizes the vertices that look closest, which expands far fewer of them than Dijkstra when the estimate is informative. It must be non-negative, must never exceed the true remaining distance and must be zero at the target — none of which is checked, and an overestimate simply returns a path that need not be shortest. It need not be consistent: a vertex is reopened whenever a shorter route to it turns up. Straight-line distance is the usual choice when the weights are Euclidean lengths.

```python
square = pgl.Polygon([0,0, 4,0, 4,4, 0,4])
graph = square.visibilityGraph()
tree = graph.spanningTree(lambda a, b: a.squaredDistance(b))   # exact weights
print(tree.edgeCount())
# Output: 3
```

A graph also behaves like a Python container: `len(graph)`, `for vertex in
graph` (sorted), and `vertex in graph`. It is mutable and therefore unhashable.

- Other methods:

### Bit Matrix

`BitMatrix` represents a digital geometry shape: the union of the unit squares $[x, x+1] \times [y, y+1]$ over a set of integer points, stored as one bit per cell of a rectangular window of the grid, packed into 64-bit words. Cell `(x, y)` is that unit square, named by its lower-left corner. The window is fixed at construction and never grows: writing outside it is a no-op and reading outside it gives `False`, so sizing it is the caller's job. It is the cheap representation for the rectilinear work an exact polygonal one makes expensive — the set algebra, the Minkowski operations, connectivity and morphology all run a word at a time — at the price of only representing what the grid can.

A matrix wears two hats, and which one an operation wears is in its name. As a **region of the plane**, the union of its cells as unit squares: that is what the predicates, `area()`, `perimeter()`, `centroid()`, `bbox()`, `convexHull()`, `asPolygonWithHoles()`, `asPolygonSet()`, the symmetries and `minkowskiSum()` answer for, and they all commute with `asPolygonSet()`. As a **set of lattice points**, each cell standing for its lower-left corner: that is what every `lattice`-prefixed operation works in, and it is the convention that makes a structuring element behave — a one-cell matrix is the identity of `latticeMinkowskiSum` and `latticeMinkowskiErosion` is its exact dual. The two readings differ by a cell: `reflected()` maps cell `c` to `-c - (1,1)` where `latticeReflected()` maps it to `-c`. Translation reads the same either way.

A cell is named either by a pair of plain `int`s or by a `Point`, whichever reads better at the call site — `m.set(3, 4)` and `m.set(pgl.Point(3, 4))` are the same call. A `Point` naming a cell must have whole coordinates: a fractional one raises rather than being rounded, since rounding it would move the cell.

- `BitMatrix(origin, width, height)` covers `width` by `height` cells from `origin`, all clear; a non-positive extent leaves the window empty. `BitMatrix(x, y, width, height)` spells the same thing with the origin as two ints. `BitMatrix(window)` takes the window as the `Rectangle` its cells cover, the inverse of `window()`. `BitMatrix(polygon)`, `BitMatrix(region)` and `BitMatrix(set)` rasterize a `Polygon`, a `PolygonWithHoles` or a `PolygonSet` whose every edge is axis-parallel, over its own bounding box, filling the cells it covers and leaving the holes and the gaps between components unset; each of those three shapes spells the same operation `asBitMatrix()`. `BitMatrix(cells)` instead takes an iterable of cells — `Point`s, `(x, y)` pairs of ints, or a mix — and sets one bit per cell over the smallest window holding them, so the result is its own `trimmed()`; an empty iterable gives an empty window. A shape is not such an iterable even though iterating one gives its vertices (those are a boundary, not a point cloud) and neither is another matrix, which carries a window this reading would trim away: both raise a `TypeError` naming what to pass instead — `shape.vertices()`, `matrix.lattice()`, or `shape.latticePoints()` for the cells a shape actually covers.

- `innerRaster(shape, window)` and `outerRaster(shape, window)` rasterize **any** shape, the first keeping the cells the shape contains and the second the cells it meets, so the two bracket the shape. Each costs one exact predicate per cell of the window, against the one pass per row a rectilinear region takes. The window may be left out, and is then the smallest cell window covering the shape's bounding box — which is why an unbounded shape (`Line`, `OrientedLine`, `Ray`, `Halfplane`, an unbounded `HalfplaneIntersection`) needs one given explicitly, though it rasterizes perfectly well once it has one.

- `get(x, y)` and `set(x, y)` read and write one cell, along with `set(x, y, value)`, `reset(x, y)`, `flip(x, y)`, `setAll()` and `clear()`. `set`, `reset` and `flip` also take an iterable of cells, read exactly as the range constructor reads one except that the window stays the one the matrix already has, so a cell outside it is dropped as it is for the single-cell forms. A repeated cell leaves `set` and `reset` unaffected but cancels under `flip`, which is what flipping a cell twice means. `origin()`, `width()`, `height()`, `window()`, `emptyWindow()`, `inWindow(x, y)` and `sameWindow(other)` describe the window; `resized(window)` moves the cells to another one, dropping those it cannot hold, and `trimmed()` moves them to the smallest window holding them.

- `count()` and `empty()` report the set cells. `lattice()` returns them as `Point`s in row-major order and `cells()` as the unit `Rectangle`s they cover; `rectangles()` instead merges each row's runs into as few disjoint covering rectangles as a row-major pass can, which is how to draw the cells as separate elements: `canvas.draw(matrix.rectangles())`.

- `area()`, `perimeter()`, `centroid()`, `pointInside()` and `bbox()` measure the covered region: the number of cells, the length of its boundary counting the edges of a cell on the window border, the average of the cell centers, the center of the first set cell, and the rectangle the cells cover. All stay exact. `centroid()` and `pointInside()` raise when no cell is set. `convexHull()` returns the hull of the region as a `Convex`.

- `asPolygonSet()` returns the covered region as a `PolygonSet`, one component per edge-connected group of cells, so it has no precondition and keeps two components touching only at a corner apart. The boundary loops are read straight off the words, and vertices in the middle of a straight stretch are dropped along the way, so a filled box comes back as four corners however many cells it holds. `asPolygonWithHoles()` returns a single `PolygonWithHoles` and raises unless the cells form one edge-connected group, which a rasterized region and its Minkowski sums are. `canvas.draw(matrix)` draws the matrix as one element by drawing that polygon set.

- The shape predicates read the cells as the closed squares they are. `contains(other)` holds when every cell of `other` is a cell of this matrix, and `interiorContains(other)` when none of them touches the boundary either, corners included. `intersects(other)` holds as soon as a cell of one comes within Chebyshev distance one of a cell of the other, since two cells sharing only an edge or a corner already share points; `interiorsIntersect(other)` is the stricter question of a shared cell. `boundaryContains(other)` holds only for an empty `other`, a boundary being a curve and a nonempty matrix covering area.

- `&`, `|`, `^` and `difference(other)` are the set algebra, with `symmetricDifference(other)` spelling `^` out. Each returns the smallest window that provably loses no cell: the overlap of the two windows for an intersection, their hull for a union or a symmetric difference, the left window for a difference. The compound `&=`, `|=` and `^=` instead never move their window and drop whatever falls outside it, exactly as `set` does. `andCount(other)`, `orCount(other)` and `xorCount(other)` give the three cardinalities without building the result. `~` is the complement *within the window*, not against the plane.

- The window is part of a matrix's value: `==` and the ordering compare it along with the cells, and the order is lexicographic on origin, width, height and bits, carrying no geometric meaning. `samePointSet(other)` is the geometric question, and `trimmed()` is the canonical form to compare by when only the region matters — a matrix is unequal to its trimmed form whenever trimming moves anything, while `samePointSet` always holds between them. Every window covering no cell has one canonical form, so all such matrices compare equal whatever origin they were built with. A matrix is mutable and therefore unhashable.

- `translated(vector)` moves the cells, spelled `matrix + point` or `point + matrix`, with `matrix - point` for the opposite and `+=` and `-=` in place. `reflected()` (also `-matrix`), `reflectedX()`, `reflectedY()`, `transposed()`, `rotated90(k)` and its in-place `rotate90(k)` are the symmetries of the covered region, so they commute with the conversion. The `lattice`-prefixed `latticeReflected()`, `latticeReflectedX()`, `latticeReflectedY()`, `latticeRotated90(k)` and `latticeRotate90(k)` map the lattice points instead. Transposition is the exception the two readings agree on, so `transposed()` and `latticeTransposed()` are the same operation.

- `latticeMinkowskiSum(other)` is the sum of the two cell sets read as lattice points, over a window that is exactly the bounding box of the result. It costs one shifted or-assignment of the larger operand per cell of the smaller one, so a large region and a small structuring element are cheap. `latticeMinkowskiErosion(other)` is its dual, the lattice points `p` with `p + other` inside this matrix, over this window shrunk by `other`'s bounding box; eroding by a matrix with no cell is vacuously true and fills the window. `latticeOpening(other)` and `latticeClosing(other)` compose the two in both orders.

- `minkowskiSum(other)`, also spelled `matrix + matrix`, is instead the sum of the two **regions**, so it commutes with the conversion. The unit square is not the identity of that sum — $U \oplus U$ is the two-by-two square — so this is the lattice sum dilated by the block that extra square covers, and comes out one cell wider and one cell taller in each direction. `minkowskiErosion(other)` is the region erosion, regularized the way a `PolygonSet` regularizes its own, which is what keeps it on the grid: a cell eroded by a cell is a single point, which has no area and is reported as empty.

- `interior(adjacency)` returns the set cells all of whose neighbors are set and `boundary(adjacency)` the rest of them, a cell on the window border always belonging to the boundary. `adjacency` is `GridAdjacency.edge` (4 neighbors) by default or `GridAdjacency.vertex` (8 neighbors).

- `connectedComponents(adjacency)` returns one trimmed matrix per connected group of cells, `componentCount(adjacency)` and `isConnected(adjacency)` count them, and `fillHoles(adjacency)` adds every group of unset cells that cannot reach outside. The background is always walked with the complementary adjacency, which is what keeps a diagonal chain of cells from both being connected and letting the background leak through it. `holeCount(adjacency)` counts what `fillHoles` would add, and `eulerNumber(adjacency)` returns components minus holes.

- `fillRows()` and `fillColumns()` close the gaps of every row or column in place and report whether anything changed; `makeHvConvex()` alternates them to a fixed point and returns how many cells it added, giving the smallest hv-convex superset. `isRowConvex()`, `isColumnConvex()` and `isHvConvex()` ask whether that fixed point is already reached.

```python
room = pgl.Polygon([0,0, 10,0, 10,10, 0,10]).asBitMatrix()
robot = pgl.BitMatrix(0, 0, 2, 2)
robot.setAll()
free = room.minkowskiErosion(robot)          # where the robot's corner may sit
print(free.count(), free.isConnected(), free.asPolygonSet().componentCount())
# Output: 64 True 1
```

A matrix also behaves like a Python container: `len(matrix)` is the number of set cells, `for cell in matrix` yields them as `Point`s in row-major order, and `point in matrix` asks whether *that cell* is set — the question `get` answers, not whether the point lies in the covered region.

- Other methods:
