"""BitMatrix: one bit per cell of a rectangular window of the integer grid.

Cell ``(x, y)`` is the closed unit square ``[x, x+1] x [y, y+1]``, named by its
lower-left corner. Two readings of a cell run through the whole class, and which
one an operation takes is in its name: unprefixed it is that unit square (the
predicates, the measures, the symmetries, ``minkowskiSum``/``minkowskiErosion``,
all of which commute with ``asPolygonSet``), while ``lattice``-prefixed it is the
single point at the corner, which is what makes a structuring element behave.

A cell crosses into Python either as a pair of plain ints or as an ordinary
``Point``; a fractional coordinate is refused rather than rounded, since rounding
it would move the cell. Everything the matrix hands back is an ordinary bound
shape, and the measures stay exact.
"""

from fractions import Fraction

import pytest

import pypgl
from pypgl import (
    BitMatrix,
    Canvas,
    Convex,
    Disk,
    GridAdjacency,
    Line,
    Point,
    Polygon,
    PolygonSet,
    PolygonWithHoles,
    Rectangle,
    Triangle,
    innerRaster,
    outerRaster,
)


def square(x, y, width, height):
    """A matrix whose every cell of a width-by-height window from (x, y) is set."""
    matrix = BitMatrix(x, y, width, height)
    matrix.setAll()
    return matrix


def cells(matrix):
    """The set cells as a sorted list of int pairs, for order-free comparison."""
    return sorted((int(cell[0]), int(cell[1])) for cell in matrix)


# --- construction and the window --------------------------------------------


def test_default_window_is_empty():
    matrix = BitMatrix()
    assert matrix.emptyWindow()
    assert matrix.empty()
    assert matrix.width() == 0 and matrix.height() == 0
    assert len(matrix) == 0


def test_window_from_origin_and_extent():
    matrix = BitMatrix(Point(2, 3), 4, 5)
    assert matrix.origin() == Point(2, 3)
    assert matrix.width() == 4 and matrix.height() == 5
    assert matrix.window() == Rectangle(Point(2, 3), Point(6, 8))
    assert matrix.empty()  # the window is sized, no cell is set


def test_int_and_point_origins_agree():
    assert BitMatrix(2, 3, 4, 5).window() == BitMatrix(Point(2, 3), 4, 5).window()


def test_window_from_rectangle_is_the_inverse_of_window():
    box = Rectangle(Point(-1, -2), Point(3, 4))
    assert BitMatrix(box).window() == box


def test_nonpositive_extent_leaves_the_window_empty():
    assert BitMatrix(0, 0, 0, 5).emptyWindow()
    assert BitMatrix(0, 0, 5, -1).emptyWindow()


def test_window_is_fixed_so_writing_outside_it_is_a_no_op():
    matrix = BitMatrix(0, 0, 2, 2)
    matrix.set(5, 5)
    assert matrix.empty()
    assert matrix.get(5, 5) is False  # reading outside is False, not an error
    assert matrix.inWindow(1, 1) and not matrix.inWindow(5, 5)


def test_resized_drops_what_the_new_window_cannot_hold():
    matrix = square(0, 0, 4, 4)
    smaller = matrix.resized(Rectangle(Point(1, 1), Point(3, 3)))
    assert smaller.count() == 4
    assert cells(smaller) == [(1, 1), (1, 2), (2, 1), (2, 2)]


def test_trimmed_is_the_smallest_window_holding_the_cells():
    matrix = BitMatrix(0, 0, 10, 10)
    matrix.set(3, 4)
    matrix.set(5, 6)
    trimmed = matrix.trimmed()
    assert trimmed.window() == Rectangle(Point(3, 4), Point(6, 7))
    assert cells(trimmed) == cells(matrix)


def test_same_window():
    assert square(0, 0, 2, 2).sameWindow(BitMatrix(0, 0, 2, 2))
    assert not square(0, 0, 2, 2).sameWindow(BitMatrix(1, 0, 2, 2))


# --- one cell, both spellings ------------------------------------------------


def test_get_set_reset_flip_take_ints_or_a_point():
    matrix = BitMatrix(0, 0, 4, 4)
    matrix.set(1, 1)
    matrix.set(Point(2, 2))
    assert matrix.get(1, 1) and matrix.get(Point(2, 2))
    assert cells(matrix) == [(1, 1), (2, 2)]

    matrix.reset(Point(1, 1))
    assert not matrix.get(1, 1)
    matrix.flip(2, 2)
    assert not matrix.get(2, 2)
    matrix.flip(Point(3, 3))
    assert matrix.get(3, 3)

    matrix.set(0, 0, True)
    matrix.set(Point(3, 3), False)
    assert cells(matrix) == [(0, 0)]


