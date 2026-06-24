# pypgl roadmap

Implementation plan and status. The design contract is [pypgl.md](pypgl.md); this
file tracks concrete progress and the next actionable steps. Read
[CLAUDE.md](CLAUDE.md) first for build commands and the gotchas already learned.

## Done

### Milestone 1 — PoC (commit `a016bc7`)
- Build system: [pyproject.toml](pyproject.toml) (scikit-build-core),
  [CMakeLists.txt](CMakeLists.txt) (nanobind via `python -m nanobind --cmake_dir`,
  pgl headers via `PGL_INCLUDE_DIR` → in-tree `.pgl-ref/` → FetchContent).
- The two casters in [src/casters.h](src/casters.h): `BigInt ↔ int`,
  `ERational ↔ fractions.Fraction` (accepts int/Fraction/`"a/b"`; rejects float).
- [src/common.h](src/common.h): `Num`/`Point`/`Segment` aliases,
  `bind_value_semantics<T>` (repr/str/ordering/eq/hash), `PGL_BIND_PREDICATES` macro.
- `Point` and `Segment` bound ([src/bind_point.cpp](src/bind_point.cpp),
  [src/bind_segment.cpp](src/bind_segment.cpp)) with the 7-predicate matrix,
  `intersection`, measures, accessors.
- Python sugar in [pypgl/__init__.py](pypgl/__init__.py): `point in shape`,
  segment iteration.
- 18 passing tests in [tests/](tests/).

### Milestone 2 — Core shapes (commit pending)
All remaining non-experimental shapes are bound, each in its own translation
unit, with the full predicate matrix.

- New TUs: [src/bind_lines.cpp](src/bind_lines.cpp) (`Line`, `OrientedLine`,
  `Ray`, `Halfplane`) and [src/bind_polygons.cpp](src/bind_polygons.cpp)
  (`Triangle`, `Rectangle`, `Convex`). `OrientedSegment` was added to
  [src/bind_segment.cpp](src/bind_segment.cpp). All wired into
  [src/module.cpp](src/module.cpp) and [CMakeLists.txt](CMakeLists.txt).
- Aliases for every shape (the pgl `E*` aliases over `EPoint`) in
  [src/common.h](src/common.h), plus a `PGL_BIND_ALL_PREDICATES(cls, Self)`
  macro that binds the 7 predicates of `Self` against **all ten** bound shapes
  (full 10×10 matrix). pgl declares every predicate for every pair (explicit
  overloads + rank-based forwarding), so all pairs compile; not-yet-implemented
  pairs throw at runtime, as designed.
- Constructors mirror the C++ ones; accessors/measures bound per shape
  (`.vertices()`, `.edges()`, `.area()`, `.twiceArea()`, `.centroid()`,
  `.min()/.max()`, `.midpoint()`, `.diameter()`, `.source()/.target()`,
  `.opposite()`, `.asLine()/.asSegment()`, `dual`/`polar`, `isVertical` …).
  Templated measures (area/centroid/dual) are bound via no-arg lambdas to pick
  the default `ResultNumber = ERational`.
- Vertex iteration (`__iter__`/`__len__`/`__getitem__`) and `point in shape`
  extended to all the new shapes in [pypgl/__init__.py](pypgl/__init__.py).
- Exact `squaredDistance` (`PGL_BIND_ALL_SQUARED_DISTANCE` in
  [src/common.h](src/common.h)) bound across the full matrix; returns the exact
  squared Euclidean distance as a `Fraction` (`ResultNumber` defaults to
  `ERational`). The approximate float `distance` stays Point-only, mirroring pgl.
- 25 new tests in [tests/test_core_shapes.py](tests/test_core_shapes.py)
  (43 total): constructors, exact measures, cross-shape predicates, exact
  squared distances, and the `variant`→concrete-type intersection results
  (line∩line→Point/Line, ray∩ray→Segment/Ray, triangle∩line→Segment, etc.).

Intersection scope (deliberately partial; expand later): bound for pairs whose
results are points / 1D shapes (all in the bound set). 2D∩2D and `Halfplane`
intersections — whose results can be a `Convex`/`Polygon` region — are left to a
later milestone so no binding returns an unbound type.

