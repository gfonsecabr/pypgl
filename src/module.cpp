#include "common.h"

void bind_point(nb::module_ &m);
void bind_segment(nb::module_ &m);
void bind_oriented_segment(nb::module_ &m);
void bind_lines(nb::module_ &m);
void bind_polygons(nb::module_ &m);
void bind_polygon(nb::module_ &m);
void bind_disk(nb::module_ &m);
void bind_triangulation(nb::module_ &m);
void bind_shapetree(nb::module_ &m);
void bind_canvas(nb::module_ &m);
void bind_transformation(nb::module_ &m);

NB_MODULE(_pgl, m) {
    m.doc() = "Compiled core of pypgl: Python bindings for the Pangolin (pgl) "
              "exact geometry library.";
    bind_point(m);
    bind_segment(m);
    bind_oriented_segment(m);
    bind_lines(m);
    bind_polygons(m);
    bind_polygon(m);
    bind_disk(m);
    bind_triangulation(m);
    bind_shapetree(m);
    bind_canvas(m);
    bind_transformation(m);
}