def test_set_all_and_clear():
    matrix = BitMatrix(0, 0, 3, 3)
    matrix.setAll()
    assert matrix.count() == 9
    matrix.clear()
    assert matrix.empty()


def test_a_fractional_coordinate_is_refused_not_rounded():
    matrix = BitMatrix(0, 0, 4, 4)
    with pytest.raises(RuntimeError, match="not an integer"):
        matrix.set(Point(Fraction(1, 2), 1))
    with pytest.raises(RuntimeError, match="not an integer"):
        matrix.get(Point(1, Fraction(7, 2)))
    assert matrix.empty()


def test_a_whole_fraction_names_a_cell():
    matrix = BitMatrix(0, 0, 4, 4)
    matrix.set(Point(Fraction(6, 2), 1))
    assert matrix.get(3, 1)


# --- container protocol ------------------------------------------------------


def test_len_and_iteration_are_over_the_set_cells():
    matrix = BitMatrix(0, 0, 3, 3)
    matrix.set(0, 0)
    matrix.set(2, 1)
    assert len(matrix) == matrix.count() == 2
    assert list(matrix) == [Point(0, 0), Point(2, 1)]  # row-major order


def test_in_asks_whether_that_cell_is_set():
    matrix = BitMatrix(0, 0, 3, 3)
    matrix.set(1, 1)
    assert Point(1, 1) in matrix
    assert Point(0, 0) not in matrix
    # The cell, not the covered region: (3/2, 3/2) lies inside cell (1, 1) but
    # names no cell of its own.
    with pytest.raises(RuntimeError, match="not an integer"):
        Point(Fraction(3, 2), Fraction(3, 2)) in matrix


def test_lattice_cells_and_rectangles():
    matrix = BitMatrix(0, 0, 3, 2)
    matrix.set(0, 0)
    matrix.set(1, 0)
    matrix.set(0, 1)
    assert matrix.lattice() == [Point(0, 0), Point(1, 0), Point(0, 1)]
    assert matrix.cells()[0] == Rectangle(Point(0, 0), Point(1, 1))
    # One rectangle per run of a row, so the bottom row's two cells merge.
    assert matrix.rectangles() == [
        Rectangle(Point(0, 0), Point(2, 1)),
        Rectangle(Point(0, 1), Point(1, 2)),
    ]


# --- measures, exact ---------------------------------------------------------


def test_measures_are_exact():
    matrix = square(0, 0, 3, 2)
    assert matrix.area() == 6
    assert isinstance(matrix.area(), Fraction)
    assert matrix.perimeter() == 10
    assert matrix.centroid() == Point(Fraction(3, 2), 1)
    assert matrix.pointInside() == Point(Fraction(1, 2), Fraction(1, 2))
    assert matrix.bbox() == Rectangle(Point(0, 0), Point(3, 2))


def test_measures_of_an_empty_matrix():
    matrix = BitMatrix(0, 0, 4, 4)
    assert matrix.area() == 0
    assert matrix.bbox() == Rectangle()
    with pytest.raises(RuntimeError, match="no cell is set"):
        matrix.centroid()
    with pytest.raises(RuntimeError, match="no cell is set"):
        matrix.pointInside()


# --- rasterizing a rectilinear region ---------------------------------------


def test_polygon_as_bit_matrix():
    polygon = Polygon([0, 0, 4, 0, 4, 2, 2, 2, 2, 4, 0, 4])
    matrix = polygon.asBitMatrix()
    assert matrix.count() == 12
    assert matrix.window() == Rectangle(Point(0, 0), Point(4, 4))
    assert BitMatrix(polygon) == matrix  # the constructor is the same operation


def test_region_and_set_as_bit_matrix_leave_the_holes_unset():
    region = PolygonWithHoles(
        Polygon([0, 0, 6, 0, 6, 6, 0, 6]), [Polygon([2, 2, 4, 2, 4, 4, 2, 4])]
    )
    assert region.asBitMatrix().count() == 36 - 4
    assert PolygonSet([region]).asBitMatrix().count() == 32
    assert BitMatrix(region) == region.asBitMatrix()
    assert BitMatrix(PolygonSet([region])) == PolygonSet([region]).asBitMatrix()


