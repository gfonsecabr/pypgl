#include "common.h"

using namespace pypgl;

// BitMatrix: one bit per cell of a fixed rectangular window of the integer grid
// (algorithm/bitmatrix.hpp), plus the GridAdjacency enum its connectivity and
// morphology take, and the innerRaster/outerRaster free functions.
//
// This is the cheap representation for the rectilinear work the exact polygonal
// one makes expensive -- set algebra, Minkowski operations, connectivity,
// morphology, hv-convexity -- at the price of only representing what the grid
// can. Cell (x, y) is the closed unit square [x, x+1] x [y, y+1], named by its
// lower-left corner.
//
// ---------------------------------------------------------------------------
// The one class not held over pypgl's own Point
//
// pgl constrains BitMatrix to `std::signed_integral` coordinates, so
// BitMatrix<Point> (ERational coordinates) is ill-formed by construction -- see
// the ::pypgl::Cell / ::pypgl::BitMatrix aliases in common.h. That stays an
// implementation detail: no second point type is bound, and the boundary is
// crossed in two directions only.
//
//   * Going in, a cell is named either by a pair of plain Python ints (the fast
//     spelling, and the one a loop wants) or by an ordinary pypgl Point, which
//     toCell() checks with pgl's own gridCoordinate -- a fractional coordinate
//     raises rather than being rounded, since rounding it would move the cell.
//   * Coming out, every shape a matrix produces (bbox, window, cells,
//     rectangles, lattice, convexHull, asPolygonWithHoles, asPolygonSet) is
//     widened into the bound ERational class by pgl's cross-point-type
//     converting constructors, and the measures (area, perimeter, centroid,
//     pointInside) request ERational explicitly, so they stay exact.
//
// ---------------------------------------------------------------------------
// Two readings of a cell, and which operation takes which
//
// Unprefixed, a cell is the unit square it covers: that is what the predicates,
// the measures, the symmetries, minkowskiSum and minkowskiErosion answer for,
// and they all commute with asPolygonSet. Prefixed with `lattice`, a cell is the
// single point at its lower-left corner, which is the convention that makes a
// structuring element behave -- a one-cell matrix is the identity of
// latticeMinkowskiSum, and latticeMinkowskiErosion is its exact dual. The two
// differ by a cell: reflected() maps cell c to -c - (1,1) where
// latticeReflected() maps it to -c.
//
// ---------------------------------------------------------------------------
// Binding decisions
//
//   * Mutable (set/reset/flip/clear/rotate90/fillRows/&=/+=/...), hence bound
//     unhashable, following Convex/Polygon/PolygonWithHoles/PolygonSet -- even
//     though pgl specializes std::hash for it.
//   * Not a Shape alternative, so it is neither a ShapeTree/IntervalTree
//     element nor a row of PGL_BIND_ALL_PREDICATES: pgl gives its five shape
//     predicates against another BitMatrix only. It is drawable (Canvas streams
//     it as its polygon set) and gets _repr_svg_ like every other shape.
//   * Not a fixed-extent shape either, so it is shielded from the generic
//     point-sugar in pypgl/__init__.py and stubgen_patterns.txt, and binds its
//     own container protocol here: len() is the number of set cells, iteration
//     yields them as Points, and `point in matrix` asks whether *that cell* is
//     set (not whether the point lies in the covered region -- pgl has no such
//     predicate here, and the cell question is the one get() answers).
//   * No __repr__ from bind_value_semantics: pgl gives BitMatrix no
//     operator<<, only the Canvas one, so repr is written by hand -- as is the
//     comparison set, over pgl's own == and <=>.
//   * latticeView()/cellsView() are not bound: they are lazy C++ views, and
//     lattice()/cells() already materialize the same sequences, which is what a
//     Python caller gets either way (the same call as Polyline's edgesView in
//     bind_chains.cpp). fbox() is not bound either, its double-coordinate
//     return type not being registered -- as on every other shape.

