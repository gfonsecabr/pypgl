"""pgl's assertions reach Python as exceptions.

pgl states its preconditions with PGL_ASSERT, which defaults to assert() and so
vanishes from a release build, leaving a violated precondition undefined. pypgl
defines PGL_ASSERT before including pgl (src/pgl_assert.h) so that every check
runs and a failure raises `PreconditionError`. These tests fail if that
override is lost -- a pgl header included ahead of it, say -- because the
calls below then stop raising.
"""

import pytest

import pypgl as pgl
from pypgl import PreconditionError, Rectangle


def test_it_is_an_exported_value_error():
    assert pgl.PreconditionError is PreconditionError
    assert issubclass(PreconditionError, ValueError)
    assert "PreconditionError" in pgl.__all__


@pytest.mark.parametrize("method", ["center", "centroid", "diameter"])
def test_a_violated_assertion_raises(method):
    # An empty rectangle has no center, centroid or diameter; pgl asserts
    # !empty() and no pypgl-side guard stands in front of it.
    with pytest.raises(PreconditionError, match=r"!empty\(\)"):
        getattr(Rectangle(), method)()


def test_the_message_names_the_header_relative_to_include():
    with pytest.raises(PreconditionError) as info:
        Rectangle().center()
    message = str(info.value)
    assert message.startswith("pgl precondition violated: !empty() (")
    # "implementation/measures.hpp:305", not a build machine's absolute path.
    location = message.rsplit("(", 1)[1].rstrip(")")
    header, line = location.rsplit(":", 1)
    assert header.endswith(".hpp") and not header.startswith(("/", "\\"))
    assert "include" not in header
    assert line.isdigit()


def test_the_shape_survives_and_a_valid_call_still_answers():
    r = Rectangle()
    with pytest.raises(PreconditionError):
        r.center()
    assert r.empty()
    assert Rectangle(pgl.Point(0, 0), pgl.Point(2, 4)).center() == pgl.Point(1, 2)