def test_as_bit_matrix_refuses_a_non_rectilinear_shape():
    with pytest.raises(RuntimeError, match="not rectilinear"):
        Polygon([0, 0, 4, 0, 0, 4]).asBitMatrix()


def test_as_bit_matrix_refuses_a_fractional_coordinate():
    half = Fraction(1, 2)
    polygon = Polygon([Point(0, 0), Point(4, 0), Point(4, half), Point(0, half)])
    with pytest.raises(RuntimeError, match="not an integer"):
        polygon.asBitMatrix()


def test_round_trip_through_the_polygon_set():
    polygon = Polygon([0, 0, 4, 0, 4, 2, 2, 2, 2, 4, 0, 4])
    assert polygon.asBitMatrix().asPolygonSet() == PolygonSet([polygon.asPolygonWithHoles()])


def test_as_polygon_set_drops_vertices_in_a_straight_stretch():
    # A filled box comes back as four corners however many cells it holds.
    region = square(0, 0, 5, 5).asPolygonWithHoles()
    assert region.outer().size() == 4


def test_as_polygon_with_holes_needs_one_edge_connected_group():
    matrix = BitMatrix(0, 0, 5, 1)
    matrix.set(0, 0)
    matrix.set(4, 0)
    with pytest.raises(RuntimeError, match="not edge-connected"):
        matrix.asPolygonWithHoles()
    # asPolygonSet has no such precondition.
    assert matrix.asPolygonSet().componentCount() == 2


def test_convex_hull_is_of_the_covered_region():
    matrix = Polygon([0, 0, 4, 0, 4, 2, 2, 2, 2, 4, 0, 4]).asBitMatrix()
    assert matrix.convexHull() == Convex(
        [Point(0, 0), Point(4, 0), Point(4, 2), Point(2, 4), Point(0, 4)]
    )


# --- set algebra -------------------------------------------------------------


def test_set_algebra():
    left, right = square(0, 0, 2, 2), square(1, 1, 2, 2)
    assert cells(left & right) == [(1, 1)]
    assert (left | right).count() == 7
    assert (left ^ right).count() == 6
    assert cells(left.difference(right)) == [(0, 0), (0, 1), (1, 0)]
    assert left.symmetricDifference(right) == left ^ right


def test_the_result_window_is_the_smallest_that_provably_loses_no_cell():
    left, right = square(0, 0, 2, 2), square(1, 1, 2, 2)
    assert (left & right).window() == Rectangle(Point(1, 1), Point(2, 2))
    assert (left | right).window() == Rectangle(Point(0, 0), Point(3, 3))
    assert left.difference(right).window() == left.window()


def test_compound_assignment_never_moves_its_window():
    left, right = square(0, 0, 2, 2), square(1, 1, 2, 2)
    combined = square(0, 0, 2, 2)
    combined |= right
    assert combined.window() == left.window()
    assert combined.count() == 4  # right's cell (2, 2) falls outside and is dropped

    combined = square(0, 0, 2, 2)
    combined &= right
    assert cells(combined) == [(1, 1)]
    combined = square(0, 0, 2, 2)
    combined ^= right
    assert cells(combined) == [(0, 0), (0, 1), (1, 0)]


def test_counts_without_building_the_result():
    left, right = square(0, 0, 2, 2), square(1, 1, 2, 2)
    assert left.andCount(right) == (left & right).count()
    assert left.orCount(right) == (left | right).count()
    assert left.xorCount(right) == (left ^ right).count()


def test_complement_is_within_the_window_not_against_the_plane():
    matrix = BitMatrix(0, 0, 3, 3)
    matrix.set(1, 1)
    complement = ~matrix
    assert complement.count() == 8
    assert complement.window() == matrix.window()


# --- comparison --------------------------------------------------------------


def test_the_window_is_part_of_the_value():
    wide = BitMatrix(0, 0, 4, 4)
    wide.set(1, 1)
    tight = wide.trimmed()
    assert wide != tight
    assert wide.samePointSet(tight)
    assert tight.samePointSet(wide)


def test_every_window_covering_no_cell_has_one_canonical_form():
    assert BitMatrix(0, 0, 4, 4).trimmed() == BitMatrix(9, 9, 2, 2).trimmed()


def test_ordering_is_total_and_carries_no_geometric_meaning():
    a, b = square(0, 0, 2, 2), square(1, 1, 2, 2)
    assert (a < b) != (b < a)
    assert (a <= b) and not (a >= b) if a < b else (b <= a)


