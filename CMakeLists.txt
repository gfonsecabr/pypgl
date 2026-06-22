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
    FetchContent_Declare(pgl
      GIT_REPOSITORY https://github.com/gfonsecabr/pgl
      GIT_TAG        main)
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
  src/bind_polygons.cpp)

target_include_directories(_pgl PRIVATE "${PGL_INCLUDE_DIR}" src)

install(TARGETS _pgl LIBRARY DESTINATION pypgl)
