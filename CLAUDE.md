# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

**Core shapes done** (milestones 1–2 of [pypgl.md](pypgl.md)): all
shapes are bound — `Point`, `Segment`, `OrientedSegment`,
`Line`, `OrientedLine`, `Ray`, `Halfplane`, `Triangle`, `Rectangle`, `Convex`,
`Disk` — each with the full 7-predicate × 14-shape matrix (`Polygon` and `Disk`
both joined it in milestone 5 below, `MonotoneChain` and `Polyline` in milestone
9; see `PGL_BIND_ALL_PREDICATES` in
[src/common.h](src/common.h)), constructors,
accessors/measures, and typed `intersection` results for the 0D/1D-result pairs.
The two casters work and the exact round-trip / `optional`→`None` /
`variant`→concrete mappings are verified by the `tests/` suite.

**Notebook UX done** (milestone 3): `Canvas`
([src/bind_canvas.cpp](src/bind_canvas.cpp)) is bound — pgl's stream API
(`canvas << pgl::stroke("red") << shape`) does not map to Python, so each stream
operation is re-exposed as a method: fluent `scale`/`width`/`height`/`size`/
`margin`/`borders` configuration; fluent `stroke`/`fill`/`fillOpacity`/
`strokeOpacity`/`strokeWidth`/`pointRadius` style commands applied to the
*current* style (so only shapes drawn afterwards capture it); one `draw(shape)`
overload per bound shape; and `toSVG()`/`writeSVG(path)` — joined by PDF and Ipe
export in milestone 9, which is also where `strokeWidth`/`pointRadius` moved from
configuration to style. The fluent self-returns
use `nb::rv_policy::reference_internal`. `_repr_svg_` is added Python-side in
[pypgl/__init__.py](pypgl/__init__.py) — on the canvas it returns `toSVG()`, on
every shape it renders a one-shot `Canvas().draw(self)` — so shapes and canvases
display inline in Jupyter.

**Type stubs done** (milestone 4): `_pgl.pyi` is generated at build time by
`nanobind_add_stub` in [CMakeLists.txt](CMakeLists.txt) — from the *bare* `_pgl`
module, with the Python-layer sugar re-added via
[src/stubgen_patterns.txt](src/stubgen_patterns.txt) — and shipped next to
`py.typed` (PEP 561).

**Wheels CI done** (milestone 4): `cibuildwheel` is configured in
[pyproject.toml](pyproject.toml) and run by
[.github/workflows/wheels.yml](.github/workflows/wheels.yml) — CPython 3.10–3.14 on
`manylinux_2_28` (GCC 12 for C++20), macOS arm64 (`macos-15`), and Windows, plus
sdist. macOS x86_64 (`macos-13`) was dropped — GitHub is retiring the Intel
runners, so the jobs sat queued for hours and timed out. pgl has no native deps,
so the build only `FetchContent`s the **pinned** pgl commit (kept in lockstep with
`.pgl-ref`, since the sdist omits the gitignored `.pgl-ref/`). Native-arch only
(no QEMU/cross) because `nanobind_add_stub` imports the just-built `_pgl` to emit
`_pgl.pyi`.

**The macOS runner floor is a compiler floor** (milestone 11 follow-up): the
`macos-14` runner ships AppleClang 15, i.e. LLVM 16, which cannot match the
constraint on an *out-of-line* member-template definition when that constraint
names the enclosing class template. pgl defines every shape's `minkowskiSum`
exactly that way, so pgl 0.5-era headers do not compile there at all and the
0.5.0 wheel job failed twice on it. LLVM 17 is the first release that accepts
the pattern (bisected locally in containers against the pinned pgl commit;
16 fails, 17/18/19 pass), so the matrix moved to `macos-15` (Xcode 16). Two
process notes worth keeping: **pushes to `main` run this same workflow without
publishing**, so the macOS job is testable for free before any tag is moved —
use that rather than burning a release tag; and a green `main` run is the
signal to tag.

**CPython 3.14 wheels** (0.5.1): 0.5.0 shipped 3.9–3.13, so 3.14 users fell
through to the sdist and compiled pgl themselves (which works — that is how the
0.5.0 release was smoke-tested locally — but takes a minute and needs a C++20
compiler). `cp314-*` is now in `build`, which required moving the action from
`cibuildwheel@v2.21` to `@v3.4.1`: v2 has no cp314 at all. Held at v3 rather
than v4 because v4 makes `delvewheel` the default Windows repair step and adds
`abi3audit` — neither is wanted for a single self-contained extension with no
DLL dependencies and no stable ABI. The pattern is `cp314-*` and not `cp314t-*`,
so the free-threaded build is deliberately out of scope (separate ABI, separate
wheel per platform).