def test_a_matrix_is_mutable_and_therefore_unhashable():
    with pytest.raises(TypeError):
        hash(square(0, 0, 2, 2))


def test_repr_names_the_window_and_the_count():
    assert repr(square(1, 2, 3, 4)) == "BitMatrix[3x4 from (1,2), 12 cells]"


# --- predicates, against another matrix -------------------------------------


def test_contains_and_interior_contains():
    outer, inner = square(0, 0, 5, 5), square(1, 1, 3, 3)
    assert outer.contains(inner)
    assert not inner.contains(outer)
    # interiorContains is contains against the vertex-adjacency interior, so a
    # cell touching the boundary even at a corner disqualifies it.
    assert outer.interiorContains(square(1, 1, 3, 3))
    assert not outer.interiorContains(square(0, 0, 3, 3))


def test_boundary_contains_holds_only_for_an_empty_other():
    matrix = square(0, 0, 3, 3)
    assert matrix.boundaryContains(BitMatrix())
    assert not matrix.boundaryContains(square(0, 0, 1, 1))


def test_intersects_counts_a_shared_corner():
    # Cells (0,0) and (1,1) share only the point (1,1), which the closed squares
    # do share -- so intersects holds while interiorsIntersect does not.
    left, right = BitMatrix(0, 0, 3, 3), BitMatrix(0, 0, 3, 3)
    left.set(0, 0)
    right.set(1, 1)
    assert left.intersects(right)
    assert not left.interiorsIntersect(right)
    right.set(0, 0)
    assert left.interiorsIntersect(right)


# --- translation and the symmetries -----------------------------------------


def test_translation_reads_the_same_under_both_hats():
    matrix = square(0, 0, 2, 2)
    assert matrix.translated(Point(5, 5)).origin() == Point(5, 5)
    assert (matrix + Point(1, 1)).origin() == Point(1, 1)
    assert (Point(1, 1) + matrix).origin() == Point(1, 1)
    assert (matrix - Point(1, 1)).origin() == Point(-1, -1)

    moved = square(0, 0, 2, 2)
    moved += Point(2, 0)
    assert moved.origin() == Point(2, 0)
    moved -= Point(2, 0)
    assert moved == matrix


def test_the_two_reflections_differ_by_a_cell():
    matrix = BitMatrix(0, 0, 3, 3)
    matrix.set(0, 0)
    # The region reflection maps cell c to -c - (1,1); the lattice one to -c.
    assert cells(matrix.reflected()) == [(-1, -1)]
    assert cells(matrix.latticeReflected()) == [(0, 0)]
    assert matrix.reflected() == -matrix


def test_reflections_along_one_axis():
    matrix = BitMatrix(0, 0, 3, 3)
    matrix.set(2, 1)
    assert cells(matrix.reflectedX()) == [(2, -2)]
    assert cells(matrix.latticeReflectedX()) == [(2, -1)]
    assert cells(matrix.reflectedY()) == [(-3, 1)]
    assert cells(matrix.latticeReflectedY()) == [(-2, 1)]


def test_transposition_is_the_one_the_two_readings_agree_on():
    matrix = BitMatrix(0, 0, 3, 3)
    matrix.set(2, 0)
    assert matrix.transposed() == matrix.latticeTransposed()
    assert cells(matrix.transposed()) == [(0, 2)]


def test_rotations_commute_with_the_conversion():
    matrix = Polygon([0, 0, 4, 0, 4, 2, 2, 2, 2, 4, 0, 4]).asBitMatrix()
    for turns in range(-4, 5):
        rotated = matrix.rotated90(turns).asPolygonSet()
        expected = pypgl.Transformation.rotation90(turns) * matrix.asPolygonSet()
        assert rotated.samePointSet(expected)
    assert matrix.rotated90(4) == matrix


def test_rotate90_is_in_place_and_fluent():
    matrix = square(0, 0, 2, 3)
    assert matrix.rotate90() is matrix
    assert matrix.width() == 3 and matrix.height() == 2
    matrix.latticeRotate90(-1)
    assert matrix.width() == 2 and matrix.height() == 3


def test_lattice_rotation_is_a_cell_off_the_region_one():
    matrix = BitMatrix(0, 0, 2, 2)
    matrix.set(1, 0)
    assert cells(matrix.rotated90()) == [(-1, 1)]
    assert cells(matrix.latticeRotated90()) == [(0, 1)]


