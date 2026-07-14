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
[.github/workflows/wheels.yml](.github/workflows/wheels.yml) — CPython 3.9–3.13 on
`manylinux_2_28` (GCC 12 for C++20), macOS arm64 (`macos-14`), and Windows, plus
sdist. macOS x86_64 (`macos-13`) was dropped — GitHub is retiring the Intel
runners, so the jobs sat queued for hours and timed out. pgl has no native deps,
so the build only `FetchContent`s the **pinned** pgl commit (kept in lockstep with
`.pgl-ref`, since the sdist omits the gitignored `.pgl-ref/`). Native-arch only
(no QEMU/cross) because `nanobind_add_stub` imports the just-built `_pgl` to emit
`_pgl.pyi`.

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

Still to do: broaden `intersection` to 2D∩2D among `Triangle`/`Rectangle`/
`Convex` themselves (unrelated to `Polygon`, whose own matrix is now
complete), and consider STABLE_ABI to cut the wheel count before the next
release. (pgl-side gaps that keep pypgl's matrices ragged are tracked in
[doc/todo.md](doc/todo.md): chain ∩ `Disk`/`Polygon`, L1/LInf distance to a
`Disk`, Hausdorff distance for the non-convex shapes.)
[pypgl.md](pypgl.md) remains the authoritative design contract —
update it in lockstep if a decision changes.

**`Triangulation` bound** (milestone 6): a mutable mesh over a fixed vertex
set (pgl's `algorithm/triangulation.hpp`) is bound in
[src/bind_triangulation.cpp](src/bind_triangulation.cpp) over the module's own
`Triangle`/`Segment` pair (`::pypgl::Triangulation` in
[src/common.h](src/common.h) — `.pgl-ref` re-pulled to commit `99ac4d2` for
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
made in this same session and pulled by re-pinning `.pgl-ref` to `dcea2a3`:
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
insertion bound** (milestone 8): `.pgl-ref` re-pinned to `3b0729b` pulled in a
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
`.pgl-ref` re-pinned to `91b6714`, which brought two new 1D shapes, a Canvas
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
way. Fixed upstream (pgl commit `5dabc73`, which `.pgl-ref` and
[CMakeLists.txt](CMakeLists.txt) are now pinned to) by swapping the two
implementations and correcting the three unit tests; pypgl's `Line.halfplaneAbove`
had been shipping the inverted result since 0.3.x. The orientation-dependent
`rightHalfplane`/`leftHalfplane` pair was always correct and is unchanged.
Throughout, "above" means larger y — the math convention, not the image one.

`Convex.insert`/`upperHull`/`lowerHull` are documented by *pgl's* `shapes.md` too
but exist in neither library, so they were dropped from
[doc/raw/shapes.md](doc/raw/shapes.md) rather than bound (upstream's copy still
has them).

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
3. `pgl::Shape<EPoint>` ↔ a concrete pypgl shape object — `ShapeTree`-only (see
   milestone 7 above); probes the fourteen bound classes with an exact `try_cast`
   going in, dispatches on the stored alternative via `nb::cast` coming out.

What falls out for free from pgl's typed API (built-in nanobind casters):
`std::optional<T>` → `T`/`None`; `std::variant<Point, Segment, …>` → the concrete
shape (so `intersection` returns `None` / `Point` / `Segment` with no sentinels);
`operator<<` → `__repr__`; `operator==`/`<`/`std::hash` → usable in `set`/`dict`.

**Layering:** the compiled `_pgl` extension stays minimal (just `.def`s). All
Pythonic sugar lives in `pgl/__init__.py`: vertex iteration, `point in shape` →
`shape.contains(point)` (point-in-shape only — keep shape-vs-shape as explicit
methods), pickling, and `_repr_svg_` for inline Jupyter rendering via `Canvas`.

**Translation units:** one `bind_*.cpp` per shape group (point, segment, lines,
polygons, chains, canvas) so heavy template instantiation compiles in parallel and objects
stay small. A `PGL_BIND_PREDICATES(cls, OtherTypes...)` macro in `src/common.h`
keeps the seven uniform predicates (`contains`, `boundaryContains`,
`interiorContains`, `intersects`, `interiorsIntersect`, `separates`, `crosses`)
consistent across classes; each predicate is overloaded per accepted shape type.

`Disk` and `Polygon` are no longer gated or asymmetric: both `PGL_BIND_ALL_PREDICATES`
and `PGL_BIND_ALL_SQUARED_DISTANCE` now list all fourteen shapes, including
themselves, so e.g. `triangle.contains(disk)` and `disk.intersects(triangle)`
both work (see milestone 5's `Disk` follow-up in Project status above) — pgl
closed every remaining pair upstream.

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