Required a pgl fix pulled into `.pgl-ref`: `std::hash` for `Line`-family shapes
and `Convex::intersection(Point)` were not compatible with `Rational<BigInt>`
coordinates (commits `de4b7d0` + the `Convex.intersection(Point)` follow-up).

Also required a pgl fix (pulled into `.pgl-ref`, commit `0544ec6`): `Convex` had
no `squaredDistance(Halfplane)` overload and no rank-based forwarding for
`squaredDistance`, so the Convex×Halfplane pair would not compile. With that
added, all ten shapes use the uniform `PGL_BIND_ALL_SQUARED_DISTANCE` macro and
the full squared-distance matrix is exposed.

Line-like helpers and duality (commit pending). Three new macros in
[src/common.h](src/common.h) — `PGL_BIND_LINE_HELPERS` (`slope`, `isVertical`,
`isHorizontal`, `isDegenerate`), `PGL_BIND_COLLINEAR` (vs `Point` + the five
line-like shapes) and `PGL_BIND_PARALLEL` (vs the five line-like shapes) — are
applied to `Segment`, `OrientedSegment`, `Line`, `OrientedLine`, `Ray`. `Point`
gained `dual`/`polar` (→ `Line`); `Segment` gained `asLine`; both segment kinds
and `Point` gained the exact `lengthL1`/`lengthLInf` and `distanceL1`/
`distanceLInf` (no square root, so exact `Fraction`), alongside the existing
approximate L2 `length`/`distance`. 11 new tests in
[tests/test_line_helpers.py](tests/test_line_helpers.py) (55 total).

Required a pgl fix pulled into `.pgl-ref` (commit `48c9614`): `OrientedLine`
declared `parallel` against `Line`/`OrientedLine`/`Segment`/`OrientedSegment`
but not `Ray`, while every other line-like shape (and `Ray.parallel(OrientedLine)`)
had the full matrix; the missing overload was added upstream so the uniform
`PGL_BIND_PARALLEL` macro compiles for `OrientedLine`.

Exact bounding box (commit pending). `bbox()` (returns the already-bound exact
`Rectangle`) is bound on the six bounded shapes — `Point`, `Segment`,
`OrientedSegment`, `Triangle`, `Rectangle`, `Convex`. The unbounded shapes
(`Line`, `OrientedLine`, `Ray`, `Halfplane`) have no `bbox`, mirroring pgl.
pgl's `fbox()` is deliberately **not** bound: it returns a float-coordinate
`Rectangle<Point<double>>`, which conflicts with the one-ERational-instantiation
/ reject-float design contract. 3 new tests in
[tests/test_core_shapes.py](tests/test_core_shapes.py) (58 total).