namespace {

// Cells of a window, tested one at a time against an exact shape.
//
// pgl's own innerRaster/outerRaster cannot serve here: they build each cell over
// the *result grid's* point type and hand it to shape.contains/intersects, and
// Shape<Point>'s predicates only accept shapes over their own point type, so an
// int64 cell against an ERational shape does not compile. The loop is the same
// one, with the cell widened to an exact Rectangle before the predicate -- which
// costs nothing, the corners being whole numbers.
BitMatrix rasterize(const AnyShape &shape, const pgl::Rectangle<Cell> &window, bool inner) {
    BitMatrix result(window);
    for (int j = 0; j < result.height(); ++j) {
        for (int i = 0; i < result.width(); ++i) {
            const std::int64_t x = result.origin().x() + i;
            const std::int64_t y = result.origin().y() + j;
            const Rectangle cell(Point(x, y), Point(x + 1, y + 1), true);
            if (inner ? shape.contains(cell) : shape.intersects(cell)) result.set(x, y);
        }
    }
    return result;
}

// Rounding an exact coordinate outward. pgl has no floor/ceil for a Rational,
// and the terms are always in lowest form with a positive denominator, so the
// truncating BigInt division is corrected by one whenever it left a remainder on
// the side being rounded away from.
std::int64_t floorTo(const Num &value) {
    const pgl::BigInt &n = value.numerator(), &d = value.denominator();
    pgl::BigInt quotient = n / d;
    if (quotient * d != n && n < pgl::BigInt(0)) quotient -= pgl::BigInt(1);
    return static_cast<std::int64_t>(quotient);
}

std::int64_t ceilTo(const Num &value) {
    const pgl::BigInt &n = value.numerator(), &d = value.denominator();
    pgl::BigInt quotient = n / d;
    if (quotient * d != n && n > pgl::BigInt(0)) quotient += pgl::BigInt(1);
    return static_cast<std::int64_t>(quotient);
}

// The window a rasterizer uses when none is given: the smallest cell window
// covering the shape's bounding box. pgl's no-window overloads require an
// integer shape, which an ERational one is not, so the box is rounded *outward*
// here -- outward rather than nearest because that is what keeps outerRaster's
// result covering the shape, which is the property the pair is for. A shape with
// no bbox (Line, OrientedLine, Ray, Halfplane, an unbounded
// HalfplaneIntersection) has no such window and raises, exactly as it does when
// stored in a ShapeTree; those shapes still rasterize fine over an explicit one.
pgl::Rectangle<Cell> boundingWindow(const AnyShape &shape) {
    const Rectangle box(shape.bbox());
    if (box.empty()) return pgl::Rectangle<Cell>();
    return pgl::Rectangle<Cell>(Cell(floorTo(box.min().x()), floorTo(box.min().y())),
                                Cell(ceilTo(box.max().x()), ceilTo(box.max().y())), true);
}

// Both spellings of a cell-addressing method: (x, y) as plain ints, and a Point.
template <class Class, class Fn>
void bind_cell_pair(Class &cls, const char *name, Fn fn, const char *doc) {
    cls.def(name, [fn](BitMatrix &self, std::int64_t x, std::int64_t y) { return fn(self, x, y); },
            nb::arg("x"), nb::arg("y"), doc);
    cls.def(name,
            [fn](BitMatrix &self, const Point &cell) {
                const Cell c = toCell(cell);
                return fn(self, c.x(), c.y());
            },
            nb::arg("cell"), doc);
}

}  // namespace