**Released done** (milestone 4): `pypgl 0.1.0` is live on
[PyPI](https://pypi.org/project/pypgl/) (`pip install pypgl`). Trusted Publishing
(OIDC, no token) is configured on PyPI and TestPyPI against `wheels.yml`'s
`pypi`/`testpypi` environments; the `publish` job fires on `v*` tags, the
`publish-testpypi` dry-run on manual `workflow_dispatch`. The package version is
exposed as `pypgl.__version__` via `importlib.metadata`; keep `version` in
[pyproject.toml](pyproject.toml) in lockstep with the tag (PyPI never allows
re-uploading a version).

**`Polygon` done** (milestone 5): an arbitrary (possibly non-convex) simple
polygon is bound in [src/bind_polygon.cpp](src/bind_polygon.cpp), pulled in
once upstream pgl's C++ predicates for it settled. It mirrors `Convex`'s
storage (vertices plus a lazy translation) and is likewise bound **mutable**
(`__iadd__`/etc. mutate in place) and therefore unhashable. `Polygon` is now an
11th column/row in the shared `PGL_BIND_ALL_PREDICATES` /
`PGL_BIND_ALL_SQUARED_DISTANCE` macros in [src/common.h](src/common.h), so
every already-bound shape's matrix picked up a `Polygon` column for free.
(`Disk` joined as the 12th shortly after — see below; `MonotoneChain` and
`Polyline` as the 13th and 14th in milestone 9.) `intersection` is
bound against every shape pgl implements it for
— including the 2D∩2D/`Halfplane` cases, since a non-convex polygon's 1D
intersection pieces are plain `list[Point]` (at the time, pgl's `Polyline` was
only a `std::vector<Point>` stub, not a dedicated class — milestone 9 made it a
real shape, but `Polygon.intersection` still returns the plain point list)
rather than a new type to bind. `pointInside`/`verticesContain` are not bound:
pgl does not implement them for a non-convex shape. (`pointInside` since
landed upstream and *is* bound as of milestone 9; `verticesContain` still does
not exist.)

**`Disk` fully joins the shared matrix** (milestone 5 follow-up): pgl finished
`Disk`'s remaining gaps against `Convex`/`Polygon` for both predicates and
squared distance, so `Disk` is now simply a 12th entry in
`PGL_BIND_ALL_PREDICATES` and `PGL_BIND_ALL_SQUARED_DISTANCE`
([src/common.h](src/common.h)) like every other shape — no more asymmetry
(`triangle.contains(disk)` works, not just `disk.intersects(triangle)`) and no
more per-file exclusion lists. Concretely: `Convex::squaredDistance(Disk)` was
added explicitly (since `Convex` outranks `Disk`), plus a generic
`shapeRank`-based forwarder on `Disk` that reaches both `Convex` and `Polygon`
(`Polygon::squaredDistance(Disk)` already existed, and `Triangle::contains(Disk)`
already existed too — only the squared-distance pair and a couple of others
were actually missing). A first attempt at the squared-distance upstream fix
mixed `Convex`'s own coordinate type with the query point's inside
`Convex::squaredDistance(const OtherPoint&)`, which happened to compile for
every prior caller (same type on both sides) but broke the moment
`Disk::center<double>()` was passed in with `ResultNumber=double` requested —
fixed by promoting through the same common-type mechanism
`orientationDeterminant` already used. On the pypgl side this simplified
things: `bind_disk.cpp`'s predicate/squared-distance sections are now each a
single macro call (`PGL_BIND_ALL_PREDICATES(cls, Disk)` /
`PGL_BIND_ALL_SQUARED_DISTANCE(cls, Disk)`, which include `Disk`'s own
self-pair since `Disk` is in both lists), and the explicit `Polygon↔Disk` /
`Convex↔Disk` lines in `bind_polygon.cpp`/`bind_polygons.cpp` were removed as
redundant.

Still to do: consider STABLE_ABI to cut the wheel count before the next
release. (The 2D∩2D `intersection` gap that used to be listed here closed in
milestone 12. pgl-side gaps that keep pypgl's matrices ragged are tracked in
[doc/todo.md](doc/todo.md): chain ∩ `Disk`, L1/LInf distance to a `Disk`,
Hausdorff distance for the non-convex shapes, and the `Halfplane`-with-`Disk`
sum and erosion, which have no exact answer at all — see milestone 16. The
`regularizedUnionOf` range gap listed here closed in milestone 13.)
[pypgl.md](pypgl.md) remains the authoritative design contract —
update it in lockstep if a decision changes.

**`Triangulation` bound** (milestone 6): a mutable mesh over a fixed vertex
set (pgl's `algorithm/triangulation.hpp`) is bound in
[src/bind_triangulation.cpp](src/bind_triangulation.cpp) over the module's own
`Triangle`/`Segment` pair (`::pypgl::Triangulation` in
[src/common.h](src/common.h) — `.pgl-ref` re-pulled to commit `2693693` for
this). All four C++ construction modes are bound: an explicit triangle set, an
explicit edge set, the Delaunay triangulation of a point set, and the
constrained Delaunay triangulation of a simple `Polygon` (optionally with
extra interior points and/or constraint segments) — `Polygon.triangulation()`/
`triangulation(segments)` are thin shortcuts for the last one, mirroring pgl's
own convenience methods. **The polygon constructor must be registered before
the point-set one**: `pypgl/__init__.py` makes every shape (`Polygon`
included) iterable for its own `in`/indexing sugar, so a bare `Polygon` also
satisfies nanobind's generic "sequence of `Point`" conversion — with the
point-set overload registered first, a positional `Triangulation(polygon)`
call silently built the *unconstrained* Delaunay triangulation of the
polygon's vertices instead (same triangle count for a convex polygon, so it
looked plausible; only `isConstrained()` gave it away). Also bound: sizes,
membership, navigation (`otherTriangle`, `edgeAdjacentTriangles`,
`vertexAdjacentTriangles`, `incidentTriangles`), the full directed/region
traversal matrix (`trianglesIntersecting` and friends, against every shape
pgl's `TriangulationQuery` concept accepts), point location, constrained
edges, and single/batch `flip`. `Triangulation` is not a fixed-extent shape
(no `contains(Point)`/`index`/`get`), so — like `Canvas` — it is shielded from
the `size()`/`get()`/`__contains__` sugar in `__init__.py` and
`stubgen_patterns.txt`; it does get `Canvas.draw()`/`_repr_svg_` support like
every other shape.

`Disk` ([src/bind_disk.cpp](src/bind_disk.cpp)) is bound as its own class:
exact `center`/`squaredRadius`/`bbox`/`pointInside`; `area` is irrational (π) so
it always returns Python `float`; `radius` returns an exact `Fraction` when the
disk was built from a center and radius (delegating the exact/inexact decision to
pgl's throwing `radius<ERational>()`) and a `float` otherwise (square root);
`squaredDistance` to a disk is likewise `float`. `diameter()` is reconstructed as
an exact `Segment` for center+radius disks (pgl ships only a floating-point one)
and raises for an irrational radius; `fbox()` is not bound (its double-coordinate
return type is not registered). Its predicate/squared-distance matrix is now
fully symmetric with every other shape — see the milestone 5 `Disk` follow-up
above.

**`ShapeTree` bound** (milestone 7): a static spatial index over a *mix* of
shapes (pgl's `algorithm/shapetree.hpp`) is bound as a single class in
[src/bind_shapetree.cpp](src/bind_shapetree.cpp) — the one deliberate
exception to "bind concrete shapes, not the `Shape` variant wrapper" (see
Load-bearing design decisions below), since a spatial index that can hold,
say, a `Triangle` and a `Disk` side by side needs a type-erased element, and
`pgl::Shape<PointType>` is exactly that (`::pypgl::AnyShape`/`::pypgl::ShapeTree`
in [src/common.h](src/common.h)). This needed two small upstream pgl fixes,
made in this same session and pulled by re-pinning `.pgl-ref` to `eec62c4`:
`Shape::bbox()` didn't exist at all (added, throwing for the four unbounded
alternatives `Line`/`OrientedLine`/`Ray`/`Halfplane`); and `Shape::squaredDistance`
threw for any pair involving a `Disk`, since `Disk`'s `squaredDistance` (and the
`Disk` overloads on `Convex`/`Polygon`) return a plain `double` rather than
being templated on `ResultNumber` — fixed by falling back to that overload and
`static_cast`ing the result, which is what `ShapeTree::nearestNeighbor` needed
to work when the nearest stored element is a `Disk`. A third bug surfaced by
cross-testing was fixed upstream too: `ShapeTree::insert` computed the new
element's `bbox()` *after* already `push_back`ing it into storage, so a
throwing `bbox()` left a phantom element counted by `size()`/`shapes()`/
iteration but never linked into the tree; the fix reordered the two lines to
restore strong exception safety, so pypgl's `insert()` needed no defensive
workaround of its own.

The casters.h caster for `pgl::Shape<EPoint>` (the third hand-written caster —
see Architecture below) is what keeps `pgl::Shape` itself invisible from
Python: on the way in it probes each of the fourteen bound classes with an
exact, non-converting `try_cast` (first match wins, no overload-order
ambiguity since there's no implicit conversion involved, unlike the
`Triangulation`/`Polygon` pitfall above); on the way out it dispatches on the
stored alternative and hands it to `nb::cast`, reaching that class's own
already-registered caster. Only the ten bounded shapes (`Point`, `Segment`,
`OrientedSegment`, `Triangle`, `Rectangle`, `Convex`, `MonotoneChain`,
`Polyline`, `Polygon`, `Disk`) can
actually be *stored* — inserting an unbounded shape raises, since pgl's own
`Shape::bbox()` throws for it — but all fourteen remain valid *query* shapes
(e.g. `tree.reportIntersecting(a_line)`), since a query never needs its own
`bbox()`, only pruning against a stored subtree's box. Bound: construction
from a mixed list (with a `leaf_size`), `size`/`empty`/`shapes`, container
sugar (`__len__`/`__iter__`/`__contains__`, the last being exact membership —
distinct from the point-in-shape `in` sugar every fixed-extent shape gets),
`insert`/`rebuild`/`erase`/`contains`, the six spatial queries
(`count`/`report`/`empty` × `Intersecting`/`ContainedIn`), `nearestNeighbor`
(returning `None` on an empty tree, since `AnyShape`'s default/empty state has
no corresponding Python object), and `boundingBoxes`. Not bound: weighted
`sumIntersecting`/`sumContainedIn` (`ShapeTree`'s `WeightFn` template
parameter is left at its default no-op) and the `visitIntersecting`/
`visitContainedIn` early-stop callback overloads — for the same reason
`bind_triangulation.cpp` skips `visitTriangles`/`visitEdges`, every other
pypgl traversal already returns a materialized list rather than taking a
Python callback. Like `Triangulation`, `ShapeTree` is not a fixed-extent shape
(no `contains(Point)`/`pointInside`/`index`/`get`), so it is shielded from the
generic `size()`/`get()`/`__contains__` sugar in `__init__.py` and
`stubgen_patterns.txt`; it does get `Canvas.draw()`/`_repr_svg_` support like
every other shape.

**L1/LInf/Hausdorff distance, `Transformation`, and incremental `Triangulation`
insertion bound** (milestone 8): `.pgl-ref` re-pinned to `e7985c7` pulled in a
batch of upstream additions, all now bound.

`distanceL1`/`distanceLInf` (exact Manhattan/Chebyshev distance) are bound for
the full cross product of all thirteen non-`Disk` shapes via
`PGL_BIND_ALL_L1LINF_DISTANCE` in [src/common.h](src/common.h), mirroring
`PGL_BIND_ALL_SQUARED_DISTANCE`'s coverage exactly. `Disk` is the one asymmetry:
pgl only implements this pair against `Point` so far (an angular scan refined by
golden-section search, always a `float` — no `ResultNumber` template, same as
`Disk.squaredDistance`), tracked upstream in `doc/todo.md` for every other pair.
That one pair is bound by hand in `bind_point.cpp`/`bind_disk.cpp` instead of
through the macro.

`squaredHausdorffDistance`/`hausdorffDistanceL1`/`hausdorffDistanceLInf` are
bound via `PGL_BIND_ALL_HAUSDORFF_DISTANCE`, but only for the six shapes pgl
implements them for — `Point`, `Segment`, `OrientedSegment`, `Rectangle`,
`Triangle`, `Convex` (all convex, so the distance is always attained at a
vertex); `Disk` (no closed form) and `Polygon` (may be non-convex) get neither
method at all. **Important semantic gotcha**: pgl returns the standard
*symmetric* Hausdorff distance `max(h(A, B), h(B, A))`, not a one-sided
directed measure — `a.squaredHausdorffDistance(b)` always equals
`b.squaredHausdorffDistance(a)`, which is easy to miss since the method reads
like a directed `self`-to-`other` call (see the long comment on the macro).

`ShapeTree` gained `nearestNeighborL1`/`nearestNeighborLInf`
([src/bind_shapetree.cpp](src/bind_shapetree.cpp)), same branch-and-bound
traversal as `nearestNeighbor` and the same `None`-on-empty-tree convention,
just minimizing a different metric.

`Triangulation` gained incremental single-vertex insertion
([src/bind_triangulation.cpp](src/bind_triangulation.cpp)): `insert(point)`
subdivides the containing triangle/edge or grows the hull, returning `False`
only if `point` is already a vertex or the triangulation is empty;
`insertDelaunay(point)` does the same and then restores the constrained-Delaunay
property via Lawson flips. For a triangulation built from a polygon, pgl now
documents inserting a point outside the closed polygon as **undefined
behavior** rather than a checked rejection (a behavior change from the point
release this milestone pulled in) — pypgl adds no guard of its own, matching
the C++ contract exactly. A new `Triangulation(points, segments)` constructor
(conforming constrained Delaunay over the *whole* convex hull, nothing carved
away, unlike the polygon constructors) is also bound; unlike the
`Polygon`/point-list overload-order pitfall above, it needs no registration-order
workaround — nanobind tries every overload without implicit conversions first,
and `points`/`segments` already have the exact `vector<Point>`/`vector<Segment>`
types the C++ overload wants, so it always wins over the polygon constructor's
same-arity overload even when `segments` is passed empty (verified empirically,
since nanobind's own resolution order isn't documented in detail).

`Transformation` ([src/bind_transformation.cpp](src/bind_transformation.cpp))
is a new, twelfth bound class: an affine map of the plane (`pgl::Transformation`
in `core/transformation.hpp`), applied to a shape via `t * shape` (transformation
always on the left, matching pgl's own `operator*`) and composed via `t1 * t2`
(applies `t2` first). Unlike every shape it carries no point/label type of its
own — just the matrix-entry type — so it is bound over the module's single
numeric instantiation directly (`::pypgl::Transformation` in
[src/common.h](src/common.h)) with no per-shape variation. It gets its own
hand-written `__repr__`/`__eq__` (pgl's `Transformation` has no `operator<<` or
`operator<`) and is shielded from the indexing/point-in-shape sugar in
`__init__.py` and `stubgen_patterns.txt`, same as `Canvas`/`Triangulation`/
`ShapeTree` — it isn't a shape with vertices either. Applying a transformation
to a `Rectangle` or `Disk` is not bound (pgl itself has no overload for either:
a general affine map turns a rectangle into a parallelogram and a disk into an
ellipse, neither representable by those classes), so it raises a Python
`TypeError` — the runtime equivalent of pgl's compile error. `rotation(radians)`
(an arbitrary-angle rotation) is also deliberately not bound: it's only defined
for a floating-point `ResultNumber` and would return a second, un-bound
`Transformation<double>` instantiation — the same reason `Disk.fbox()` is
skipped. **A real bug surfaced and was fixed while binding `inverse()`**: pgl's
own zero-determinant guard in `Rational::reciprocal()` is only an `assert()`,
which is compiled out under `NDEBUG` — the release build pypgl ships — so
calling `inverse()` on a singular transformation silently corrupted an internal
`Rational` (denominator `0`, marked as already normalized) instead of throwing,
and that corruption later crashed the whole process with an uncaught
`std::domain_error` once something (e.g. printing the result) forced a real
`BigInt` division. `bind_transformation.cpp` now checks `isInvertible()`
explicitly before calling pgl's `inverse()` and raises a clean Python
`ValueError` instead of ever reaching that path — this is a pypgl-side guard,
not an upstream fix.

**`Polyline` + `MonotoneChain`, PDF/Ipe export, `has()` rename** (milestone 9):
`.pgl-ref` re-pinned to `8804140`, which brought two new 1D shapes, a Canvas
overhaul, and one breaking rename.

The two shapes are bound together in
[src/bind_chains.cpp](src/bind_chains.cpp) — both are open polygonal chains
(n − 1 edges for n vertices, no closing edge) that mirror `Convex`/`Polygon`'s
storage (vertices plus a lazy translation), so both are bound **mutable** and
therefore unhashable, and both take `Segment`'s boundary convention (boundary =
the two extreme vertices, relative interior = everything else). What separates
them is what the vertex sequence *means*: `MonotoneChain` treats its input as a
**point set** (sorted lexicographically and deduplicated at construction, so any
input order gives the same chain, and the chain is automatically simple), which
is what buys its O(log n) vertical queries — `indexAtX`/`yAtX`/`isBelow`/
`isAbove` and the strict variants, unique to this shape — and lets it grow via
`insert`. `Polyline` keeps its vertices in **traversal order** (only the
direction is canonicalized, so a polyline equals its own reverse), may therefore
self-intersect (`isSimple()`), and has neither vertical queries nor `insert`.
Both are 13th/14th entries in `PGL_BIND_ALL_PREDICATES` /
`PGL_BIND_ALL_SQUARED_DISTANCE` / `PGL_BIND_ALL_L1LINF_DISTANCE`
([src/common.h](src/common.h)), so every already-bound shape picked up two more
columns for free; neither gets the Hausdorff family (pgl defines it only for the
six convex shapes). `intersection` is bound against the twelve shapes pgl
implements it for — everything except `Disk` and `Polygon` — and always returns
a *list* of `Point`/`Segment` pieces (a chain can meet even a line in
arbitrarily many disjoint places, so there is no single-piece `optional` form
like `Convex`'s). Both are also storable `ShapeTree` elements (they have a
`bbox()`), valid `Triangulation` queries (pgl gives a chain its own traversal:
the directed walk run over each edge in turn), and `Transformation` targets.

**Breaking: `contains()` → `has()`** on `ShapeTree` and `Triangulation`. Upstream
renamed the exact-membership predicate so that a container's "do you store this"
never reads like a shape's geometric `contains()`. pypgl follows (the API mirrors
C++); `shape in tree` still works, and now routes to `has`.

**Breaking: `Canvas.strokeWidth`/`pointRadius` are style commands, not
configuration.** Upstream turned both into stream manipulators taking an SVG
length string, so in
[src/bind_canvas.cpp](src/bind_canvas.cpp) they moved out of the fluent
configuration group and in with `stroke`/`fill` — they are now captured per
shape, by the shapes drawn *after* the call. Each is bound twice, once taking
the string pgl takes and once taking a plain number (disjoint types, so the
overloads never collide). Canvas also gained `toPDF()`/`writePDF(path)` and
`toIPE()`/`writeIPE(path)` alongside the SVG pair; **`toPDF()` returns `bytes`,
not `str`** — pgl's `std::string` there is a binary buffer, not text. None of
the three `write*` methods is fluent: all return `None`, mirroring pgl, where
each returns `void`. (`writePDF`/`writeIPE` briefly returned `Canvas&` upstream,
and pypgl 0.3.0 shipped them fluent because of it, before pgl made the trio
consistent — so 0.3.1 is a small breaking change for anyone who chained off
them.)

`Polygon.pointInside()` is now bound: pgl implements it for a non-convex polygon
(it cuts a diagonal or an ear at a convex vertex), which it previously did not.
`Polygon.verticesContain()` still does not exist upstream, so `Polygon` keeps
its hand-written vertex-query pair rather than `PGL_BIND_VERTEX_QUERIES`.

Not bound: `pointInsideInteriorContainedIn` (a new benchmark-oriented helper
predicate whose coverage is ragged — every shape has it except `Point` and
`Polyline`) and `Polyline`/`MonotoneChain`'s `edgesView`/`orientedEdgesView`
(lazy C++ views; `edges()`/`orientedEdges()` already materialize the same
sequence, which is what a Python caller gets anyway).

**Generated docs + the 42 methods they were promising** (milestone 10):
[doc/raw/doxylink.py](doc/raw/doxylink.py) (see Docs below) checks every method
the pages mention against the *built* module, and it immediately found that the
pages documented 42 mentions of pgl methods pypgl never bound. All of them are
now bound, so the report is clean:

- shared macros in [src/common.h](src/common.h): `PGL_BIND_XY_AT` (`yAtX`/`xAtY`
  on `Segment`/`OrientedSegment`/`Line`/`OrientedLine`/`Ray` — `MonotoneChain`
  keeps its own `yAtX`, which has a different contract), `PGL_BIND_HALFPLANES`
  (`halfplaneAbove`/`halfplaneBelow` on `Line`/`OrientedLine`/`Ray`), and
  `PGL_BIND_ORIENTED_HELPERS` (`orientation`/`rightHalfplane`/`leftHalfplane` on
  the three oriented shapes);
- `Point.swapped`; `Segment`/`OrientedSegment` `containsEndpoint`;
  `OrientedSegment.asOrientedLine`/`asRay`; `Halfplane` picks up
  `PGL_BIND_LINE_HELPERS` (`slope`/`isVertical`/`isHorizontal`, replacing its
  hand-written `isDegenerate`) plus `asOrientedLine`; `Triangle`
  `isRectangle`/`isObtuse`/`isIsosceles`/`circumcircle`/`asConvex`/`asPolygon`;
  `Rectangle` `circumcircle`/`asConvex`/`asPolygon`; `Convex.asPolygon`.

**`orientation` returns an `int`, not an ordering**: pgl's returns a
`std::partial_ordering`, which nanobind has no caster for, so
`::pypgl::orientationSign` in [src/common.h](src/common.h) maps it to -1 (point
to the right of the direction) / +1 (left) / 0 (collinear). The `unordered` case
cannot arise — the comparison is an exact rational determinant, never a NaN.

**An upstream bug this surfaced**: `halfplaneAbove()` returned the half-plane
geometrically *below* the supporting line (and vice versa) on all three of
`Line`/`OrientedLine`/`Ray`. `Halfplane(source, target)` is the closed half-plane
to the *left* of the directed boundary, so "above" is bounded by `min() -> max()`,
not `max() -> min()`. pgl's own unit tests asserted the inverted behavior, and its
`shapes.md` stated it as `orientation(p) <= 0`, which is how it got written that
way. Fixed upstream (pgl commit `7966a5d`, which `.pgl-ref` and
[CMakeLists.txt](CMakeLists.txt) are now pinned to) by swapping the two
implementations and correcting the three unit tests; pypgl's `Line.halfplaneAbove`
had been shipping the inverted result since 0.3.x. The orientation-dependent
`rightHalfplane`/`leftHalfplane` pair was always correct and is unchanged.
Throughout, "above" means larger y — the math convention, not the image one.

`Convex.insert`/`upperHull`/`lowerHull` are documented by *pgl's* `shapes.md` too
but exist in neither library, so they were dropped from
[doc/raw/shapes.md](doc/raw/shapes.md) rather than bound (upstream's copy still
has them).

**`PolygonWithHoles` + `HalfplaneIntersection`, booleans, Minkowski sums, and
the degeneracy family** (milestone 11): `.pgl-ref` re-pinned to `fe8c3ec`, which
brought 156 upstream commits — two new shape classes, two new operation
families, and one cross-cutting addition to every existing shape.

**The re-pin did not build**, and the fix was upstream (pgl commit `fe8c3ec`,
made in this session and pushed). `Shape::squaredDistanceOf` probes
`left.squaredDistance<ResultNumber>(right)` first; `PolygonWithHoles` and
`HalfplaneIntersection` declare that templated form but answered in a hard-coded
`double`, so the probe won and the `double`→`ERational` conversion failed. (The
older shapes escaped only because their `Disk` overloads take no `ResultNumber`
at all and fell through to the untemplated second probe.) The fix generalizes the
whole family: `detail::floating_result_t<ResultNumber>` — the requested type when
it is floating-point, `double` otherwise — so every `Disk` distance now takes a
`ResultNumber` and computes in that width, including the golden-section searches
behind `distanceL1`/`distanceLInf`. `Shape`'s three distance helpers convert
explicitly on both probes. **One exception is load-bearing**: `Disk`'s two
`distanceL1`/`distanceLInf(Shape<PointType>)` overloads keep their untemplated
`double`. Giving them a `ResultNumber` slot makes the rank-forwarding probe
`o.template distanceL1<ResultNumber>(self)` *succeed* by converting the other
shape to `Shape<PointType>`, so `line.distanceL1(disk)` forwards to
`disk.distanceL1(Shape(line))`, which visits the `Line` alternative and forwards
straight back — a stack overflow, not a compile error. pgl's own
`tests/unit/shape.cpp` caught it; a regression test for the original bug was
added there too.

`PolygonWithHoles` ([src/bind_region.cpp](src/bind_region.cpp)) is the 15th
bound class: a closed region, an outer simple polygon minus the *interiors* of
pairwise interior-disjoint holes. Mutable (`addHole`/`eraseHole`) and therefore
unhashable, like `Convex`/`Polygon`. Structural validity is a precondition, not
an invariant — `isValid()` checks it on demand. The subtle predicate is
`isRegular()`: a valid region may pinch shut along a stretch of edge (a **slit**,
material with no area on either side), and `regularized()` returns the pieces of
`closure(interior)` without them. Pinching at an isolated *point* is not a slit.
`isSolidVertex` is **private** upstream and is not bound.

`HalfplaneIntersection`
([src/bind_halfplaneintersection.cpp](src/bind_halfplaneintersection.cpp)) is the
16th: convex like `Convex` but possibly unbounded and possibly empty. Two
conventions bite. A **default-constructed one is the whole plane**, the opposite
of `Convex()`. And its **stored elements are half-planes, not points** — its
corners are implicit and generally rational even for integer half-planes, which
is precisely the case pypgl's single `ERational` instantiation handles exactly.

**The two new shapes take opposite decisions on container sugar**, both
deliberate (see [pypgl/__init__.py](pypgl/__init__.py) and
[src/stubgen_patterns.txt](src/stubgen_patterns.txt)):

- `HalfplaneIntersection` **mirrors C++**: `len`/`[]`/iteration run over its
  half-planes, since that is what pgl gives it `size()`/`get()`/`index()` for.
  Its own corners come from `vertexCount()`/`vertex(i)`/`vertices()`. It needs
  its own stubgen rule, ahead of the generic one, or the stub would promise
  `Point`.
- `PolygonWithHoles` **diverges from C++**: pgl iterates its *holes* and gives it
  no `size()`/`get()` at all (deliberately, so a name shared with a polygon never
  means two things). Python instead flattens the rings' vertices, outer boundary
  first, so a region reads like every other pypgl shape. `holeCount()`/`hole(i)`/
  `holes()` reach the holes. It takes the generic stubgen rule.

Both are 15th/16th entries in `PGL_BIND_ALL_PREDICATES` /
`PGL_BIND_ALL_SQUARED_DISTANCE` / `PGL_BIND_ALL_L1LINF_DISTANCE`
([src/common.h](src/common.h)) — pgl's coverage is complete, so the whole 16×16
matrix compiled first try. Neither gets the Hausdorff family. Both are `Canvas`
targets; `PolygonWithHoles` is a storable `ShapeTree` element, while a
`HalfplaneIntersection` is the one shape whose storability depends on the
*value*: bounded ones store, unbounded ones raise, and either is a valid query.
The `casters.h` `Shape` caster grew to sixteen alternatives.

**Boolean operations and Minkowski sums** are bound through new macros in
[src/common.h](src/common.h) rather than a file of their own — a first attempt at
a separate `bind_booleans.cpp` used `nb::borrow<nb::class_<T>>` to re-open
classes registered in other TUs, which is unnecessary: nanobind resolves argument
types at call time, so registration order across TUs is irrelevant and each shape
can simply call the macro itself. `difference`/`unionWith`/`symmetricDifference`
live on `Polygon`/`PolygonWithHoles`, with the three symmetric ones forwarded
from a `Convex`/`Triangle`/`Rectangle` receiver (`difference` is not symmetric
and forwards nowhere, so those shapes have no `difference` attribute at all). All
return `list[PolygonWithHoles]` and all are **regularized**, so
`a.unionWith(a)` is `a.regularized()`, not `a`.

`minkowskiSum`/`+` is bound for every summable pair per the user's decision to
mirror pgl exactly, so `polygon + rectangle` returns `list[PolygonWithHoles]`
while `triangle + triangle` returns a `Convex`. Two subtleties cost a round of
test failures each: the convex shapes have a **rank-based forwarder** for
non-convex operands (`rectangle.minkowskiSum(polygon)` works), and `Polyline` is
a valid operand for the `Polygon`/`PolygonWithHoles` receivers but
`polyline + polyline` is not a pair. Unsupported pairs (`Disk`, unbounded
operands) are simply not bound, so they raise `TypeError` — the runtime
equivalent of pgl's compile error.

**The degeneracy family** (`isPoint`/`getIfPoint`, `isSegment`/`getIfSegment`,
`isUndefined`) is bound across every shape via three tiered macros in
[src/common.h](src/common.h), since not every shape can collapse every way:
`PGL_BIND_IS_UNDEFINED` for `Line`/`OrientedLine`/`Ray`/`Halfplane` (nothing to
collapse *to*), `PGL_BIND_DEGENERACY_POINT` for `Segment`/`OrientedSegment`/
`Disk`, and `PGL_BIND_DEGENERACY` for the rest. `PolygonWithHoles` has the two
tests but no `getIf*` pair upstream, so it binds them by hand. **The chains are
the case worth remembering**: a straight `MonotoneChain`/`Polyline` satisfies
`isSegment()` but is *not* `isDegenerate()` — a chain is one-dimensional already,
so it has dropped nothing and keeps its relative interior, unlike a flattened
`Triangle`.

**A pypgl-side guard was needed for `Convex.insert`.** C++ accepts only shapes
exposing `vertices()`, making a `Disk` or a `Line` a compile error. In Python
they are not, because every pypgl shape is iterable over its defining points, so
a `Disk` satisfied the `list[Point]` overload and `c.insert(disk)` quietly
inserted the disk's three *boundary* points — whose hull the disk bulges straight
past, so the answer was wrong rather than merely surprising. Five explicit
refusing overloads now raise `TypeError`, and **they must be registered first**:
nanobind takes the first matching overload, and the converting list overload
would otherwise win.

Also bound in this milestone: `Convex.insert`/`upperHull`/`lowerHull` (which
[doc/raw/shapes.md](doc/raw/shapes.md) had dropped back in milestone 10 as
existing in neither library — they exist now); `Polygon.isStarShaped`/
`getStarShapedKernel` (the kernel is a `HalfplaneIntersection`, or `None`);
`MonotoneChain.erase`/`asPolyline`; `Polyline`'s 2-opt edge flip
(`flip`/`flipped`/`flippable`, which take an *old and a new edge* — not a
direction reversal) plus in-place `set`/`insert`/`pushBack`; `Halfplane`'s whole
`intersection` overload set, which it had lacked entirely; `asPolygonWithHoles`
and `asHalfplaneIntersection` across the shapes that have them; `Triangulation`
from a region; and `polyominoRegions`/`polyominoRegionsUpTo`, which omit no
polyomino (108 at size seven against `polyominoes`' 107).

**Breaking: `Polyline` stores its vertices verbatim.** Upstream dropped the
constructor's `trusted` parameter and stopped canonicalizing the traversal
direction, so `vertices()` now returns exactly what was passed and a transform
that moves vertices past each other in the lexicographic order no longer
re-sorts them. Equality, ordering and hashing stay direction-agnostic, so a
polyline still equals its own reverse.


**`PolygonSet`, `Graph`, `Arrangement`, `IntervalTree`, visibility, and the
closed boolean algebra** (milestone 12, version 0.6.0): `.pgl-ref` re-pinned to
`a50a25a`, 162 upstream commits on from `6e8d65b`. Four new bound classes, three
breaking renames, and the two ragged matrices (`intersection`, `minkowskiSum`)
filled in.

**Ground truth came from a probe, not from reading headers.** The pair matrices
are far too large to reason about by hand now, so
`scratchpad/probe.cpp` (generated, throwaway) instantiated
`requires`-guarded calls for all 17×17 pairs of every method family and printed
the demangled return type of each. That produced the exact operand lists the new
macros encode. **A `requires` check is not enough on its own**: it proves the
declaration is viable, not that the body compiles, which is how
`regularizedUnionOf` over a `Triangle` range passed the probe and then failed to
build (fixed upstream in milestone 13, but the lesson stands). Re-run the probe after any re-pin; compile a real call for
anything whose body might be a template that only some operands instantiate.

**`PolygonSet`** ([src/bind_polygonset.cpp](src/bind_polygonset.cpp)) is the
17th bound class: a set of `PolygonWithHoles` components with pairwise disjoint
interiors, whose point set is their union. It is what **closes the regularized
boolean operations** — they used to answer with a bare `list`, which could not
be fed back in, compared, hashed, drawn or measured. It is also the one shape
whose point set need not be connected (`isConnected()`), and its components are
deliberately not nested. Mutable (`addComponent`/`eraseComponent`) and therefore
unhashable, like `Convex`/`Polygon`/`PolygonWithHoles`; it takes the same
container-sugar decision as `PolygonWithHoles` (Python flattens the vertices of
every ring of every component, C++ iterates the components) and hence the generic
stubgen rule.

**Breaking renames, all upstream's:** `unionWith` → `regularizedUnion`;
`isEmpty` → `empty` on `PolygonWithHoles` and `HalfplaneIntersection` (every
shape with an empty state now spells it `empty()`, and `Rectangle`, `Convex` and
`Polygon` *gained* that state — a vertexless `Convex` is now the empty set, not
an undefined shape, and `Rectangle()` is the empty rectangle); and the
region-valued `intersection` is now `regularizedIntersection`, a separate
operation from the literal `intersection` rather than an overload of it. The
Canvas default viewport also shrank from 1000×1000 to 800×800.

**The boolean grids are wider and not square** (see the section comment in
[src/common.h](src/common.h)): all four operations over the six bounded region
types (`Triangle`, `Rectangle`, `Convex`, `Polygon`, `PolygonWithHoles`,
`PolygonSet`), with `difference` also taking an unbounded *argument*, and
`regularizedIntersection` requiring a `PolygonWithHoles` or a `PolygonSet` on
one side — so `rectangle.regularizedIntersection(triangle)` raises where the
other three answer.

**`minkowskiSum` now covers every pair pgl has**, each with the tightest return
type: `Convex`/`Rectangle` for the bounded convex pairs, `Polygon` for a
`MonotoneChain` with a convex body, `HalfplaneIntersection` for the unbounded
convex ones, `Halfplane` when one operand already is one, `PolygonWithHoles`
when the answer is guaranteed connected and `PolygonSet` when it is not, and
`Disk` for two disks. **The two `Disk` sums and `Halfplane + Disk` are bound by
hand**: pgl defaults their result to `double`, which pypgl does not instantiate,
so they request `ERational` explicitly and raise for an irrational radius.

**`intersection` is now a full grid too** — the "still to do" item from
milestone 5. Four macros rather than one, since the operand sets differ by
receiver (chains take no `HalfplaneIntersection`, a `PolygonSet` takes only
shapes with area, a `Disk` still only takes a `Point`).

**`samePointSet`** is bound 17×17 via `PGL_BIND_ALL_SAME_POINT_SET`: geometric
equality across types, which `==` cannot express (it compares representations of
one type, and a `Polygon` with a redundant collinear vertex is unequal to one
without it while covering the same points).

**`Graph`** ([src/bind_graph.h](src/bind_graph.h) +
[src/bind_graph.cpp](src/bind_graph.cpp)) is bound as a template because pgl
instantiates it over two vertex types pypgl exposes: `Point` (visibility,
`Triangulation.asGraph`) and an arrangement's `VertexId` (`ArrangementGraph`),
whose vertex at infinity has no position and so could not be keyed by a point.
Two deliberate departures from C++: `vertices`/`edges`/`neighbors` are
materialized **sorted** copies rather than lazy views over a hash table (so
output never depends on hashing), and `degree` answers `None` rather than -1.
The weighted algorithms take a Python callable whose return value *is* the
weight: `PyWeight` wraps `nb::object` with `<` and `+` through the Python
protocols, so an exact `Fraction` weight stays exact and a `float` one is
allowed — no C++ number type is imposed.

**`Arrangement`** ([src/bind_arrangement.cpp](src/bind_arrangement.cpp)) is
bound as the **single instantiation `Arrangement<Point, Point>`**, i.e. with
`Point` labels, because `Triangulation.voronoiDiagram()` returns exactly that
and a Voronoi diagram should not be a second Python class. Two consequences:
face labels of a plain arrangement start as `Point(0, 0)` (writable via
`setLabel`, which is what recording a per-cell classification wants), and the
label type propagates into the shapes the class hands back — its `SegmentType`
is `Segment<Point, Point>`, a type no caster knows — so `edges()`,
`boundedEdges()` and `halfedge()` go through `stripLabel`, rebuilding each piece
as the bound label-free shape. The three handle families (`VertexId`,
`HalfedgeId`, `FaceId`) are bound as distinct small classes, which is what lets
`locateCell` return "whichever kind of cell contains this point" and the caller
tell them apart with `isinstance`.

**`IntervalTree`** ([src/bind_intervaltree.cpp](src/bind_intervaltree.cpp)) is
bound as two classes, `IntervalTree` and `IntervalTreeY`, since the axis is a
template parameter and a runtime flag would cost the tight storage. Its
projection query family answers a genuinely different question from the exact
one, and — unlike `ShapeTree` — an unbounded shape is rejected as a *query* too,
since every query is projected before anything else happens.

Also bound: `smallestEnclosingDisk`, `closestPair`, `regularizedUnionOf`,
`ShapeTree.kNearestNeighbors`, `Triangulation`'s domain predicates
(`contains`/`interiorContains`/`intersects`/`interiorsIntersect` against all 17
shapes, a *smaller* family than `PGL_BIND_ALL_PREDICATES` since a mesh has no
`boundaryContains`/`separates`/`crosses`), `convexPartition`/`convexCovering` on
`Polygon`/`PolygonWithHoles`/`PolygonSet`/`Triangulation`, the six visibility
methods on those same four classes, `asPolygonSet` across the region shapes, and
`Canvas.view` (framing by an explicit rectangle instead of by the drawing's
bounding box).

**Two upstream bodies did not compile, and the workaround was a narrower
binding** — since fixed upstream and widened in milestone 13 below.
`regularizedUnionOf` over a `Triangle` or `Rectangle` range asked the pieces for
an `edgesView()` neither has, and over a `PolygonSet` range hit the
arrangement's "accepts points, segment-bounded shapes, lines, and rays"
static_assert, so only `Convex`/`Polygon`/`PolygonWithHoles` ranges were bound.
A constraint segment that
*touches* the polygon boundary also silently produces an empty triangulation
(pgl documents interior segments as a precondition), which cost a round of test
failures before the tests moved their walls strictly inside.

**The build dir pins `PGL_INCLUDE_DIR` to `../pgl-public`**, not to `.pgl-ref`:
`build/cp314-*/CMakeCache.txt` was configured that way, and scikit-build-core
reuses it. Both checkouts sat at the same commit here, so it went unnoticed
until an error message named the wrong path. Check the cache before concluding
that a header change did not take.

**`regularizedUnionOf` accepts all six bounded region types** (milestone 13):
`.pgl-ref` re-pinned to `61ad2c5`, one commit on from `a50a25a`, which fixed
both bodies milestone 12 had to route around — `appendCutSegments` now dispatches
on whether a piece carries a lazy `edgesView()` and materializes its `edges()`
otherwise (which is what a `Triangle`/`Rectangle` returns, a fixed-size array),
and a `PolygonSet` range is separated into its components before anything else,
since a set is already a union of regions and is not something an `Arrangement`
can be built from. So [src/bind_algorithms.cpp](src/bind_algorithms.cpp) simply
gained three more overloads (`Triangle`, `Rectangle`, `PolygonSet`) beside the
existing three; the range is still homogeneous, which is the C++ template's
shape, not a binding choice. `simple_boundaries` is now free for a `Triangle`
and a `Rectangle` too — both are convex with a simple boundary by construction,
like a `Convex` — and separating a set's components is also what *weakens* what
the flag has to promise, a boundary stretch two components share being two
distinct origins once they are apart.

**Docs carry no C++ comparisons** (user's instruction, this milestone): the
markdown under [doc/](doc/) and [examples/README.md](examples/README.md) describe
the Python API on its own terms — no "in C++ this is…", no "unlike the C++
original". Source comments and this file are exempt; they are for maintainers.
Seven new examples were ported (`mindisk`, `minkowskisum`, `mst`, `visibility`,
`arrangement`, `voronoi`), and `example3.py`/`example_triangulation2.py` were
renamed to `example_convex.py`/`example_polygon_triangulation.py` to match
upstream.

**Flat coordinate lists and collection drawing** (milestone 14): two
convenience features asked for by the user, both about how much boilerplate a
literal drawing costs.

`Convex`, `Polygon`, `MonotoneChain` and `Polyline` now take **one flat
coordinate list** read in `(x, y)` pairs — `Polygon([0,0, 4,0, 4,4])` — which is
the Python spelling of the `std::initializer_list<NumberType>` constructor pgl
gives those same four shapes (and only those). `pypgl::pointsFromCoords` in
[src/common.h](src/common.h) does the pairing; pgl states the even-count
requirement as an `assert()`, compiled out in the release build pypgl ships, so
it is checked there and raised as a `ValueError` rather than silently dropping
the odd trailing value. **The coordinate overload must be registered after the
point one**: both match an empty list (either builds the same empty shape, so the
tie is harmless), and registration order is what settles it. Nothing else
collides — a `Point` has no `numerator`/`denominator`, so the `ERational` caster
refuses it, and a number is not a `Point`. `Convex`'s *point* constructor also
picked up the `trusted` flag it had always had in C++ (and which
[doc/raw/shapes.md](doc/raw/shapes.md) had been documenting), so the two
overloads agree.

**`Canvas.draw` now takes a collection** and draws its elements one by one, each
capturing the style active at the call: `canvas.draw(polygon.edges())`,
`canvas.draw(triangulation.triangles())`, `canvas.draw([tri, disk, point])`. The
overload takes `nb::iterable` and goes back through `self.attr("draw")`, so a
collection may mix types, hold `None`, and nest. It lives in C++ rather than in
[pypgl/__init__.py](pypgl/__init__.py) with the rest of the sugar because its
whole behavior is a question of *where in the overload set* it sits:
it is registered **after every typed shape overload** (every bound shape is
iterable in the Python layer, so a `Point` would otherwise be drawn as its two
coordinates) and **before the `None`/type-error fallback**. A `str` is iterable
too and a one-character string iterates to itself, which would recurse forever,
so `str`/`bytes` `throw nb::next_overload()` and land in the fallback as the type
error they are. The lambda returns the canvas's own Python object, so the fluent
chain still works; `nb::sig` says so in the stub, which would otherwise promise a
bare `object`.

Every example was then simplified with both: the `points(*coords)` / `ring(...)`
helpers that three of them carried are gone, and a `for x in …: canvas.draw(x)`
loop is now one `canvas.draw(…)`. Every generated SVG is byte-identical to
before, which is the check worth repeating after touching them — with two
pre-existing exceptions that are not the edits' doing: the PDF carries a
creation date, and `example_mindisk.svg` varies run to run because
`smallestEnclosingDisk` is randomized, so the same disk comes back through a
different triple of boundary points (the `<title>` tooltip changes, the drawing
does not). (That second exception went away in milestone 16: the algorithm's
default order is deterministic upstream now, and the example is
`example_enclosing.py`.)

**A shipped segfault, fixed by a re-pin** (milestone 15, version 0.6.1):
`.pgl-ref` re-pinned to `8c1d0bb`, 31 upstream commits on from `61ad2c5`.
`Triangulation`'s four domain predicates crashed the interpreter for every
compound region query — `PolygonWithHoles`, `PolygonSet` and
`HalfplaneIntersection`, twelve combinations in all — because the erased `Shape`
path recursed straight back into itself instead of reaching the concrete
overload. pypgl 0.6.0 shipped it: milestone 12 bound the family against all 17
shapes but tested only the simple ones, so nothing caught it. Fixed upstream
(pgl `987db75`) and now covered by three tests in
[tests/test_triangulation.py](tests/test_triangulation.py). **The lesson is the
one the probe already taught in a different key**: a matrix bound by a macro is
only as tested as its rows — bind 17 columns, test at least one of each *kind* of
column, compound shapes included.

The rest of that re-pin needed no binding change: the red-blue sweep behind
`Polygon`/`PolygonWithHoles`/`PolygonSet` containment and intersection, a
`PolygonWithHoles.pointInside` fast path, an amortized-logarithmic
`IntervalTree.erase` (already bound), and a deterministic default order for
`smallestEnclosingDisk`.

**Minkowski erosion, `convexHull`, the enclosing shapes and A\*** (milestone 16,
version 0.7.0): the new API that same re-pin brought, bound in one pass. The
grid came from a probe (`scratchpad/probe.cpp`, generated and thrown away) that
instantiated `requires`-guarded calls for all 17×17 pairs and printed each
demangled return type — the same method milestone 12 used, and still the only
practical way to get a matrix this size right.

**`minkowskiErosion` mirrors `minkowskiSum` operand for operand**, since pgl
gates both on `MinkowskiSummableConcept`, so the four new macros in
[src/common.h](src/common.h) (`PGL_BIND_EROSION_CONVEX` / `_UNBOUNDED` /
`_REGION` / `PGL_BIND_TRANSLATION_EROSION`) carry the four sum lists verbatim and
each shape simply calls the erosion macro next to its sum macro. There is **no
operator spelling**: pgl gives it none, and `-` already means translation by a
point. What differs is the answer, and two differences are load-bearing:

- **A convex receiver answers a `HalfplaneIntersection` even when it is
  bounded**, where the sum would have given a `Convex`. Eroding a convex shape
  is clamping each of its own half-planes by the operand's support function, and
  that never leaves the form. It also means the operand counts only through its
  hull, so a non-convex operand and its `convexHull()` erode identically.
  `Rectangle` ⊖ `Rectangle` is the one pair closed under it, as under the sum.
- **An erosion disconnects**, so a bounded non-convex receiver answers a
  `PolygonSet` and never a single `PolygonWithHoles` — a dumbbell eroded by
  anything wider than its handle is two regions, for operands that are in no way
  degenerate. This is the one structural difference from the sum.

The `Disk` pairs are hand-bound for the same reason its sums are: `Disk` ⊖ `Disk`
is a `Disk` or **`None`** when the eroding disk is the larger (the sum always
answers), and `Disk` ⊖ `Halfplane` is empty — pgl models that with an
`EmptyShape` pypgl does not bind, so the lambda returns `None`, which is how
every other empty result already reaches Python. `Point` ⊖ `Disk` is exact and
macro-free, since "nothing" needs no square root.

**A pre-existing bug this surfaced**: `Halfplane` + `Disk` has *never* worked in
pypgl, in either direction or either spelling. Sliding a boundary out by a radius
moves it along that boundary's own **unit** normal, and normalizing is a square
root even when the radius is exact — so pgl refuses `ERational` outright,
however the disk was built. The docstrings said "raises for an irrational
radius", which is wrong; they now say it always raises and why, and
[doc/raw/todo.md](doc/raw/todo.md) records it as a gap rather than a feature.
The erosion counterpart behaves identically and is bound anyway, so the refusal
at least names its reason.

Also bound: **`convexHull()`** on the twelve shapes that have one — the eleven
bounded ones other than `Disk` (whose hull is itself and is no polygon), plus
`HalfplaneIntersection`, which raises when unbounded; the four unbounded shapes
have no `bbox` to begin with — via `PGL_BIND_CONVEX_HULL`. **`Convex`'s two
smallest enclosing shapes**, which read a convex boundary and so live on that
class alone: `smallestEnclosingDisk()` (the method form of the free function)
and `smallestEnclosingRectangle()`, which returns a `HalfplaneIntersection`
rather than a `Rectangle` because the smallest-**area** one is generally tilted
and a `Rectangle` is axis-aligned by definition. **`Graph.shortestPath`'s A\*
overload**, a fifth `lowerBound` argument wrapped in the same `PyWeight` as the
weight, so an exact bound stays exact; the extra argument is what tells the two
overloads apart. And **`chainCount()`** on `Polygon`/`PolygonWithHoles`, the
count the new containment fast paths price themselves on.

Not bound: **the `Triangulation` handle API** (`TriId`/`VertexId`/`getShape`/
`getId`/`label(TriId)`, the largest single addition in the re-pin) — the user's
call. Per-triangle labels go with it, being reachable only through a handle.
Also skipped: `Polygon.containsChainBased` and `sweepContains`, which upstream
documents as benchmark-only ("reach for `contains` rather than this"), the same
call as the existing `containsCollinear` skip.

Examples: `example_mindisk.py` became `example_enclosing.py` (both enclosing
shapes, matching upstream's rename) and `example_motion.py` is new — a polygonal
robot routed through a room by eroding the room by the robot and running A\* over
the reduced visibility graph, which is the erosion's headline use. Its printed
output matches the C++ example's exactly, and its SVG matches too **up to the
order of the graph edges**: pypgl's `Graph.edges()` is a sorted materialized list
rather than a hash-table walk, so the same lines come out in a different document
order. Every pre-existing figure is byte-identical, which stays the check worth
repeating. [examples/README.md](examples/README.md)'s gallery is three columns
now, with one-line descriptions, following upstream.

**nanobind 3.0.0 broke the release run twice, in two different ways** (0.7.0).
`pyproject.toml` asked for `nanobind>=2.0`, so CI's isolated build env picked up
the major released 2026-08-22 while the local venv kept its pinned 2.13.0 —
which is exactly why 0.7.0 built clean here and failed in CI, and why a green
`main` run is the release gate rather than a formality. **A local build proves
nothing about the build environment CI resolves.** Two distinct failures, in
this order:

1. **cp39 fails at CMake configure time**, before a line is compiled: nanobind 3
   refuses Python < 3.10. It is first in the matrix, so it took all three
   platform jobs down and hid the second failure entirely.
2. **nanobind 3 does not compile on the Windows runner at all** (clang-cl
   19.1.5), inside its own `nb_backend_slots.h` on a constexpr in the
   `NB_SLOT_ALIAS` macro. pypgl's sources are never reached. This only surfaced
   after cp39 was gone — the first failure was masking it.

So the build is **capped at `nanobind>=2.0,<3`**, restoring the 2.x line the
green 0.6.0 run used (2.15.0 builds clean here and passes all 980 tests). Lift
the cap once nanobind fixes the Windows bug. Worth knowing when doing so:
nanobind 3 builds fine on Linux, passes the whole suite, and emits a
**byte-identical `_pgl.pyi`** — so there is nothing to adopt beyond the fix, and
that stub equality is worth re-checking rather than assuming.

**`cp39` stays dropped anyway** — a deliberate choice, not a forced one, since
the cap holds the build on a 2.x that still supports 3.9. Python 3.9 went
end-of-life in October 2025, nanobind 3 has dropped it, and re-adding the wheels
now would only mean dropping them again when the cap lifts. `requires-python` is
`>=3.10`, so pip holds 3.9 users on 0.6.0 rather than erroring, and a release is
15 wheels instead of 18.

**Open-segment containment, a triangulation point-location index, and greedy
independent sets** (milestone 17, version 1.0.0): `.pgl-ref` re-pinned to
`f1c9dad`, 26 upstream commits on from `8c1d0bb`. Most of that batch is
performance with no API attached — batched edge-disjoint flips behind
`Polygon.untangle`, a faster `regularizedUnion`, faster `ShapeTree`
construction, a rewritten Bentley-Ottmann status order, an `Arrangement`
simple-boundaries construction path — plus a benchmark rework whose recorded
history moved to its own repository. Nothing was removed or renamed upstream, so
this is the first re-pin since milestone 9 that breaks nothing. Three things
were genuinely new and all three are bound.

**`interiorContainsInterior(segment)`** on `Polygon`, `PolygonWithHoles` and
`PolygonSet` (`PGL_BIND_INTERIOR_CONTAINS_INTERIOR` in
[src/common.h](src/common.h)) is the predicate `interiorContains` cannot express:
the segment's *endpoints* may rest on the boundary as long as everything strictly
between them stays strictly inside. A sightline between two boundary vertices is
exactly that shape, which is what the predicate is for. The operand is a
`Segment` and only a `Segment` — upstream gates it on `SegmentConcept`, which an
`OrientedSegment` does not satisfy, so there is no second overload to bind. A
`PolygonSet` answers componentwise, so a segment through the pinch point two
touching components share is refused: it lies in the union but in no single
component.

**`Triangulation.buildPointLocation()`** plus `hasPointLocation()` /
`hasCurrentPointLocation()` / `clearPointLocation()`
([src/bind_triangulation.cpp](src/bind_triangulation.cpp)) — an arrangement over
a *coarsening* of the mesh (one sampled vertex per `bit_width(V)`) that seeds the
visibility walk beside the query instead of at the previous query's answer. It
mirrors the `Arrangement` trio already bound in
[src/bind_arrangement.cpp](src/bind_arrangement.cpp), with one difference worth
keeping straight: **this index survives every edit.** It only chooses where the
walk starts, so it stays *correct* across an `insert` or a `flip` and merely
loses seed quality; `hasCurrentPointLocation()` is the fourth method, and it
reports exactly that — whether rebuilding would find anything new. Testing it
needs strictly-interior queries: a query on a vertex or an edge gets *an*
incident triangle, which one being unspecified with or without the index, so the
"answers exactly as the bare walk" test offsets its grid queries by
`(1/3, 1/4)` to miss the mesh's horizontal, vertical and ±1-slope edges.

**`Graph.independentSet()`** on both bound instantiations
([src/bind_graph.h](src/bind_graph.h)): a maximal — not maximum — set of pairwise
non-adjacent vertices, greedy from the lowest degree up. It is returned **sorted**,
per the `vertices()`/`edges()` convention, but sorting fixes only the *order* of
the answer: equal-degree ties are broken inside pgl by its hash-table walk, so
*which* of several equally good sets comes back can vary between runs. The
docstring and [doc/raw/data_structures.md](doc/raw/data_structures.md) say so
rather than promising a stability the binding cannot deliver.

**Not bound: `Triangulation.asArrangement()`**, which labels each face with the
triangle's `TriId`. It returns `Arrangement<PointType, TriId>`, and pypgl binds
the single instantiation `Arrangement<Point, Point>` (milestone 12) and left the
`TriId` handle API unbound (milestone 16). Binding it means either a second
`Arrangement` class plus the handle type, or stripping the labels — which throws
away the only reason the method exists. The existing decision stands.

**Version 1.0.0**, the first stable release: the API has been additive-only
since 0.6.1, the seventeen shape classes cover pgl's own set, and the matrices
(predicates, distances, booleans, Minkowski, intersection, `samePointSet`) are
complete rather than ragged. `requires-python` stays `>=3.10` and the
`nanobind>=2.0,<3` cap from 0.7.0 is unchanged — the Windows bug that forced it
is still open, so lifting it is still the separate piece of work milestone 16
describes.

**`BitMatrix`, the digital-geometry grid** (milestone 18, version 1.1.0):
`.pgl-ref` re-pinned to `1e4e6c1`, two upstream commits on from `f1c9dad`. One
new class, one new enum, two new free functions — and one collision with the
project's most load-bearing rule.

**`BitMatrix` is the one bound class pypgl cannot hold over its own `Point`.**
pgl constrains it to `std::signed_integral` coordinates, since a cell of the grid
*is* an integer position, so `BitMatrix<Point>` (ERational) is ill-formed by
construction. The cells are therefore stored over `Cell = pgl::Point<int64_t>`
(`::pypgl::Cell` / `::pypgl::BitMatrix` in [src/common.h](src/common.h)), which
never surfaces in Python: no second point type is bound, and the boundary is
crossed in exactly two directions. Going in, a cell is named either by a pair of
plain ints (the fast spelling, and the one a loop wants) or by an ordinary
`Point`, which `toCell` checks with pgl's own `gridCoordinate`. Coming out, every
shape a matrix produces is widened into the bound ERational class by pgl's
cross-point-type converting constructors, and the measures request `ERational`
explicitly, so they stay exact. int64_t is not an arbitrary choice: it is exactly
what pgl itself picks for an ERational shape (`grid_number_t<Rational<BigInt>>`),
so `polygon.asBitMatrix()` and `BitMatrix(polygon)` name the same grid.

**The second of the two re-pinned commits is what made that clean.** At
`2996e20` — the commit that added `BitMatrix` — `asBitMatrix` forwarded the
shape's own point type and so did not compile for an exact shape at all, and
narrowing one by hand *silently truncated*: a probe put a `7/2` coordinate
through and got `3` back, no complaint. `1e4e6c1` ("Throw on a non-integer
coordinate in asBitMatrix") added `gridCoordinate`, which checks
`Rational::isInteger()` exactly and range-checks against the grid type, and gave
`asBitMatrix` a `ResultNumber` defaulting through `grid_number_t`. So the whole
narrowing/guard layer this milestone was budgeting for does not exist — pypgl
reuses pgl's check rather than reimplementing it, which is also what keeps the
message identical wherever a bad coordinate enters.

**pgl's own `innerRaster`/`outerRaster` could not be bound directly**, and the
workaround is a fifteen-line loop in
[src/bind_bitmatrix.cpp](src/bind_bitmatrix.cpp). They build each cell over the
*result grid's* point type and hand it to `shape.contains`/`intersects`, and
`Shape<Point>`'s predicates only accept shapes over their own point type — so an
int64 cell against an ERational shape does not compile (the error names
`ShapeAlternative`). The binding runs the same loop with the cell widened to an
exact `Rectangle` first, which costs nothing since the corners are whole. That
also buys `AnyShape` support, so all 17 shapes rasterize. **The no-window
overload is pypgl's own**: pgl's requires an integer shape, which an ERational
one is not, so the window defaults to the bounding box **rounded outward** —
outward rather than nearest, because that is the property `outerRaster` exists
to have. An unbounded shape raises there and rasterizes fine over an explicit
window, the same split `ShapeTree` already makes between storing and querying.

Binding decisions worth keeping straight: `BitMatrix` is **not** a `Shape`
alternative, so `casters.h` is untouched, it is no `ShapeTree`/`IntervalTree`
element, and it is not a row of `PGL_BIND_ALL_PREDICATES` — pgl gives its five
shape predicates against another `BitMatrix` only. It is mutable and hence
unhashable, and not a fixed-extent shape, so it is shielded from the generic
point sugar in [pypgl/__init__.py](pypgl/__init__.py) and
[src/stubgen_patterns.txt](src/stubgen_patterns.txt) like `Triangulation`/
`ShapeTree`, binding its own container protocol instead: `len` is the number of
set cells, iteration yields them as `Point`s, and **`point in matrix` asks
whether that *cell* is set**, not whether the point lies in the covered region.
`__repr__` is hand-written (pgl gives `BitMatrix` no `operator<<`, only the
`Canvas` one), as is the comparison set. `latticeView`/`cellsView` are not bound
(lazy views, the same call as `Polyline.edgesView`), nor is `fbox`.

**The two readings of a cell are the thing to remember.** Unprefixed, a cell is
the unit square it covers — the predicates, the measures, the symmetries,
`minkowskiSum`/`minkowskiErosion`, all of which commute with `asPolygonSet`.
Prefixed with `lattice`, it is the single point at its lower-left corner, which
is what makes a structuring element behave. The pair differs by a cell:
`reflected()` maps `c` to `-c - (1,1)` where `latticeReflected()` maps it to
`-c`, and the region sum comes out one cell wider and taller in each direction
than the lattice sum. Transposition is the one operation the two readings agree
on.

`asBitMatrix()` is bound on `Polygon`/`PolygonWithHoles`/`PolygonSet` through
`PGL_BIND_AS_BIT_MATRIX` in [src/common.h](src/common.h), each shape calling it
in its own file (the milestone 11 lesson: nanobind resolves argument types at
call time, so cross-TU registration order is irrelevant). `GridAdjacency` is
bound as an `nb::enum_`, and `Canvas.draw(matrix)` streams the matrix's polygon
set, so touching cells merge into one path — `canvas.draw(matrix.rectangles())`
is how to draw the cells as separate elements.

**A pre-existing gap this surfaced**, unrelated to `BitMatrix` and now fixed:
`Transformation * PolygonWithHoles`, `* PolygonSet` and
`* HalfplaneIntersection` were never bound, though pgl supports all three (a
test rotating a matrix's polygon set is what tripped over it). The `__mul__`
list in [src/bind_transformation.cpp](src/bind_transformation.cpp) stopped at
`Polygon`, where milestone 8 left it, and the three shapes that landed after it
were never added — which is what a matrix-shaped API costs when one list is
written out by hand rather than by a macro over a shared shape list.

Not added: an example. [examples/](examples/) is one file per upstream C++ one
and upstream ships no `BitMatrix` example, so adding one would break that
mapping.

**`latticePoints` and cell ranges** (milestone 19, version 1.2.0): `.pgl-ref`
re-pinned to `bfa6e08`, two upstream commits on from `1e4e6c1` — a small re-pin
that renames and breaks nothing, so both additions are pure new surface.

**`latticePoints()`** — the integer points a shape contains, boundary included
as `contains` counts it, each of them once — is bound on the twelve bounded
shapes pgl gives it to via `PGL_BIND_LATTICE_POINTS` in
[src/common.h](src/common.h): every bounded shape except `Point` (which has none
upstream: it is its own answer), plus `HalfplaneIntersection`, which raises when
unbounded. The four unbounded shapes cover infinitely many and do not have it.
Ordering is the shape's own — increasing everywhere except an `OrientedSegment`
(source to target) and a `Polyline` (edge by edge in traversal order, each point
kept where the chain first reaches it, so a shared vertex, a crossing and a
retraced stretch are each reported once).

**The one binding decision is `ResultNumber = BigInt`, asked for explicitly
rather than defaulted.** The default for an ERational shape is the same int64_t
grid `asBitMatrix()` uses, and pgl throws when a lattice point does not fit it —
but a pypgl `Point` holds a BigInt coordinate, so that ceiling would be one the
*binding* imposes on an answer the bound type represents perfectly well: a short
segment sitting at x = 10^20 has three lattice points and no int64_t to name
them with. Measured at ~3.5x the int64_t path end to end (180k points: 6ms
against 1.7ms, widening included), which the Python object creation dominates
anyway — and the widening to the bound `Point` allocates a BigInt per coordinate
either way, which is most of what the narrower type would have saved.

**A range of cells for `BitMatrix`**: the new `BitMatrix(cells)` constructor
(one set cell per point, over the smallest window holding them, so the result is
its own `trimmed()`) plus range `set`/`reset`/`flip` (same reading, over the
window the matrix already has, a cell outside it dropped as for the single-cell
forms). Both spellings a single cell already took are accepted item by item — a
`Point` or a pair of plain ints — and they may be mixed.

**pgl refuses a shape or another matrix as such a range, and in Python that
refusal has to be made at runtime.** Upstream constrains the overload with
`!AnyShapeConcept && !is_bit_matrix_v`; here every shape iterates over its
defining points and a matrix over its set cells, so both would convert quietly
and answer the wrong question — a `Polygon` coming in as the ring of its
vertices (a boundary, not a point cloud) and a matrix trimmed out of the window
it carries. Rather than the ~68 refusing overloads the milestone 11
`Convex.insert` pattern would have cost here, `toCells` in
[src/bind_bitmatrix.cpp](src/bind_bitmatrix.cpp) takes `nb::iterable` and probes
once: `nb::isinstance<BitMatrix>`, then a non-converting `try_cast<AnyShape>`,
which is exactly the seventeen-class probe the `casters.h` `Shape` caster
already does. Each raises a `TypeError` naming what to pass instead
(`shape.vertices()`, `matrix.lattice()`, or `shape.latticePoints()`). The
`nb::iterable` overloads are registered **after** every typed one, the milestone
14 `Canvas.draw` ordering: that is what keeps `BitMatrix(polygon)` reaching its
rasterizing constructor rather than the cell-range one.

**An upstream doc bug this surfaced, not fixed here** (pgl's checkout is the
user's): in `shape/disk.hpp` and `shape/polygonwithholes.hpp`, commit `08992e0`
inserted `latticePoints`' doc block *and declaration* between `bbox()`'s doc
comment and `bbox()` itself. Doxygen therefore gives `latticePoints` the `bbox`
brief and leaves `bbox` with `latticePoints`' `@return`/`@throws`, which is why
those two rows of [doc/shapes.md](doc/shapes.md) carry a bounding-box tooltip on
a lattice-points link. The generated pages will correct themselves on the next
re-pin once the two comment blocks are reordered upstream; there is nothing to
change on the pypgl side.

Not added: an example, for the same reason milestone 18 added none — upstream
ships no example for either addition.


The package directory is [pypgl/](pypgl/) (so `import pypgl` works); the compiled
extension is `pypgl._pgl`. Binding sources live in [src/](src/).

## What pypgl is

Python bindings for **Pangolin** (`pgl`), a header-only C++20 exact-geometry
library at `github.com/gfonsecabr/pgl`. The public API mirrors the C++ one:
`import pypgl` and type/method names stay unchanged. pgl is consumed via CMake
`FetchContent` (pinned `GIT_TAG`), never vendored or submoduled.

## Load-bearing design decisions

These are the choices that constrain everything else; violating them defeats the
point of the project:

- **One numeric instantiation only:** `pgl::ERational = pgl::Rational<pgl::BigInt>`.
  Do **not** bind the `double` / `Rational<int64_t>` family. This is what keeps the
  binary and API surface bounded. "The number type" / `Num` always means `ERational`.
  `BitMatrix` (milestone 18) is the one class that cannot obey this — pgl
  constrains it to `std::signed_integral` cells — so it holds
  `Cell = pgl::Point<int64_t>` internally while keeping the rule where it counts:
  no second point type is *bound*, cells enter as ints or ordinary `Point`s, and
  everything it hands back is widened to the ERational classes.
- **Exactness is a hard contract.** Coordinates are accepted as `int`, `Fraction`,
  or `"a/b"` strings. **Reject `float` loudly** with a message pointing at the
  accepted forms — never silently approximate.
- **nanobind, not pybind11.** Chosen for small binaries / fast compile because
  binding a templated header-only library is instantiation-heavy.
- **Bind concrete shapes, not the `Shape` variant wrapper.** Each shape is its own
  Python class. `ShapeTree` (milestone 7 above) is the one deliberate exception —
  a spatial index that mixes shape types needs a type-erased element, so it stores
  `pgl::Shape<PointType>` internally, kept invisible from Python by a dedicated
  caster (see Architecture below).

## Architecture

The hand-written plumbing is three type casters in `src/casters.h`; everything
else is mechanical `.def(...)`:

1. `pgl::BigInt` ↔ Python `int` — via decimal string round-trip (lossless; uses
   pgl's existing `operator<<`/`operator>>`). A machine-int fast path is a later
   optimization, not a correctness requirement.
2. `pgl::ERational` ↔ Python `fractions.Fraction` — built from `numerator()` /
   `denominator()` (stored in lowest terms), each term flowing through the BigInt
   caster so arbitrarily large coordinates round-trip.
3. `pgl::Shape<EPoint>` ↔ a concrete pypgl shape object — used by `ShapeTree`
   and `IntervalTree` (see milestones 7 and 12); probes the seventeen bound
   classes with an exact `try_cast` going in, dispatches on the stored
   alternative via `nb::cast` coming out.

What falls out for free from pgl's typed API (built-in nanobind casters):
`std::optional<T>` → `T`/`None`; `std::variant<Point, Segment, …>` → the concrete
shape (so `intersection` returns `None` / `Point` / `Segment` with no sentinels);
`operator<<` → `__repr__`; `operator==`/`<`/`std::hash` → usable in `set`/`dict`.

**Layering:** the compiled `_pgl` extension stays minimal (just `.def`s). All
Pythonic sugar lives in `pgl/__init__.py`: vertex iteration, `point in shape` →
`shape.contains(point)` (point-in-shape only — keep shape-vs-shape as explicit
methods), pickling, and `_repr_svg_` for inline Jupyter rendering via `Canvas`.

**Translation units:** one `bind_*.cpp` per shape group (point, segment, lines,
polygons, polygon, region, polygonset, chains, canvas, and one per data
structure: triangulation, shapetree, bitmatrix, intervaltree, arrangement, graph) so heavy template instantiation compiles in parallel and objects
stay small. A `PGL_BIND_PREDICATES(cls, OtherTypes...)` macro in `src/common.h`
keeps the seven uniform predicates (`contains`, `boundaryContains`,
`interiorContains`, `intersects`, `interiorsIntersect`, `separates`, `crosses`)
consistent across classes; each predicate is overloaded per accepted shape type.

`PGL_BIND_ALL_PREDICATES`, `PGL_BIND_ALL_SQUARED_DISTANCE` and
`PGL_BIND_ALL_SAME_POINT_SET` list all **seventeen** shapes, including
themselves, so every pair works in both directions;
`PGL_BIND_ALL_L1LINF_DISTANCE` lists sixteen (no `Disk`, which pgl implements
only against a `Point`) and `PGL_BIND_ALL_HAUSDORFF_DISTANCE` only the six
bounded convex ones.

## Build & test

Build backend is `scikit-build-core` (PEP 517); `nanobind` is a build dependency
found via `python -m nanobind --cmake_dir` (not FetchContent). Development uses a
venv:

```bash
python3 -m venv .venv
.venv/bin/pip install scikit-build-core nanobind pytest
.venv/bin/pip install -e . --no-build-isolation   # --no-build-isolation so CMake finds the venv's nanobind
.venv/bin/python -m pytest tests/ -q
```

Re-run the `pip install -e .` line after editing any `src/*.cpp` — the editable
install rebuilds the extension; importing alone does not.

**pgl headers.** pgl is header-only and (currently) ships no CMake target or
release tags, so we do **not** `FetchContent_MakeAvailable` a `pgl::pgl` target.
[CMakeLists.txt](CMakeLists.txt) resolves `PGL_INCLUDE_DIR` in this order: an
explicit `-DPGL_INCLUDE_DIR=…`, then an in-tree `.pgl-ref/` checkout (the offline
default — a gitignored `git clone` of github.com/gfonsecabr/pgl), then FetchContent
from GitHub. `.pgl-ref/` is the local copy of the real pgl API; **read it to get
exact signatures** rather than trusting the design doc's header paths (which differ,
e.g. real headers are `include/shape/point.hpp`, `include/implementation/io.hpp`).

Co-develop against another pgl checkout:
`pip install -e . --no-build-isolation -C cmake.define.PGL_INCLUDE_DIR=/path/to/pgl/include`

Wheels (later milestone): `cibuildwheel` in GitHub Actions; ship generated
`_pgl.pyi` stubs + `py.typed`.

## Examples

[examples/](examples/) is the Python port of pgl's `examples/`, one file per C++
one, plus a `README.md` and a `Makefile` (`make` runs them all, `make clean`
removes what they wrote — the C++ Makefile compiles, this one only runs). Their
generated `.svg`/`.pdf`/`.ipe` are gitignored and excluded from the sdist.
Its `README.md` is a **gallery** like upstream's, so one copy of each output
is tracked under [examples/figures/](examples/figures/) — `make figures` runs
every example and refreshes them; the sdist leaves that directory out too.

They are the closest thing to an integration test of the *user-facing* API, and
they earn it: porting `example3.cpp` immediately turned up that
`Convex.verticesCentroid` was never bound, though `Polygon` and
`PolygonWithHoles` both had it. Re-run them after changing a binding.

That one prompted a full audit — every class's doxygen-documented C++ methods
against `dir(cls)` — which found seven more pre-existing omissions, all now
bound: `orientedEdges` on `Triangle`/`Rectangle`/`Convex` (it was bound on
`Polygon` and the chains, and pgl documents it for all of them), `Triangle.a/b/c`
(the counterpart of `Disk.a/b/c`, which was bound), `Rectangle.center`/`width`/
`height`/`insert`, `MonotoneChain.edgesCross`, the in-place `rotate90`/`scale*`
on `PolygonWithHoles`/`HalfplaneIntersection` (every other mutable shape had
them), and the named `minkowskiSum` on the translation-only shapes — `shape +
point` always worked there, so which spelling was available depended on which
shape you held. The audit script is worth re-running after a re-pin; it is a few
lines of regex over the headers plus a `dir()` diff.

What it still reports is noise or deliberate: iterator typedefs, `detail::`
helpers, private members, `fbox`/`pointInsideInteriorContainedIn`/labels (all
deliberately unbound), and the in-place transforms on the *immutable* shapes,
which by contract only get the value-returning `rotated90`/`scaled*`. A handful
of genuinely marginal ones are left alone: `Segment.area`/`twiceArea`/`edges`
(uniformity methods for generic C++ code), `containsCollinear` (an unchecked
precondition fast path for `contains`), `Line.asSegmentFor`,
`OrientedLine.crossingOrder`, `Convex.edgesAtX`/`maxIndex`, and
`Polyline.polygonIntersection`.

Two places where a port cannot be literal, both called out in the examples'
README: the canvas is methods rather than a stream, and `float` coordinates are
rejected so trigonometric layouts must `round()` first. (A third — that only the
fixed-size shapes took flat coordinates — went away in milestone 14, which is
also what removed the `points(*coords)` helper three examples carried.)

## Docs

Same split as pgl: the editable pages are [doc/raw/](doc/raw/)`*.md` and
**[doc/](doc/)`*.md` is generated — never edit the latter (it carries a
"do not edit" banner). [doc/raw/doxylink.py](doc/raw/doxylink.py) is the pypgl
port of pgl's script of the same name; it rewrites inline-code API mentions
(`s.midpoint()`, `pgl.convexHull(points)`, a bare `Segment`) into links to pgl's
doxygen site, with the C++ `@brief` as the link's hover tooltip.

```bash
.venv/bin/python doc/raw/doxylink.py           # report only
.venv/bin/python doc/raw/doxylink.py --write   # regenerate doc/*.md
```

The one structural difference from pgl's version: **the authority on what exists
is the built extension, not the headers.** The script `import pypgl`s (so run it
with the venv interpreter, after a rebuild) and links a mention only if the
method is actually *bound*; doxygen — run on `.pgl-ref/` for its tag file (urls)
and XML (briefs) — merely supplies where to point. That asymmetry is the point:
pypgl binds a subset of pgl, so the report separates

- `not-bound` — the page documents a real pgl method pypgl does not expose
  (**genuine doc drift**; 42 such mentions existed when the script landed, e.g.
  `Segment.yAtX`, `OrientedSegment.orientation`, `Triangle.circumcircle`);
- `no-doxygen` — a bound method with no C++ counterpart (Python-only sugar, e.g.
  `Canvas.draw`, which replaces pgl's `operator<<`), left unlinked;
- `not-in-context` / `no-context` — a mention naming another class, or one in a
  section with no class heading (the generic `A.contains(B)` in
  [doc/raw/shape_methods.md](doc/raw/shape_methods.md)). Both are left alone.

A bare `- Other methods:` line in a class section is a placeholder, filled with
every **bound** method of that section's class that got no link in the section
(dropped entirely when there is nothing left to list, so it doubles as a
self-maintaining drift catcher in the fully-documented sections). The class comes
from the nearest heading naming one (`### Oriented Segment` → `OrientedSegment`);
`` `t.collinear()`{Point} `` overrides it for one mention.

## Gotchas learned while binding

- **pgl's `BigInt::operator>>` reads a whole whitespace-delimited token**, so it
  cannot drive `Rational::operator>>`'s `"a/b"` parse (the `/` gets swallowed). The
  `ERational` caster therefore parses string coordinates through Python's
  `fractions.Fraction` instead, then uses the uniform numerator/denominator path.
- **Predicate/intersection methods are templated** on the result/other-shape type
  with defaults (`ResultNumber = NumberType = ERational`). Bind them via lambdas
  (`[](const Self&, const Other&){ return self.method(other); }`) so the default
  instantiation is chosen; don't try to take their address.
- The `in`/iteration sugar is added Python-side in [pypgl/__init__.py](pypgl/__init__.py)
  by assigning to the nanobind classes (`Point.__contains__ = …`), which nanobind
  permits.