# --- Minkowski operations and morphology ------------------------------------


def test_a_one_cell_matrix_is_the_identity_of_the_lattice_sum():
    unit = BitMatrix(0, 0, 1, 1)
    unit.setAll()
    matrix = square(0, 0, 3, 2)
    assert matrix.latticeMinkowskiSum(unit).samePointSet(matrix)


def test_the_region_sum_is_the_lattice_sum_dilated_by_the_unit_block():
    left, right = square(0, 0, 2, 2), square(0, 0, 2, 2)
    lattice = left.latticeMinkowskiSum(right)
    region = left.minkowskiSum(right)
    assert lattice.width() == 3 and lattice.height() == 3
    assert region.width() == 4 and region.height() == 4  # one cell wider each way
    assert region == left + right


def test_the_region_sum_commutes_with_the_conversion():
    left = Polygon([0, 0, 3, 0, 3, 1, 0, 1]).asBitMatrix()
    right = Polygon([0, 0, 1, 0, 1, 2, 0, 2]).asBitMatrix()
    summed = (left + right).asPolygonSet()
    expected = left.asPolygonSet().minkowskiSum(right.asPolygonSet())
    assert summed.samePointSet(expected)


def test_lattice_erosion_is_the_exact_dual_of_the_lattice_sum():
    body, stamp = square(0, 0, 6, 6), square(0, 0, 2, 2)
    eroded = body.latticeMinkowskiErosion(stamp)
    assert eroded.count() == 25  # a 5x5 of admissible placements
    assert eroded.latticeMinkowskiSum(stamp).samePointSet(body)


def test_eroding_by_a_matrix_with_no_cell_fills_the_window():
    body = BitMatrix(0, 0, 3, 3)
    body.set(1, 1)
    assert body.latticeMinkowskiErosion(BitMatrix()).count() == 9


def test_region_erosion_regularizes_away_the_lower_dimensional_part():
    # A cell eroded by a cell is the single point 0, which has no area.
    cell = square(0, 0, 1, 1)
    assert cell.minkowskiErosion(cell).empty()
    assert square(0, 0, 4, 4).minkowskiErosion(cell).count() == 9


def test_lattice_opening_and_closing():
    matrix = square(0, 0, 4, 4)
    stamp = square(0, 0, 2, 2)
    assert matrix.latticeOpening(stamp).samePointSet(matrix)
    assert matrix.latticeClosing(stamp).samePointSet(matrix)

    notched = square(0, 0, 4, 4)
    notched.reset(1, 1)
    assert notched.latticeClosing(stamp).count() >= notched.count()


def test_interior_and_boundary():
    matrix = square(0, 0, 3, 3)
    # Every cell touches the window border, so with 4-adjacency only the center
    # has all four neighbors set.
    assert cells(matrix.interior()) == [(1, 1)]
    assert matrix.boundary().count() == 8
    assert matrix.interior(GridAdjacency.vertex).count() == 1
    assert matrix.interior().count() + matrix.boundary().count() == matrix.count()


# --- connectivity ------------------------------------------------------------


def test_connected_components_are_trimmed():
    matrix = BitMatrix(0, 0, 5, 1)
    matrix.set(0, 0)
    matrix.set(4, 0)
    components = matrix.connectedComponents()
    assert len(components) == 2
    assert matrix.componentCount() == 2
    assert not matrix.isConnected()
    assert all(component.width() == 1 for component in components)


def test_adjacency_decides_whether_a_diagonal_chain_connects():
    matrix = BitMatrix(0, 0, 3, 3)
    matrix.set(0, 0)
    matrix.set(1, 1)
    assert matrix.componentCount(GridAdjacency.edge) == 2
    assert matrix.componentCount(GridAdjacency.vertex) == 1
    assert matrix.isConnected(GridAdjacency.vertex)


def test_fill_holes_and_hole_count():
    ring = square(0, 0, 3, 3)
    ring.reset(1, 1)
    assert ring.holeCount() == 1
    assert ring.fillHoles().count() == 9
    assert ring.count() == 8  # fillHoles does not mutate


def test_euler_number_is_components_minus_holes():
    ring = square(0, 0, 3, 3)
    ring.reset(1, 1)
    assert ring.eulerNumber() == 0
    assert ring.componentCount() - ring.holeCount() == ring.eulerNumber()
    assert square(0, 0, 2, 2).eulerNumber() == 1


