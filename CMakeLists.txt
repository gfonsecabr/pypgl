cmake_minimum_required(VERSION 3.15...3.30)
project(pypgl LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

find_package(Python 3.9 COMPONENTS Interpreter Development.Module REQUIRED)

# Locate the installed nanobind (a build dependency) and load its CMake config.
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE nanobind_ROOT)
find_package(nanobind CONFIG REQUIRED)

# Locate pgl's header-only include/ directory. Resolution order:
#   1. an explicit -DPGL_INCLUDE_DIR=... (co-development against a local checkout)
#   2. an in-tree .pgl-ref/ checkout (offline default)
#   3. CMake FetchContent from GitHub (pinned to a tag once pgl publishes them)
set(PGL_INCLUDE_DIR "" CACHE PATH "Path to pgl's include/ directory")
if(NOT PGL_INCLUDE_DIR)
  if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/.pgl-ref/include/pgl.hpp")
    set(PGL_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/.pgl-ref/include")
  else()
    include(FetchContent)
    # Pinned to the exact commit the in-tree .pgl-ref/ dev checkout is at, so CI
    # wheel builds (which don't ship the gitignored .pgl-ref/) are reproducible
    # and match local development. Bump in lockstep with .pgl-ref. Switch to a
    # release tag once pgl publishes them.
    FetchContent_Declare(pgl
      GIT_REPOSITORY https://github.com/gfonsecabr/pgl
      GIT_TAG        5dabc73dcf0a28a9024c8b95429e3acdb794306c)
    FetchContent_MakeAvailable(pgl)
    set(PGL_INCLUDE_DIR "${pgl_SOURCE_DIR}/include")
  endif()
endif()
message(STATUS "pypgl: using pgl headers from ${PGL_INCLUDE_DIR}")

nanobind_add_module(_pgl
  NB_STATIC
  src/module.cpp
  src/bind_point.cpp
  src/bind_segment.cpp
  src/bind_lines.cpp
  src/bind_polygons.cpp
  src/bind_polygon.cpp
  src/bind_chains.cpp
  src/bind_disk.cpp
  src/bind_triangulation.cpp
  src/bind_shapetree.cpp
  src/bind_canvas.cpp
  src/bind_transformation.cpp
  src/bind_algorithms.cpp)

target_include_directories(_pgl PRIVATE "${PGL_INCLUDE_DIR}" src)

# clang-cl (the Windows toolset — see pyproject's [tool.cibuildwheel.windows])
# emits calls to compiler-rt's 128-bit-integer builtins (__udivti3, __modti3,
# __divti3, __floattidf, __fixdfti) for the __int128 path pgl takes, but lld-link
# does not auto-link the builtins archive the way GCC/Clang do on Unix. Link it
# explicitly, located relative to the compiler.
if(MSVC AND CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  # clang-cl uses the MSVC standard library, whose `inplace_merge` needs this
  # explicit opt-in when pgl's exact Point exceeds max_align_t alignment.
  target_compile_definitions(_pgl PRIVATE _ENABLE_EXTENDED_ALIGNED_STORAGE)

  get_filename_component(_clang_bin_dir "${CMAKE_CXX_COMPILER}" DIRECTORY)
  file(GLOB _clang_rt_builtins
    "${_clang_bin_dir}/../lib/clang/*/lib/windows/clang_rt.builtins-x86_64.lib")
  if(_clang_rt_builtins)
    list(GET _clang_rt_builtins -1 _clang_rt_builtins)  # highest clang version
    target_link_libraries(_pgl PRIVATE "${_clang_rt_builtins}")
    message(STATUS "pypgl: linking compiler-rt builtins ${_clang_rt_builtins}")
  else()
    message(WARNING "pypgl: clang_rt.builtins-x86_64.lib not found near ${_clang_bin_dir}")
  endif()
endif()

install(TARGETS _pgl LIBRARY DESTINATION pypgl)

# Generate a type stub (_pgl.pyi) for the compiled module and ship it next to
# py.typed (PEP 561) so type checkers and IDEs see the full exact-geometry API.
# The stub is built from the bare `_pgl` module (importing it standalone, before
# pypgl/__init__.py runs); src/stubgen_patterns.txt re-adds the Python-layer
# sugar that __init__.py applies at import time (len/indexing/iteration over a
# shape's defining points and `point in shape`).
nanobind_add_stub(_pgl_stub
  MODULE _pgl
  OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/_pgl.pyi"
  PYTHON_PATH "$<TARGET_FILE_DIR:_pgl>"
  PATTERN_FILE "${CMAKE_CURRENT_SOURCE_DIR}/src/stubgen_patterns.txt"
  DEPENDS _pgl)

install(FILES "${CMAKE_CURRENT_BINARY_DIR}/_pgl.pyi" DESTINATION pypgl)
