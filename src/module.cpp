#include "common.h"

void bind_point(nb::module_ &m);
void bind_segment(nb::module_ &m);
void bind_oriented_segment(nb::module_ &m);
void bind_lines(nb::module_ &m);
void bind_polygons(nb::module_ &m);
void bind_polygon(nb::module_ &m);
void bind_region(nb::module_ &m);
void bind_polygonset(nb::module_ &m);
void bind_chains(nb::module_ &m);
void bind_halfplane_intersection(nb::module_ &m);
void bind_disk(nb::module_ &m);
void bind_triangulation(nb::module_ &m);
void bind_shapetree(nb::module_ &m);
void bind_canvas(nb::module_ &m);
void bind_transformation(nb::module_ &m);
void bind_algorithms(nb::module_ &m);
void bind_graph(nb::module_ &m);
void bind_intervaltree(nb::module_ &m);
void bind_arrangement(nb::module_ &m);

NB_MODULE(_pgl, m) {
    m.doc() = "Compiled core of pypgl: Python bindings for the Pangolin (pgl) "
              "exact geometry library.";
    bind_point(m);
    bind_segment(m);
    bind_oriented_segment(m);
    bind_lines(m);
    bind_polygons(m);
    bind_polygon(m);
    bind_region(m);
    bind_polygonset(m);
    bind_chains(m);
    bind_halfplane_intersection(m);
    bind_disk(m);
    bind_triangulation(m);
    bind_shapetree(m);
    bind_canvas(m);
    bind_transformation(m);
    // Graph first: the visibility methods of the shapes above and of a
    // triangulation return one, and the arrangement's own graph binding
    // (over vertex handles) reuses the same template.
    bind_graph(m);
    bind_intervaltree(m);
    bind_arrangement(m);
    bind_algorithms(m);
}
