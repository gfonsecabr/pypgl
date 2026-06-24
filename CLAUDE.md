# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

**Core shapes done** (milestones 1–2 of [pypgl.md](pypgl.md)): all
shapes are bound — `Point`, `Segment`, `OrientedSegment`,
`Line`, `OrientedLine`, `Ray`, `Halfplane`, `Triangle`, `Rectangle`, `Convex`,
`Disk` — each with the full 7-predicate × 10-shape matrix
(`PGL_BIND_ALL_PREDICATES` in [src/common.h](src/common.h)), constructors,
accessors/measures, and typed `intersection` results for the 0D/1D-result pairs.
The two casters work and the exact round-trip / `optional`→`None` /
`variant`→concrete mappings are verified by the `tests/` suite.

**Notebook UX done** (milestone 3): `Canvas`
([src/bind_canvas.cpp](src/bind_canvas.cpp)) is bound — pgl's stream API
(`canvas << pgl::stroke("red") << shape`) does not map to Python, so each stream
operation is re-exposed as a method: fluent `scale`/`width`/`height`/`size`/
`margin`/`pointRadius`/`borders` and the numeric `strokeWidth` configuration;
fluent `stroke`/`fill`/`fillOpacity`/`strokeOpacity` style commands applied to the
*current* style (so only shapes drawn afterwards capture it); one `draw(shape)`
overload per bound shape; and `toSVG()`/`writeSVG(path)`. The fluent self-returns
use `nb::rv_policy::reference_internal`. `_repr_svg_` is added Python-side in
[pypgl/__init__.py](pypgl/__init__.py) — on the canvas it returns `toSVG()`, on
every shape it renders a one-shot `Canvas().draw(self)` — so shapes and canvases
display inline in Jupyter.

Still to do: broaden `intersection` to 2D∩2D / `Halfplane` (Convex/Polygon
results), packaging/stubs (milestone 4), and the experimental `Polygon`.
[pypgl.md](pypgl.md) remains the authoritative design contract —
update it in lockstep if a decision changes; [ROADMAP.md](ROADMAP.md) tracks
progress.

`Disk` ([src/bind_disk.cpp](src/bind_disk.cpp)) is bound as its own complete
class — its full predicate matrix against every shape (including itself) plus
exact `center`/`squaredRadius`/`bbox`/`pointInside`. `area` is irrational (π) so
it always returns Python `float`; `radius` returns an exact `Fraction` when the
disk was built from a center and radius (delegating the exact/inexact decision to
pgl's throwing `radius<ERational>()`) and a `float` otherwise (square root);
`squaredDistance` to a disk is likewise `float`. `diameter()` is reconstructed as
an exact `Segment` for center+radius disks (pgl ships only a floating-point one)
and raises for an irrational radius; `fbox()` is not bound (its double-coordinate
return type is not registered). Disk's
*column* is not added to the other shapes' matrices yet (e.g. `triangle.contains(disk)`),
partly because pgl still lacks `Triangle::contains(Disk)` and
`Convex::squaredDistance(Disk)`; symmetric relations are reachable from the Disk
side.

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
  Python class.

## Architecture

The only hand-written plumbing is two type casters in `src/casters.h`; everything
else is mechanical `.def(...)`:

1. `pgl::BigInt` ↔ Python `int` — via decimal string round-trip (lossless; uses
   pgl's existing `operator<<`/`operator>>`). A machine-int fast path is a later
   optimization, not a correctness requirement.
2. `pgl::ERational` ↔ Python `fractions.Fraction` — built from `numerator()` /
   `denominator()` (stored in lowest terms), each term flowing through the BigInt
   caster so arbitrarily large coordinates round-trip.

What falls out for free from pgl's typed API (built-in nanobind casters):
`std::optional<T>` → `T`/`None`; `std::variant<Point, Segment, …>` → the concrete
shape (so `intersection` returns `None` / `Point` / `Segment` with no sentinels);
`operator<<` → `__repr__`; `operator==`/`<`/`std::hash` → usable in `set`/`dict`.

**Layering:** the compiled `_pgl` extension stays minimal (just `.def`s). All
Pythonic sugar lives in `pgl/__init__.py`: vertex iteration, `point in shape` →
`shape.contains(point)` (point-in-shape only — keep shape-vs-shape as explicit
methods), pickling, and `_repr_svg_` for inline Jupyter rendering via `Canvas`.

**Translation units:** one `bind_*.cpp` per shape group (point, segment, lines,
polygons, canvas) so heavy template instantiation compiles in parallel and objects
stay small. A `PGL_BIND_PREDICATES(cls, OtherTypes...)` macro in `src/common.h`
keeps the seven uniform predicates (`contains`, `boundaryContains`,
`interiorContains`, `intersects`, `interiorsIntersect`, `separates`, `crosses`)
consistent across classes; each predicate is overloaded per accepted shape type.

`Disk` and `Polygon` are **experimental** — keep them gated until their C++
predicates settle, so the public API doesn't churn.

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