# --- hv-convexity ------------------------------------------------------------


def test_fill_rows_and_columns_report_whether_anything_changed():
    matrix = BitMatrix(0, 0, 3, 1)
    matrix.set(0, 0)
    matrix.set(2, 0)
    assert matrix.fillRows() is True
    assert matrix.count() == 3
    assert matrix.fillRows() is False


def test_make_hv_convex_returns_how_many_cells_it_added():
    # A row with a gap in it: rows and columns each have to be one interval, so
    # two cells in different rows and columns are already hv-convex.
    matrix = BitMatrix(0, 0, 3, 3)
    matrix.set(0, 0)
    matrix.set(2, 0)
    matrix.set(2, 2)
    assert not matrix.isHvConvex()
    added = matrix.makeHvConvex()
    assert added == matrix.count() - 3
    assert matrix.isHvConvex()
    assert matrix.isRowConvex() and matrix.isColumnConvex()
    assert matrix.makeHvConvex() == 0


# --- rasterizing any shape ---------------------------------------------------


def test_inner_and_outer_raster_bracket_a_shape():
    disk = Disk(Point(4, 4), 3)
    window = Rectangle(Point(0, 0), Point(9, 9))
    inner, outer = innerRaster(disk, window), outerRaster(disk, window)
    assert inner.count() == 16
    assert outer.count() == 44
    assert outer.contains(inner)


def test_the_default_window_is_the_bounding_box_rounded_outward():
    triangle = Triangle(Point(0, 0), Point(5, 0), Point(0, 5))
    assert outerRaster(triangle).window() == Rectangle(Point(0, 0), Point(5, 5))
    assert innerRaster(triangle).count() == 10
    assert outerRaster(triangle).count() == 19


def test_a_fractional_bounding_box_is_rounded_outward():
    half = Fraction(1, 2)
    triangle = Triangle(Point(half, half), Point(3, half), Point(half, 3))
    window = outerRaster(triangle).window()
    assert window == Rectangle(Point(0, 0), Point(3, 3))
    assert outerRaster(triangle).contains(innerRaster(triangle))


def test_an_unbounded_shape_rasterizes_over_an_explicit_window_only():
    line = Line(Point(0, 0), Point(1, 1))
    window = Rectangle(Point(0, 0), Point(9, 9))
    assert outerRaster(line, window).count() == 25
    with pytest.raises(RuntimeError, match="bbox"):
        outerRaster(line)


def test_rasterizing_a_rectilinear_region_agrees_with_as_bit_matrix():
    # asBitMatrix keeps the cells the region covers, which is exactly what
    # innerRaster answers. outerRaster is strictly wider: it also keeps the cells
    # the region only *touches* along its boundary.
    polygon = Polygon([0, 0, 4, 0, 4, 2, 2, 2, 2, 4, 0, 4])
    assert innerRaster(polygon).samePointSet(polygon.asBitMatrix())
    assert outerRaster(polygon).contains(polygon.asBitMatrix())
    assert outerRaster(polygon).count() > polygon.asBitMatrix().count()


# --- drawing -----------------------------------------------------------------


def test_a_matrix_draws_as_one_element_and_renders_inline():
    matrix = Polygon([0, 0, 4, 0, 4, 2, 2, 2, 2, 4, 0, 4]).asBitMatrix()
    svg = Canvas().draw(matrix).toSVG()
    assert svg.startswith("<svg")
    # Streaming the matrix is streaming its polygon set.
    assert svg == Canvas().draw(matrix.asPolygonSet()).toSVG()
    # _repr_svg_ renders a one-shot canvas at the smaller inline size.
    assert matrix._repr_svg_() == matrix.asPolygonSet()._repr_svg_()


def test_drawing_the_cells_as_separate_elements():
    matrix = square(0, 0, 2, 2)
    svg = Canvas().draw(matrix.rectangles()).toSVG()
    # One element per merged run, against the single path a matrix draws as.
    assert svg.count("<rect") == len(matrix.rectangles()) == 2
    assert Canvas().draw(matrix).toSVG().count("<rect") == 0


# --- shielded from the point sugar ------------------------------------------


def test_a_matrix_is_not_a_fixed_extent_shape():
    matrix = square(0, 0, 3, 3)
    # No indexing over defining points: the container protocol is over cells.
    with pytest.raises(TypeError):
        matrix[0]
    assert not hasattr(matrix, "index")
    assert not hasattr(matrix, "vertices")
