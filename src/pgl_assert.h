#pragma once

// Every pgl assertion, turned into a Python exception.
//
// pgl states its preconditions (and a few internal invariants) with
// PGL_ASSERT(cond), which defaults to assert(cond) and so disappears under
// NDEBUG -- the release build pypgl ships. A violated precondition was then
// undefined behavior rather than an error: an empty Convex read past the end of
// its vertex list, a zero divisor built a Rational that crashed the process
// later, and so on, one segfault at a time (milestones 11, 28, 29 and 30 each
// guarded a few by hand). pgl lets the includer define PGL_ASSERT first, so
// pypgl defines it to *throw*: the check always runs, and a failure reaches
// Python as pypgl.PreconditionError, a ValueError, instead of taking the
// interpreter down.
//
// This header must be included before any pgl header, in every translation
// unit. casters.h includes it first and every pgl include goes through
// casters.h (common.h includes it ahead of pgl.hpp), which is what makes that
// hold; the #error below catches a pgl header that slipped in earlier.
//
// Upstream commented out every assert costing more than O(1) (pgl 3000446), so
// running the rest in a release build is cheap.
//
// An assert inside a noexcept function still cannot throw out of it: that ends
// in std::terminate, an abort with a message, which is no worse than before.

#ifdef PGL_ASSERT
#error "PGL_ASSERT is already defined: include pgl_assert.h before any pgl header"
#endif

#include <stdexcept>
#include <string>
#include <string_view>

namespace pypgl {

// Registered as pypgl.PreconditionError (a ValueError) in module.cpp.
struct PreconditionError : std::logic_error {
    using std::logic_error::logic_error;
};

[[noreturn]] inline void assertionFailed(const char *condition, const char *file, int line) {
    // Name the header relative to pgl's include/ directory, which is what a
    // user can look up, rather than a build machine's absolute path.
    std::string_view path(file);
    for (std::string_view marker : {"/include/", "\\include\\"}) {
        if (auto at = path.rfind(marker); at != std::string_view::npos) {
            path.remove_prefix(at + marker.size());
            break;
        }
    }
    throw PreconditionError("pgl precondition violated: " + std::string(condition) + " (" +
                            std::string(path) + ":" + std::to_string(line) + ")");
}

}  // namespace pypgl

// A conditional expression rather than an if, so it stays an expression like
// assert() is (pgl uses it in comma and constexpr contexts). The call in the
// false branch is not constexpr, which is fine in a constexpr function as long
// as a constant evaluation never takes that branch -- exactly assert()'s own
// contract.
#define PGL_ASSERT(cond)                                                                \
    (static_cast<bool>(cond) ? void(0)                                                  \
                             : ::pypgl::assertionFailed(#cond, __FILE__, __LINE__))
