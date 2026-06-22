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

## Next

### Milestone 2 — Core shapes (the current next step)
Bind the remaining non-experimental shapes, each as its own translation unit, and
extend the predicate/intersection matrix to cover every pair.

- New TUs (mirror the design doc's grouping):
  - `src/bind_lines.cpp` → `Line`, `OrientedLine`, `Ray`, `Halfplane`
    (headers: `.pgl-ref/include/shape/{line,orientedline,ray,halfplane}.hpp`)
  - `src/bind_polygons.cpp` → `Triangle`, `Rectangle`, `Convex`
    (headers: `.pgl-ref/include/shape/{triangle,rectangle,convex}.hpp`)
  - Also bind `OrientedSegment` (likely in `bind_segment.cpp` or a `bind_lines.cpp`).
- Register each new `bind_*` in [src/module.cpp](src/module.cpp) and add the
  `.cpp` to `nanobind_add_module` in [CMakeLists.txt](CMakeLists.txt).
- Add `Num`/`Point` aliases as needed; define each shape alias as
  `pgl::Shape<EPoint>` analog (e.g. `using Triangle = pgl::Triangle<Point>;`).
- Extend `PGL_BIND_PREDICATES(cls, Self, Other)` calls so every bound shape lists
  every other bound shape as an `Other`. Some pairs are not-yet-implemented in pgl
  and **throw at runtime** but still compile — that's fine; if a pair fails to
  *compile*, drop that one overload and note it.
- Constructors mirroring C++ ones; accessors (`.vertices()`, `.area()`,
  `.centroid()`, `.min()/.max()`, `.length()`, etc.); constructions
  (`intersection`, `distance`, `bounding`, `dual`/`polar` duality).
- Tests per shape: constructors, predicate samples, exact measures, and the
  `variant`→concrete-type results for richer intersections.

Watch for: predicate methods are templated with defaults — always bind via
lambdas, never by address (see CLAUDE.md gotchas). Verify each shape has a
`std::hash` specialization (they do, in `core/hash.hpp`) before using
`bind_value_semantics`.

### Milestone 3 — Notebook UX
- Bind `Canvas` (`.pgl-ref/include/visualization/canvas.hpp`): construction,
  `draw(...)`, styling (`stroke`/`fill`/`strokeWidth`/…), `size`/`scale`,
  `toSVG()`, `writeSVG(path)`.
- Add `_repr_svg_()` to `Canvas` (returns `toSVG()`).
- Add `_repr_svg_()` to each shape by wrapping it in a one-shot `Canvas`
  (Python-side in `__init__.py`, like the existing sugar).

### Milestone 4 — Packaging & distribution
- `cibuildwheel` GitHub Actions across manylinux/macOS/Windows + CPython versions.
- Generate `_pgl.pyi` stubs (nanobind stubgen) and ship them next to `py.typed`.
- Confirm `pypgl` name on PyPI; publish.
- Consider STABLE_ABI builds (nanobind, Python ≥ 3.12) to cut wheel count.

### Milestone 5 — Experimental
- `Disk` and `Polygon` once their pgl C++ predicates settle; keep gated so the
  stable public API does not churn.

## Cross-cutting TODOs
- Pickling via `__getstate__`/`__setstate__` (serialize coordinates).
- Once pgl ships a `pgl::pgl` CMake target + release tags, switch CMake to
  `find_package`/pinned `FetchContent` and drop the manual include-dir handling.
- Decide whether to bind the `Shape` variant wrapper at all (design says no —
  bind concrete shapes only).
