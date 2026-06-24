"""Milestone 4: the packaged type information.

PEP 561 requires a ``py.typed`` marker and (for a compiled module) a ``.pyi``
stub shipped next to the extension. These are generated at build time by
``nanobind_add_stub`` from the bare ``_pgl`` module, with the Python-layer sugar
from ``pypgl/__init__.py`` re-added via ``src/stubgen_patterns.txt``. This test
checks the artifacts are installed, syntactically valid, and that the re-added
sugar landed on the shapes (and not on ``Canvas``)."""

import ast
from pathlib import Path

import pytest

import pypgl

# The stub must sit next to the compiled extension it describes; the py.typed
# marker next to the package's __init__. In an editable install these dirs differ
# (the .so is staged in site-packages, __init__.py loads from the source tree);
# in a wheel they coincide.
_EXT_DIR = Path(pypgl._pgl.__file__).parent
_PKG_DIR = Path(pypgl.__file__).parent
_STUB = _EXT_DIR / "_pgl.pyi"


def test_py_typed_marker_shipped():
    assert (_PKG_DIR / "py.typed").is_file()


def test_stub_shipped_next_to_extension():
    assert _STUB.is_file(), f"missing generated stub: {_STUB}"


def test_stub_is_valid_python():
    ast.parse(_STUB.read_text())


def _classes(tree):
    return {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}


def test_stub_declares_every_public_class():
    classes = _classes(ast.parse(_STUB.read_text()))
    for name in pypgl.__all__:
        assert name in classes, f"{name} missing from stub"


def test_stub_has_no_leaked_runtime_patches():
    # The bare-module generation must not pull in the runtime-patched lambdas as
    # an invalid `from pypgl import <lambda>` (the quirk the pattern file avoids).
    text = _STUB.read_text()
    assert "<lambda>" not in text
    assert "from pypgl" not in text


@pytest.mark.parametrize("shape", [
    "Point", "Segment", "OrientedSegment", "Line", "OrientedLine", "Ray",
    "Halfplane", "Triangle", "Rectangle", "Convex", "Disk",
])
def test_sugar_methods_present_on_shapes(shape):
    cls = _classes(ast.parse(_STUB.read_text()))[shape]
    methods = {n.name for n in cls.body if isinstance(n, ast.FunctionDef)}
    assert {"__len__", "__getitem__", "__iter__", "__contains__"} <= methods


def test_canvas_has_no_point_sugar():
    cls = _classes(ast.parse(_STUB.read_text()))["Canvas"]
    methods = {n.name for n in cls.body if isinstance(n, ast.FunctionDef)}
    assert "__getitem__" not in methods
    assert "__contains__" not in methods


def test_point_indexing_returns_fraction():
    # Point indexes over its two rational coordinates, so __getitem__ -> Fraction;
    # the other shapes index over their defining Points.
    cls = _classes(ast.parse(_STUB.read_text()))["Point"]
    getitem = next(n for n in cls.body
                   if isinstance(n, ast.FunctionDef) and n.name == "__getitem__")
    assert "fractions.Fraction" in ast.unparse(getitem.returns)
