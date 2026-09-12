#include "bind_arrangement.h"

using namespace pypgl;

// The power (Laguerre) diagrams of a set of disks (algorithm/voronoi.hpp): the
// Voronoi diagram with the squared distance to a site replaced by the power
// distance |x - center|^2 - radius^2. Bisectors are still lines and cells still
// convex, but a disk its neighbors swallow owns no cell and a center may lie
// outside its own cell.
//
// The two label types, Disk and std::vector<Disk>, are the two classes bound
// here from the shared template -- DiskArrangement and DiskListArrangement --
// in a translation unit of their own, so the two instantiations compile in
// parallel with the point diagrams of bind_voronoi.cpp.
//
// Exactness: a site is weighted by its *squared* radius, which pgl keeps exact
// for every disk, including one through three points whose radius is
// irrational. So every power diagram is exact, whichever way its disks were
// built -- unlike the Disk sums of the Minkowski family, which need the radius.

void bind_power_diagram(nb::module_ &m) {
    bindArrangement<Disk>(
        m, "DiskArrangement",
        "An arrangement whose edges and faces carry a Disk as their label: what "
        "powerDiagram(disks) returns.",
        "The label of a face: for a power diagram, the one disk that owns it.",
        "The label of an edge. A diagram leaves it default-constructed and gives it no "
        "meaning; setLabel() overwrites it.");
    bindArrangement<std::vector<Disk>>(
        m, "DiskListArrangement",
        "An arrangement whose edges and faces carry a list of disks as their label: what "
        "the order-k powerDiagram(disks, k) returns.",
        "The label of a face: for an order-k power diagram, the k disks nearest to "
        "every point of the face in the power distance, in their order in the input "
        "list.",
        "The label of an edge. A diagram leaves it empty and gives it no meaning; "
        "setLabel() overwrites it.");

    m.def("powerDiagram",
          [](const std::vector<Disk> &sites) { return pgl::powerDiagram(sites); },
          nb::arg("sites"),
          "The power (Laguerre) diagram of the disks in sites: the Voronoi diagram under "
          "the power distance |x - center|^2 - radius^2. A DiskArrangement whose every "
          "face is labeled with the disk that owns it. A disk its neighbors swallow owns "
          "no cell and labels no face, and a disk's center may lie outside its own cell; "
          "disks of equal radius give the Voronoi diagram of their centers. Disks sharing "
          "a center are allowed, the heavier one owning everything. Exact for every disk, "
          "since only squared radii are used. O(n^3 log n); raises ValueError for no "
          "sites.");
    m.def("powerDiagram",
          [](const std::vector<Disk> &sites, int k) { return pgl::powerDiagram(sites, k); },
          nb::arg("sites"), nb::arg("k"),
          "The order-k power diagram of the disks in sites, as a DiskListArrangement "
          "whose every face is labeled with the k disks nearest to it in the power "
          "distance, in their order in sites. Empty cells never appear. O(n^3 log n) for "
          "every k; raises ValueError unless 1 <= k <= len(sites).");
}
