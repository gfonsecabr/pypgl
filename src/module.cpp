#include "common.h"

void bind_point(nb::module_ &m);
void bind_segment(nb::module_ &m);

NB_MODULE(_pgl, m) {
    m.doc() = "Compiled core of pypgl: Python bindings for the Pangolin (pgl) "
              "exact geometry library.";
    bind_point(m);
    bind_segment(m);
}