void bind_bitmatrix(nb::module_ &m) {
    nb::enum_<pgl::GridAdjacency>(m, "GridAdjacency",
                                  "Which grid cells count as neighbors: edge is 4-adjacency "
                                  "(cells sharing a side), vertex is 8-adjacency (a side or "
                                  "only a corner).")
        .value("edge", pgl::GridAdjacency::edge, "4-adjacency: cells sharing a side.")
        .value("vertex", pgl::GridAdjacency::vertex,
               "8-adjacency: cells sharing a side or only a corner.");

    nb::class_<BitMatrix> cls(m, "BitMatrix");

    // ---- construction ------------------------------------------------------
    cls.def(nb::init<>(), "Create a matrix whose window is empty, so no cell can be set.");
    cls.def("__init__",
            [](BitMatrix *self, const Point &origin, int width, int height) {
                new (self) BitMatrix(toCell(origin), width, height);
            },
            nb::arg("origin"), nb::arg("width"), nb::arg("height"),
            "A matrix covering width by height cells from origin, all clear. The window is "
            "fixed here and never grows: writing outside it is a no-op and reading outside "
            "it is False. A non-positive extent leaves the window empty.");
    cls.def("__init__",
            [](BitMatrix *self, std::int64_t x, std::int64_t y, int width, int height) {
                new (self) BitMatrix(Cell(x, y), width, height);
            },
            nb::arg("x"), nb::arg("y"), nb::arg("width"), nb::arg("height"),
            "A matrix covering width by height cells from (x, y), all clear.");
    cls.def("__init__",
            [](BitMatrix *self, const Rectangle &box) { new (self) BitMatrix(toGridWindow(box)); },
            nb::arg("window"),
            "A matrix whose window is the rectangle its cells cover, the inverse of window(). "
            "Raises if a corner is not a whole number the grid can hold.");
    cls.def("__init__", [](BitMatrix *self, const Polygon &p) { new (self) BitMatrix(p); },
            nb::arg("polygon"),
            "The rectilinear polygon rasterized over its own bounding box; the same operation "
            "as Polygon.asBitMatrix().");
    cls.def("__init__", [](BitMatrix *self, const PolygonWithHoles &r) { new (self) BitMatrix(r); },
            nb::arg("region"),
            "The rectilinear region rasterized over its own bounding box, holes left unset; "
            "the same operation as PolygonWithHoles.asBitMatrix().");
    cls.def("__init__", [](BitMatrix *self, const PolygonSet &s) { new (self) BitMatrix(s); },
            nb::arg("set"),
            "The rectilinear set rasterized over the bounding box of all its components, the "
            "holes and the gaps between components left unset; the same operation as "
            "PolygonSet.asBitMatrix().");

    // ---- the window --------------------------------------------------------
    cls.def("origin", [](const BitMatrix &b) { return Point(b.origin()); },
            "Lower-left cell of the window.");
    cls.def("width", &BitMatrix::width, "Number of cells across the window.");
    cls.def("height", &BitMatrix::height, "Number of cells up the window.");
    cls.def("window", [](const BitMatrix &b) { return Rectangle(b.window()); },
            "The rectangle the window's cells cover.");
    cls.def("emptyWindow", &BitMatrix::emptyWindow, "Whether the window holds no cell at all.");
    bind_cell_pair(cls, "inWindow",
                   [](const BitMatrix &b, std::int64_t x, std::int64_t y) { return b.inWindow(x, y); },
                   "Whether the cell lies in the window.");
    cls.def("sameWindow", &BitMatrix::sameWindow, nb::arg("other"),
            "Whether two matrices cover the same window.");
    cls.def("resized", [](const BitMatrix &b, const Rectangle &box) { return b.resized(toGridWindow(box)); },
            nb::arg("window"),
            "The same cells over another window, dropping those the new one does not hold.");
    cls.def("trimmed", &BitMatrix::trimmed,
            "The same cells over the smallest window holding them. This is the canonical form "
            "to compare or hash by when only the region matters: a matrix is unequal to its "
            "trimmed form whenever trimming moves anything, while samePointSet always holds.");

    // ---- one cell ----------------------------------------------------------
    bind_cell_pair(cls, "get", [](const BitMatrix &b, std::int64_t x, std::int64_t y) { return b.get(x, y); },
                   "Whether the cell is set. A cell outside the window is False.");
    bind_cell_pair(cls, "set", [](BitMatrix &b, std::int64_t x, std::int64_t y) { b.set(x, y); },
                   "Sets the cell. Outside the window this is a no-op.");
    bind_cell_pair(cls, "reset", [](BitMatrix &b, std::int64_t x, std::int64_t y) { b.reset(x, y); },
                   "Clears the cell. Outside the window this is a no-op.");
    bind_cell_pair(cls, "flip", [](BitMatrix &b, std::int64_t x, std::int64_t y) { b.flip(x, y); },
                   "Inverts the cell. Outside the window this is a no-op.");
    cls.def("set",
            [](BitMatrix &b, std::int64_t x, std::int64_t y, bool value) { b.set(x, y, value); },
            nb::arg("x"), nb::arg("y"), nb::arg("value"), "Sets or clears the cell.");
    cls.def("set",
            [](BitMatrix &b, const Point &cell, bool value) {
                const Cell c = toCell(cell);
                b.set(c.x(), c.y(), value);
            },
            nb::arg("cell"), nb::arg("value"), "Sets or clears the cell.");
    cls.def("setAll", &BitMatrix::setAll, "Sets every cell of the window.");
    cls.def("clear", &BitMatrix::clear, "Clears every cell.");

    // ---- what is set -------------------------------------------------------
    cls.def("empty", &BitMatrix::empty, "Whether no cell is set.");
    cls.def("count", &BitMatrix::count, "Number of set cells.");
    cls.def("__len__", &BitMatrix::count);
    // Iteration materializes: the C++ iterator yields a Cell, which is not a
    // bound type, so each one is widened to a Point first. That is what
    // lattice() already builds, and iterating it is the whole of __iter__.
    cls.def("__iter__",
            [](const BitMatrix &b) {
                std::vector<Point> cells;
                cells.reserve(b.count());
                for (const Cell &c : b) cells.emplace_back(c);
                return nb::iter(nb::cast(std::move(cells)));
            },
            nb::sig("def __iter__(self) -> collections.abc.Iterator[Point]"),
            "The set cells as lattice points, in row-major order.");
    cls.def("__contains__",
            [](const BitMatrix &b, const Point &cell) {
                const Cell c = toCell(cell);
                return b.get(c.x(), c.y());
            },
            nb::arg("cell"),
            "Whether that cell is set. This asks get(), not whether the point lies in the "
            "covered region.");
    cls.def("lattice",
            [](const BitMatrix &b) {
                std::vector<Point> result;
                result.reserve(b.count());
                for (const Cell &c : b) result.emplace_back(c);
                return result;
            },
            "The set cells as lattice points, in row-major order.");
    cls.def("cells",
            [](const BitMatrix &b) {
                std::vector<Rectangle> result;
                result.reserve(b.count());
                for (const auto &square : b.cells()) result.emplace_back(square);
                return result;
            },
            "The set cells as the unit squares they cover, in row-major order.");
    cls.def("rectangles",
            [](const BitMatrix &b) {
                std::vector<Rectangle> result;
                for (const auto &run : b.rectangles()) result.emplace_back(run);
                return result;
            },
            "The set cells merged into as few disjoint covering rectangles as a row-major "
            "pass can, one per run of a row. This is how to draw the cells as separate "
            "elements: canvas.draw(matrix.rectangles()).");

    // ---- measures ----------------------------------------------------------
    cls.def("area", [](const BitMatrix &b) { return b.area<Num>(); },
            "Area of the covered region: the number of set cells, each of unit area.");
    cls.def("perimeter", [](const BitMatrix &b) { return b.perimeter<Num>(); },
            "Length of the covered region's boundary, counting the edges of a cell on the "
            "window border.");
    cls.def("centroid", [](const BitMatrix &b) { return Point(b.centroid<Num>()); },
            "The average of the set cells' centers. Raises if no cell is set.");
    cls.def("pointInside", [](const BitMatrix &b) { return Point(b.pointInside<Num>()); },
            "The center of the first set cell. Raises if no cell is set.");
    cls.def("bbox", [](const BitMatrix &b) { return Rectangle(b.bbox()); },
            "The rectangle the set cells cover; the empty rectangle when none is set.");

    // ---- conversion --------------------------------------------------------
    cls.def("convexHull", [](const BitMatrix &b) { return Convex(b.convexHull()); },
            "The convex hull of the covered region, as a Convex.");
    cls.def("asPolygonWithHoles", [](const BitMatrix &b) { return PolygonWithHoles(b.asPolygonWithHoles()); },
            "The covered region as a single PolygonWithHoles. Raises unless the set cells form "
            "one edge-connected group, which a rasterized region and its Minkowski sums are.");
    cls.def("asPolygonSet", [](const BitMatrix &b) { return PolygonSet(b.asPolygonSet()); },
            "The covered region as a PolygonSet, one component per edge-connected group of "
            "cells, so it has no precondition and keeps two components touching only at a "
            "corner apart. Vertices in the middle of a straight stretch are dropped, so a "
            "filled box comes back as four corners however many cells it holds.");

    // ---- set algebra -------------------------------------------------------
    cls.def("__and__", [](const BitMatrix &a, const BitMatrix &b) { return a & b; }, nb::is_operator());
    cls.def("__or__", [](const BitMatrix &a, const BitMatrix &b) { return a | b; }, nb::is_operator());
    cls.def("__xor__", [](const BitMatrix &a, const BitMatrix &b) { return a ^ b; }, nb::is_operator());
    cls.def("__invert__", [](const BitMatrix &a) { return ~a; }, nb::is_operator());
    cls.def("__iand__", [](BitMatrix &a, const BitMatrix &b) -> BitMatrix & { return a &= b; },
            nb::is_operator());
    cls.def("__ior__", [](BitMatrix &a, const BitMatrix &b) -> BitMatrix & { return a |= b; },
            nb::is_operator());
    cls.def("__ixor__", [](BitMatrix &a, const BitMatrix &b) -> BitMatrix & { return a ^= b; },
            nb::is_operator());
    cls.def("difference", &BitMatrix::difference, nb::arg("other"),
            "The cells of this matrix that are not cells of other, over this window.");
    cls.def("symmetricDifference", &BitMatrix::symmetricDifference, nb::arg("other"),
            "The cells set in exactly one of the two, over the hull of the two windows; "
            "spelled out from ^.");
    cls.def("andCount", &BitMatrix::andCount, nb::arg("other"),
            "How many cells the two share, without building the intersection.");
    cls.def("orCount", &BitMatrix::orCount, nb::arg("other"),
            "How many cells the union holds, without building it.");
    cls.def("xorCount", &BitMatrix::xorCount, nb::arg("other"),
            "How many cells the symmetric difference holds, without building it.");

    // ---- comparison --------------------------------------------------------
    //
    // The window is part of a matrix's value: == and the ordering compare it
    // along with the cells, as a shape's do for its stored representation.
    // samePointSet is the geometric question, and trimmed() the canonical form
    // to compare by when only the region matters. Mutable, hence unhashable.
    cls.def("__eq__", [](const BitMatrix &a, const BitMatrix &b) { return a == b; }, nb::is_operator());
    cls.def("__ne__", [](const BitMatrix &a, const BitMatrix &b) { return !(a == b); }, nb::is_operator());
    cls.def("__lt__", [](const BitMatrix &a, const BitMatrix &b) { return a < b; }, nb::is_operator());
    cls.def("__le__", [](const BitMatrix &a, const BitMatrix &b) { return !(b < a); }, nb::is_operator());
    cls.def("__gt__", [](const BitMatrix &a, const BitMatrix &b) { return b < a; }, nb::is_operator());
    cls.def("__ge__", [](const BitMatrix &a, const BitMatrix &b) { return !(a < b); }, nb::is_operator());
    cls.attr("__hash__") = nb::none();
    cls.def("samePointSet", &BitMatrix::samePointSet, nb::arg("other"),
            "Whether the two cover the same region, whatever windows they carry.");
    cls.def("__repr__", [](const BitMatrix &b) {
        std::ostringstream out;
        out << "BitMatrix[" << b.width() << "x" << b.height() << " from (" << b.origin().x() << ","
            << b.origin().y() << "), " << b.count() << " cells]";
        return out.str();
    });
    cls.def("__str__", [](const BitMatrix &b) {
        std::ostringstream out;
        out << "BitMatrix[" << b.width() << "x" << b.height() << " from (" << b.origin().x() << ","
            << b.origin().y() << "), " << b.count() << " cells]";
        return out.str();
    });

    // ---- predicates (against another matrix) -------------------------------
    //
    // These read the cells as the closed squares they are, which is why
    // intersects() is true as soon as two cells come within Chebyshev distance
    // one: cells sharing only a corner already share a point.
    cls.def("contains", &BitMatrix::contains, nb::arg("other"),
            "Whether every cell of other is a cell of this matrix.");
    cls.def("interiorContains", &BitMatrix::interiorContains, nb::arg("other"),
            "Whether every cell of other is a cell of this matrix and none of them touches "
            "the boundary, corners included.");
    cls.def("boundaryContains", &BitMatrix::boundaryContains, nb::arg("other"),
            "Whether other lies in the boundary, which holds only for an empty other: a "
            "boundary is a curve and a nonempty matrix covers area.");
    cls.def("intersects", &BitMatrix::intersects, nb::arg("other"),
            "Whether the two regions share a point, so as soon as a cell of one comes within "
            "Chebyshev distance one of a cell of the other.");
    cls.def("interiorsIntersect", &BitMatrix::interiorsIntersect, nb::arg("other"),
            "Whether the two share a cell, which is the stricter question.");

    // ---- translation -------------------------------------------------------
    cls.def("translated", [](const BitMatrix &b, const Point &v) { return b.translated(toCell(v)); },
            nb::arg("vector"), "The same cells moved by the vector. Both readings agree on this.");
    cls.def("__add__", [](const BitMatrix &b, const Point &v) { return b.translated(toCell(v)); },
            nb::is_operator());
    cls.def("__radd__", [](const BitMatrix &b, const Point &v) { return b.translated(toCell(v)); },
            nb::is_operator());
    cls.def("__sub__",
            [](const BitMatrix &b, const Point &v) {
                const Cell c = toCell(v);
                return b.translated(Cell(-c.x(), -c.y()));
            },
            nb::is_operator());
    cls.def("__iadd__",
            [](BitMatrix &b, const Point &v) -> BitMatrix & { return b += toCell(v); },
            nb::is_operator());
    cls.def("__isub__",
            [](BitMatrix &b, const Point &v) -> BitMatrix & { return b -= toCell(v); },
            nb::is_operator());

    // ---- symmetries --------------------------------------------------------
    //
    // The unprefixed ones are symmetries *of the covered region*, so they
    // commute with the conversion: a.rotated90(k).asPolygonSet() and
    // Transformation.rotation90(k) * a.asPolygonSet() agree. A symmetry carries
    // the square of a cell onto the square of another cell, which is not the
    // square of the image of that cell as a point -- hence the lattice pair,
    // which maps the lower-left corners instead. Transposition is the exception
    // the two readings agree on.
    cls.def("reflected", &BitMatrix::reflected, "The region reflected through the origin.");
    cls.def("__neg__", [](const BitMatrix &b) { return b.reflected(); }, nb::is_operator());
    cls.def("reflectedX", &BitMatrix::reflectedX, "The region reflected across the x axis.");
    cls.def("reflectedY", &BitMatrix::reflectedY, "The region reflected across the y axis.");
    cls.def("transposed", &BitMatrix::transposed,
            "The cells with their coordinates swapped; the same operation as "
            "latticeTransposed(), which the two readings agree on.");
    cls.def("rotated90", &BitMatrix::rotated90, nb::arg("k") = 1,
            "The region turned k quarter turns counterclockwise.");
    cls.def("rotate90", &BitMatrix::rotate90, nb::arg("k") = 1, nb::rv_policy::reference_internal,
            "Turns the region k quarter turns counterclockwise, in place.");
    cls.def("latticeReflected", &BitMatrix::latticeReflected,
            "The cells as lattice points reflected through the origin: cell c maps to -c, "
            "where reflected() maps it to -c - (1,1).");
    cls.def("latticeReflectedX", &BitMatrix::latticeReflectedX,
            "The cells as lattice points reflected across the x axis.");
    cls.def("latticeReflectedY", &BitMatrix::latticeReflectedY,
            "The cells as lattice points reflected across the y axis.");
    cls.def("latticeTransposed", &BitMatrix::latticeTransposed,
            "The cells with their coordinates swapped; the same operation as transposed().");
    cls.def("latticeRotated90", &BitMatrix::latticeRotated90, nb::arg("k") = 1,
            "The cells as lattice points turned k quarter turns counterclockwise.");
    cls.def("latticeRotate90", &BitMatrix::latticeRotate90, nb::arg("k") = 1,
            nb::rv_policy::reference_internal,
            "Turns the cells as lattice points k quarter turns counterclockwise, in place.");

    // ---- Minkowski operations and morphology -------------------------------
    cls.def("latticeMinkowskiSum", &BitMatrix::latticeMinkowskiSum, nb::arg("other"),
            "The sum of the two cell sets read as lattice points, over a window that is "
            "exactly the bounding box of the result. This is the family to reach for in "
            "morphology: a one-cell matrix is its identity.");
    cls.def("latticeMinkowskiErosion", &BitMatrix::latticeMinkowskiErosion, nb::arg("other"),
            "The exact dual of latticeMinkowskiSum: the lattice points p with p + other "
            "inside this matrix, over this window shrunk by other's bounding box. Eroding by "
            "a matrix with no cell is vacuously true and fills the window. With operator~, "
            "one of the two operations that compute from the window rather than the cells.");
    cls.def("latticeOpening", &BitMatrix::latticeOpening, nb::arg("other"),
            "The lattice erosion by other, then the lattice sum with it.");
    cls.def("latticeClosing", &BitMatrix::latticeClosing, nb::arg("other"),
            "The lattice sum with other, then the lattice erosion by it.");
    cls.def("minkowskiSum", &BitMatrix::minkowskiSum, nb::arg("other"),
            "The sum of the two *regions*, the one the shapes compute, so it commutes with "
            "the conversion. The unit square is not its identity -- U + U is the two-by-two "
            "square -- so this is the lattice sum dilated by that block, one cell wider and "
            "taller in each direction.");
    cls.def("__add__", [](const BitMatrix &a, const BitMatrix &b) { return a.minkowskiSum(b); },
            nb::is_operator());
    cls.def("minkowskiErosion", &BitMatrix::minkowskiErosion, nb::arg("other"),
            "The region erosion, regularized exactly as PolygonSet regularizes its own, which "
            "is what keeps it on the grid: a cell eroded by a cell is a single point, which "
            "the shapes report as a degenerate shape and this reports as empty.");
    cls.def("interior", &BitMatrix::interior, nb::arg("adjacency") = pgl::GridAdjacency::edge,
            "The set cells all of whose neighbors are set.");
    cls.def("boundary", &BitMatrix::boundary, nb::arg("adjacency") = pgl::GridAdjacency::edge,
            "The rest of the set cells; one on the window border always belongs here.");

    // ---- connectivity ------------------------------------------------------
    cls.def("connectedComponents", &BitMatrix::connectedComponents,
            nb::arg("adjacency") = pgl::GridAdjacency::edge,
            "One trimmed matrix per connected group of cells.");
    cls.def("componentCount", &BitMatrix::componentCount, nb::arg("adjacency") = pgl::GridAdjacency::edge,
            "How many connected groups the cells form.");
    cls.def("isConnected", &BitMatrix::isConnected, nb::arg("adjacency") = pgl::GridAdjacency::edge,
            "Whether the cells form exactly one connected group.");
    cls.def("fillHoles", &BitMatrix::fillHoles, nb::arg("adjacency") = pgl::GridAdjacency::edge,
            "The matrix with every group of unset cells that cannot reach outside added. The "
            "background is walked with the complementary adjacency, which is what keeps a "
            "diagonal chain of cells from both being connected and letting the background "
            "leak through it.");
    cls.def("holeCount", &BitMatrix::holeCount, nb::arg("adjacency") = pgl::GridAdjacency::edge,
            "How many cells fillHoles would add, counted as groups.");
    cls.def("eulerNumber", &BitMatrix::eulerNumber, nb::arg("adjacency") = pgl::GridAdjacency::edge,
            "Components minus holes, read off the sixteen patterns a two-by-two block of "
            "cells can show rather than by a flood fill.");

    // ---- hv-convexity ------------------------------------------------------
    cls.def("fillRows", &BitMatrix::fillRows,
            "Closes the gap of every row in place, returning whether anything changed.");
    cls.def("fillColumns", &BitMatrix::fillColumns,
            "Closes the gap of every column in place, returning whether anything changed.");
    cls.def("makeHvConvex", &BitMatrix::makeHvConvex,
            "Alternates fillRows and fillColumns to a fixed point, giving the smallest "
            "hv-convex superset; returns how many cells it added.");
    cls.def("isRowConvex", &BitMatrix::isRowConvex,
            "Whether every row meets the set cells in a single interval.");
    cls.def("isColumnConvex", &BitMatrix::isColumnConvex,
            "Whether every column meets the set cells in a single interval.");
    cls.def("isHvConvex", &BitMatrix::isHvConvex,
            "Whether every row and every column meets the cells in one interval.");

    // ---- rasterizing any shape --------------------------------------------
    //
    // The two bracket a shape: inner keeps the cells it covers, outer the cells
    // it meets. Each costs one exact predicate per cell of the window, against
    // the one pass per row that asBitMatrix takes for the rectilinear case.
    m.def("innerRaster",
          [](const AnyShape &shape, const Rectangle &window) {
              return rasterize(shape, toGridWindow(window), true);
          },
          nb::arg("shape"), nb::arg("window"),
          "The shape rasterized into the cells of window it wholly covers, so the result is "
          "covered by the shape.");
    m.def("innerRaster", [](const AnyShape &shape) { return rasterize(shape, boundingWindow(shape), true); },
          nb::arg("shape"),
          "The shape rasterized into the cells it wholly covers, over the smallest cell window "
          "covering its bounding box. Raises for a shape with no bounding box (Line, "
          "OrientedLine, Ray, Halfplane, an unbounded HalfplaneIntersection); pass a window "
          "explicitly for those.");
    m.def("outerRaster",
          [](const AnyShape &shape, const Rectangle &window) {
              return rasterize(shape, toGridWindow(window), false);
          },
          nb::arg("shape"), nb::arg("window"),
          "The shape rasterized into the cells of window it meets, boundary included, so the "
          "result covers the shape.");
    m.def("outerRaster", [](const AnyShape &shape) { return rasterize(shape, boundingWindow(shape), false); },
          nb::arg("shape"),
          "The shape rasterized into the cells it meets, over the smallest cell window covering "
          "its bounding box. Raises for a shape with no bounding box; pass a window explicitly "
          "for those.");
}
