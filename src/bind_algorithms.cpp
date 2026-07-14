#include "common.h"

using namespace pypgl;

namespace {

void replace_points(nb::list points, const std::vector<Point> &sorted) {
    for (std::size_t i = 0; i < sorted.size(); ++i)
        points[i] = nb::cast(sorted[i]);
}

}  // namespace

void bind_algorithms(nb::module_ &m) {
    m.def("findIntersections",
          [](const std::vector<Segment> &segments) { return pgl::findIntersections(segments); },
          nb::arg("segments"),
          "Return all intersecting pairs of segments using Bentley-Ottmann.");
    m.def("findCrossings",
          [](const std::vector<Segment> &segments) { return pgl::findCrossings(segments); },
          nb::arg("segments"),
          "Return all properly crossing pairs of segments using Bentley-Ottmann.");
    m.def("bruteForceIntersections",
          [](const std::vector<Segment> &segments) { return pgl::bruteForceIntersections(segments); },
          nb::arg("segments"),
          "Return all intersecting pairs of segments by exhaustive search.");
    m.def("bruteForceCrossings",
          [](const std::vector<Segment> &segments) { return pgl::bruteForceCrossings(segments); },
          nb::arg("segments"),
          "Return all properly crossing pairs of segments by exhaustive search.");
    m.def("detectIntersections",
          [](const std::vector<Segment> &segments) { return pgl::detectIntersections(segments); },
          nb::arg("segments"),
          "Whether any two segments intersect, using Bentley-Ottmann.");
    m.def("detectCrossings",
          [](const std::vector<Segment> &segments) { return pgl::detectCrossings(segments); },
          nb::arg("segments"),
          "Whether any two segments properly cross, using Bentley-Ottmann.");

    m.def("convexHull",
          [](const std::vector<Point> &points) { return pgl::convexHull(points); },
          nb::arg("points"), "Return the extreme vertices of the convex hull in counterclockwise order.");
    m.def("convexHullExtended",
          [](const std::vector<Point> &points) { return pgl::grahamScanExtended(points); },
          nb::arg("points"),
          "Return the convex hull, retaining input points on its edge interiors.");

    m.def("sortAround",
          [](nb::list points, const Point &center) {
              auto sorted = nb::cast<std::vector<Point>>(points);
              pgl::sortAround(sorted, center);
              replace_points(points, sorted);
          },
          nb::arg("points"), nb::arg("p"),
          "Reorder a list of points counterclockwise around p.");
    m.def("hilbertSort",
          [](nb::list points) {
              auto sorted = nb::cast<std::vector<Point>>(points);
              pgl::hilbertSort(sorted);
              replace_points(points, sorted);
          },
          nb::arg("points"), "Reorder a list of points along a Hilbert curve.");

    m.def("polyominoes",
          [](std::size_t size) { return pgl::polyominoes<Num>(size); },
          nb::arg("size"), "Return the hole-free free polyominoes of one cell count.");
    m.def("polyominoes",
          [](std::size_t n1, std::size_t n2) {
              return pgl::polyominoes<Num>(n1, n2);
          },
          nb::arg("n1"), nb::arg("n2"),
          "Return the hole-free free polyominoes for every cell count in an inclusive range.");
    m.def("polyominoesUpTo",
          [](std::size_t size) { return pgl::polyominoesUpTo<Num>(size); },
          nb::arg("size"), "Return the hole-free free polyominoes up to a cell count.");
}