Operators and transforms (commit pending). Two new macros in
[src/common.h](src/common.h) — `PGL_BIND_OPERATORS` (translate by a `Point` via
`+`/`-`, scale by a scalar via `*`/`/`, both orders) and `PGL_BIND_TRANSFORMS`
(value-returning `rotated90`, `scaledUpX/Y`, `scaledDownX/Y`). `Point` gets its
own arithmetic (`+`/`-` of points, unary `-`, scalar `*`//) plus the transforms.

Mutability split, decided here and reflected in
[src/common.h](src/common.h)'s `bind_value_semantics(cls, hashable)`:

- **Fixed-size shapes** (`Point`…`Rectangle`): immutable + hashable. Only the
  value-returning operators/transforms are bound; `s += p` rebinds (Python
  fallback), so a shape used as a dict key is never mutated underneath a live
  container.
- **`Convex`** (and, later, `Polygon`): variable-size, so it keeps pgl's lazy
  translation offset and is bound **mutable** — `__iadd__`/`__isub__`/`__imul__`/
  `__itruediv__` mutate in place and return self (O(1) translate), and the void
  `rotate90`/`scaleUpX/Y`/`scaleDownX/Y` mutators are bound too. Following
  Python's mutable⇒unhashable rule it is bound with `hashable = false`
  (`__hash__` set to `None`), so it cannot be a dict key / set member and thus
  can never corrupt a container when mutated. Its value-returning operators are
  synthesized as copy-then-compound-assign (Convex has no free operators).

12 new tests in [tests/test_transforms.py](tests/test_transforms.py) (70 total).

Vertex/interior queries (commit pending). A `PGL_BIND_VERTEX_QUERIES` macro in
[src/common.h](src/common.h) binds `pointInside()` (an exact interior point —
`ResultNumber` defaults to `ERational`, so pgl's `/2` or `/4` stays exact),
`verticesContain(point)`, and `index(point)` on every shape **except `Point`**,
which has no interior; `Point` instead gets `index(value)` over its two
coordinates. `index` returns `None` when not found (mapped from pgl's `-1` via
`std::optional`), rather than a Python-unsafe `-1`.

Indexing on every shape (commit pending). `PGL_BIND_INDEXING` binds pgl's
`size()` and cyclic `get(i)` on all ten shapes, and
[pypgl/__init__.py](pypgl/__init__.py) wires `len`, `shape[i]`, and iteration to
them uniformly. So every shape is indexable/iterable over its defining points —
the polygons over their vertices, the line-like shapes over their two defining
points, and `Point` over its two coordinates. `shape[i]` is cyclic (wraps modulo
`size()`, negatives count from the end, never raises); iteration still
terminates because it goes through `__iter__` over `range(size())`. 11 new tests
in [tests/test_vertex_queries.py](tests/test_vertex_queries.py) (81 total).

Rectangle bounding-box constructors (commit pending). `Rectangle([p0, p1, …])`
builds the componentwise bounding box of points (placement-new factory like
`Convex`'s; empty raises `ValueError`). A second factory takes any `nb::iterable`
of bounded shapes and unions each element's `bbox()`, so `Rectangle([seg, tri,
convex])` works — and, unlike pgl's homogeneous range constructor, the iterable
may **mix shape types** (and points). Unbounded shapes expose no `bbox()`, so
they raise and are correctly excluded. pgl's `minmax`/trusted bool flag is
deliberately not exposed — it skips the bbox computation and could produce an
invalid rectangle. 3 new tests in
[tests/test_core_shapes.py](tests/test_core_shapes.py) (84 total).

- `Disk` — **done** ([src/bind_disk.cpp](src/bind_disk.cpp)): bound as its own
  complete class once its pgl C++ predicates settled. Exact
  `center`/`squaredRadius`/`bbox`/`pointInside`; the irrational `radius`/`area`
  and disk `squaredDistance` return `float`; float-coordinate
  `diameter()`/`fbox()` are not bound. Its column is not yet added to the other
  shapes' matrices (pgl still lacks `Triangle::contains(Disk)` and
  `Convex::squaredDistance(Disk)`).

### Milestone 3 — Notebook UX (commit pending)
`Canvas` is bound in its own TU ([src/bind_canvas.cpp](src/bind_canvas.cpp),
wired into [src/module.cpp](src/module.cpp) and [CMakeLists.txt](CMakeLists.txt)).
pgl's stream API (`canvas << pgl::stroke("red") << shape`) does not map to Python,
so each stream operation is exposed as a method:

- **Configuration** (fluent — each returns the same canvas): `scale`, `width`,
  `height`, `size`, `margin`, `pointRadius`, the numeric `strokeWidth`, `borders`.
- **Style** (fluent; applied to the *current* style, so only shapes drawn
  afterwards capture it, exactly like the C++ stream): `stroke`, `fill`,
  `fillOpacity`, `strokeOpacity`, each taking an SVG string.
- **`draw(shape)`** — one overload per bound shape (all 11, including `Disk`),
  equivalent to `<< shape`; returns the canvas so draws chain.
- **`toSVG()`** → SVG string; **`writeSVG(path)`** → file.

The fluent self-returns use `nb::rv_policy::reference_internal` so the canvas
stays alive behind the returned handle. `_repr_svg_` is added Python-side in
[pypgl/__init__.py](pypgl/__init__.py): on `Canvas` it returns `toSVG()`; on every
shape it wraps the shape in a one-shot `Canvas().draw(self).toSVG()`, so shapes
render inline in Jupyter. 37 new tests in
[tests/test_canvas.py](tests/test_canvas.py) (139 total): SVG well-formedness
(parsed with `xml.etree`), fluent chaining, per-shape rendering, style capture
order, borders, arrowhead markers, `writeSVG`, and the `_repr_svg_` hooks.

## Next

### Milestone 4 — Packaging & distribution

Type stubs (commit pending). `_pgl.pyi` is generated at build time by
`nanobind_add_stub` in [CMakeLists.txt](CMakeLists.txt) and installed next to the
extension and the existing `py.typed` (PEP 561). The stub is generated from the
**bare** `_pgl` module (`MODULE _pgl`, `PYTHON_PATH` = the built `.so`'s dir),
i.e. before [pypgl/__init__.py](pypgl/__init__.py) runs — which both keeps the
qualified names clean and dodges a stubgen quirk where the runtime-patched
lambdas otherwise leak in as an invalid `from pypgl import <lambda>`. The
Python-layer sugar that `__init__.py` adds at import time (per-shape `__len__`/
`__getitem__`/`__iter__` over the defining points, and `__contains__` for
`point in shape`) is re-added via a pattern file,
[src/stubgen_patterns.txt](src/stubgen_patterns.txt): a `Point.__suffix__` rule
(coords → `Fraction`), a generic `*.__suffix__` rule for the other shapes
(→ `Point`), and a `Canvas` shield (no point sugar). 18 new tests in
[tests/test_stubs.py](tests/test_stubs.py) (163 total): artifacts shipped, stub
parses, every public class declared, no leaked patches, sugar present on shapes
but not `Canvas`.

Wheels CI (commit pending). `cibuildwheel` is configured in
[pyproject.toml](pyproject.toml) (`[tool.cibuildwheel]`) and driven by
[.github/workflows/wheels.yml](.github/workflows/wheels.yml): it builds wheels for
CPython 3.9–3.13 on Linux (`manylinux_2_28` — GCC 12 for full C++20; the legacy
`manylinux2014`/GCC 10 is not enough), macOS arm64 (`macos-14`) + x86_64
(`macos-13`), and Windows, plus an sdist. PyPy, 32-bit, and musllinux are skipped
for now. pgl has **no native dependencies** (its `BigInt` is pure C++), so no
system libraries are installed in the build — CMake `FetchContent`s the pinned pgl
commit (the sdist omits the gitignored `.pgl-ref/`), so the pin in
[CMakeLists.txt](CMakeLists.txt) must move in lockstep with `.pgl-ref` for
reproducible CI wheels. The matrix is **native-arch only (no QEMU/cross)** because
`nanobind_add_stub` imports the freshly built `_pgl` to emit `_pgl.pyi`, which
requires the build host to run the target binary; this also means every wheel is
verified importable during its own build, on top of the `pytest` test step.
Verified locally by building the sdist and a wheel from it (stub + `py.typed`
present, 163 tests green).

Still to do:
- Confirm `pypgl` name on PyPI and configure Trusted Publishing for the `publish`
  job (gated on `v*` tags, OIDC — no API token); then tag a release to publish.
- Consider STABLE_ABI builds (nanobind, Python ≥ 3.12) to cut wheel count.
- Consider adding aarch64 Linux + musllinux once a non-stub-importing build path
  (or a separate stub-gen step) removes the native-host requirement.

### Milestone 5 — Experimental
- `Polygon` once its pgl C++ predicates settle; keep gated so the stable public
  API does not churn.

## Cross-cutting TODOs
- Pickling via `__getstate__`/`__setstate__` (serialize coordinates).
- Once pgl ships a `pgl::pgl` CMake target + release tags, switch CMake to
  `find_package`/pinned `FetchContent` and drop the manual include-dir handling.
- Decide whether to bind the `Shape` variant wrapper at all (design says no —
  bind concrete shapes only).
