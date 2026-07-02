# pypgl — Python bindings for Pangolin

Pangolin (`pgl`) is a C++ geometry library available at `github.com/gfonsecabr/pgl`.
A design plan for `pypgl`, a Python package that exposes pgl library to Python.
To use the libray the user should write
`import pypgl` and all type and method names remain unchanged.

## Guiding decision: one number type, `Rational<BigInt>`

Pangolin shapes are templated on a numeric type. Python is dynamically typed, so
binding the full `{shapes} × {int, double, Rational<i64>, Rational<BigInt>, …}`
matrix would explode the API surface and the binary. **We bind exactly one
instantiation: `pgl::ERational = pgl::Rational<pgl::BigInt>`.** No `double` family, no
`Rational<int64_t>`.

Throughout this document, "the number type" / `Num` means `pgl::ERational`,
and "a coordinate" is a value of that type.

## Binding library: nanobind

Use [**nanobind**](https://github.com/wjakob/nanobind).

- Same author and nearly identical API to pybind11, but dramatically smaller
  binaries and faster compile/runtime — which matters because binding a
  templated header-only library is instantiation-heavy.
- C++17+, so pgl's C++20 is fine.
- First-class `scikit-build-core` integration and `.pyi` stub generation.


## The two custom type casters (the only real plumbing)

Everything else is `.def(...)` calls. Only two conversions need hand-written
casters; both live in a single `casters.h` shared by all translation units.

### 1. `pgl::BigInt` ↔ Python `int`

- **Py→C++:** read the Python `int`. For values that fit a machine integer, use
  the fast path; otherwise convert via decimal string (Python `int` → `str` →
  feed through `pgl::BigInt`'s `operator>>` / stream parse). String is lossless
  and simple; optimize the small-int path later if profiling demands.
- **C++→Py:** `pgl::BigInt` → decimal string (`operator<<`) → Python `int(str)`.

`pgl::BigInt` already provides `operator<<` / `operator>>`
(`include/core/bigint.hpp`), so the string route needs no library change.

### 2. `pgl::ERational` ↔ Python `fractions.Fraction`

- **C++→Py:** build `fractions.Fraction(numerator(), denominator())` from the
  reduced terms (`Rational` stores in lowest terms; `numerator()` /
  `denominator()` in `include/core/rational.hpp`). Each term goes through the
  BigInt caster, so arbitrarily large coordinates round-trip.
- **Py→C++:** accept `Fraction`, `int`, **and** `str` (e.g. `"3/2"`); reject
  `float` loudly (a `float` cannot represent an exact rational — forcing the user
  to be explicit preserves the exactness contract).

With these two casters in place, coordinates flow naturally and the rest of the
binding is mechanical.

## What maps for free

pgl already returns std-typed results, which land on idiomatic Python with the
built-in casters:

| pgl | Python | mechanism |
| --- | --- | --- |
| `std::optional<T>` | `T` or `None` | built-in caster |
| `std::variant<Point, Segment, …>` (intersection results) | the concrete shape object | built-in caster |
| `operator<<` (`io.hpp`) | `__repr__` / `__str__` | bind the stream insertion |
| `operator==`, `operator<`, `std::hash` | `__eq__`, `__lt__`, `__hash__` | shapes work in `set` / `dict` |
| `pgl::ERational` | `fractions.Fraction` | custom caster (above) |
| `pgl::BigInt` | `int` | custom caster (above) |

Consequence worth calling out: `seg.intersection(other)` returns `None`, a
`Point`, or a `Segment` **automatically** — no out-params, no sentinels. That
falls straight out of the existing typed API.

## Shapes to bind

Bind each concrete shape as its own Python class (Pythonic), **not** the `Shape`
variant wrapper. The `Shape::Variant`
(`include/geometry/shape.hpp`) enumerates the full set:

```
Point, Segment, OrientedSegment, Line, OrientedLine, Ray,
Halfplane, Rectangle, Triangle, Convex, Disk, Polygon
```

The seven predicates are uniform across shapes and bound on every class:

```
contains, boundaryContains, interiorContains,
intersects, interiorsIntersect, separates, crosses
```

Predicate overloading: each predicate takes any other shape. Bind one overload
per accepted shape type and let nanobind's overload resolution dispatch — this
mirrors the C++ overload set directly and avoids exposing the variant.

## Pythonic surface

Bound directly from C++:

- **Constructors** mirroring the C++ ones, e.g. `Point(x, y)`,
  `Segment(p, q)` and `Segment(x1, y1, x2, y2)`, `Triangle(...)`, etc., with
  coordinates accepted as `int`, `Fraction`, or `"a/b"` strings.
- **`__repr__` / `__str__`** from `io.hpp`.
- **`__eq__`, `__lt__`, `__hash__`** → usable in `set` / `dict` immediately.
- **Accessors** (`.x()`, `.y()`, `.min()`, `.max()`, vertices, `.length()`,
  `.area()`, `.centroid()`, `.midpoint()`, `.diameter()`, …). All constructive
  results are exact rationals — no result-type argument.
- **Constructions:** `intersection`, `distance`, `bounding`, duality, etc.

Added in the thin Python layer (`pgl/__init__.py`), where it is cheap:

- **Iteration** over polygon / convex vertices (`__iter__`, `__len__`,
  `__getitem__`).
- **`in` operator:** map `point in shape` to `shape.contains(point)` (only the
  unambiguous point-in-shape case; keep shape-vs-shape as explicit method calls
  to avoid confusion).
- **`fractions` / `int` helpers** for pulling coordinates back out.
- **Pickling** via `__getstate__` / `__setstate__` (trivial given value
  semantics — serialize the coordinates).

### Jupyter visualization (high priority)

`include/visualization/canvas.hpp` already has `toSVG()` returning a
`std::string` and `writeSVG(path)`. Bind `Canvas`, then:

- Add **`_repr_svg_()`** to `Canvas` (returns `toSVG()`), so a canvas renders
  inline in notebooks with zero extra work.
- Add `_repr_svg_()` to individual shapes by wrapping each in a one-shot
  `Canvas`. Inline rendering of shapes and results is the single biggest
  usability win for a geometry library and should ship early.

## Repository layout

`pypgl` is its **own repository**, separate from pgl. This keeps pgl
dependency-free, header-only, and with CI that only runs g++/clang++, while the
binding gets independent versioning, release cadence, and Python tooling. It
consumes pgl through CMake `FetchContent` (see below) rather than a git
submodule — same reproducible pinning, none of the submodule workflow friction.

```
pypgl/                      # separate repo; pgl is fetched, not vendored
  pyproject.toml            # scikit-build-core backend
  CMakeLists.txt            # FetchContent nanobind + pgl; links pgl::pgl
  src/
    casters.h               # BigInt<->int, Rational<BigInt><->Fraction
    common.h                # the Num typedef, shared helpers, predicate macro
    module.cpp              # module def; calls bind_* registrars
    bind_point.cpp
    bind_segment.cpp
    bind_lines.cpp          # Line / OrientedLine / Ray / Halfplane
    bind_polygons.cpp       # Triangle / Rectangle / Convex
    bind_canvas.cpp
    # bind_disk.cpp, bind_polygon.cpp  (experimental, later)
  pgl/
    __init__.py             # re-exports + Pythonic sugar + _repr_svg_
    py.typed
    _pgl.pyi                # generated stubs
  tests/
    test_predicates.py
    test_exact.py           # the 10**50 round-trip, Fraction in/out
    test_intersection.py    # optional->None, variant->concrete type
```

- **`_pgl`** is the compiled extension, kept minimal (just `.def`s).
- **`pgl/__init__.py`** re-exports from `_pgl` and adds the Python-level sugar.
- **One translation unit per shape group** so the heavy template instantiation
  compiles in parallel and objects stay small — the main reason to prefer
  nanobind here. A small `PGL_BIND_PREDICATES(cls, OtherTypes...)` macro in
  `common.h` keeps the seven-predicate boilerplate uniform.

## Consuming pgl via CMake FetchContent

The binding pulls pgl in at configure time, pinned to a tagged release, and links
an interface target — no submodule, no vendored headers.

```cmake
include(FetchContent)

FetchContent_Declare(
  pgl
  GIT_REPOSITORY https://github.com/gfonsecabr/pgl
  GIT_TAG        v0.1.0          # pin a release tag (or a commit), not main
)
FetchContent_MakeAvailable(pgl)

# nanobind, fetched the same way (or found via its installed CMake package):
FetchContent_Declare(
  nanobind
  GIT_REPOSITORY https://github.com/wjakob/nanobind
  GIT_TAG        v2.x.y
)
FetchContent_MakeAvailable(nanobind)

nanobind_add_module(_pgl
  src/module.cpp src/bind_point.cpp src/bind_segment.cpp
  src/bind_lines.cpp src/bind_polygons.cpp src/bind_canvas.cpp)

target_link_libraries(_pgl PRIVATE pgl::pgl)   # carries include/ + C++20
```

Why FetchContent over a submodule, for a header-only dependency:

- **Reproducible without the tax.** Pinning `GIT_TAG` gives the same exact-version
  guarantee a submodule SHA does, but contributors never need
  `--recurse-submodules`, never land in detached-HEAD edits, and CI needs no
  recursive checkout flag.
- **Local override for co-development.** When editing pgl and the binding in
  tandem, point the build at a local checkout instead of the fetched copy:

  ```bash
  cmake -DFETCHCONTENT_SOURCE_DIR_PGL=/path/to/pgl ...
  ```

  Pinned tag by default; live local source while hacking — strictly better than a
  submodule for both cases.

This depends on two small additions **in the pgl repo** (useful to all C++
consumers, not just Python):

1. A minimal root `CMakeLists.txt` exposing an `INTERFACE` target `pgl::pgl` that
   carries `include/` (`target_include_directories(... INTERFACE include)`) and
   `target_compile_features(... INTERFACE cxx_std_20)`. This is what makes
   `FetchContent` and `find_package` clean.
2. **Release tags** (even `v0.x`), so the binding pins something meaningful rather
   than a bare commit SHA.

Until those land, FetchContent can still point at `GIT_TAG main` and the binding
can set include dirs by hand — but the interface target + tags are the right
foundation and cheap to add.

## Build, packaging, distribution

- **Build backend:** `scikit-build-core` (PEP 517, CMake-based; nanobind ships a
  template). CMake `FetchContent`s both nanobind and pgl and links `pgl::pgl`
  (see *Consuming pgl via CMake FetchContent* above).
- **Wheels:** `cibuildwheel` in GitHub Actions → manylinux / macOS / Windows
  across supported CPython versions. Pure C++20 + header-only keeps this simple.
- **Stubs:** generate `_pgl.pyi` with nanobind's stubgen and ship `py.typed` for
  editor autocomplete and type checking.
- **PyPI name:** confirm availability — `pypgl`.
- **Versioning:** track the pgl library version; the binding is a thin layer over
  tagged library states.

## Risks and mitigations

- **Compile time / binary size.** One instantiation only (`Rational<BigInt>`) and
  per-shape translation units keep it bounded; nanobind's lean codegen helps
  most. Revisit only if wheels get large.
- **BigInt caster performance.** The decimal-string round-trip is fine for
  correctness-first usage; add a machine-int fast path if profiling shows it
  matters.
- **`Disk` / `Polygon` still in flux.** Keep them experimental and behind a
  feature gate until their C++ predicates are complete, so the public Python API
  doesn't churn.
- **`float` inputs.** Reject them explicitly with a clear error pointing at
  `Fraction` / `int` / `"a/b"`, rather than silently approximating.

## Suggested milestones

1. **PoC:** `casters.h` (both casters) + `Point` and `Segment` with their
   predicates and `intersection`; `pip install -e .`. Prove the exact round-trip
   (`10**50`, `Fraction` in/out) and the `optional`→`None` / `variant`→concrete
   mappings feel right.
2. **Core shapes:** add `Line`, `OrientedLine`, `Ray`, `Halfplane`, `Triangle`,
   `Rectangle`, `Convex`; full predicate matrix; constructions and measures.
3. **Notebook UX:** `Canvas` + `_repr_svg_` on canvas and shapes.
4. **Packaging:** `cibuildwheel`, stubs, PyPI publish.
5. **Experimental:** `Disk`, `Polygon`, `Triangulation` once their C++ contracts settle.
