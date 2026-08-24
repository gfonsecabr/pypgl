"""The shortest collision-free translation of a polygonal robot.

The Python port of pgl's `examples/example_motion.cpp`.

A configuration is the position of the robot's reference point (the origin of
`robot`). The reference point may be placed at `x` exactly when `robot + x` is
contained in `room`, so the free configuration space is the Minkowski erosion
`room.minkowskiErosion(robot)` — the set of translations that keep the robot
inside. That is the whole idea: a shape moving in a room becomes a point moving
in the eroded room.

Shortest paths in that free space turn only at its vertices. The reduced
visibility graph keeps just the edges where a taut path can bend; the two
endpoints are not vertices of it, so they need edges to every corner they can
see. `shortestPath` then routes across it with A*, using straight-line distance
as both the edge weight and the lower bound.

The drawing shows the room in grey, the free space in green, its reduced
visibility graph in blue, the robot's motion in orange, and a translucent robot
at each waypoint — each of which really is inside the room, which is what the
erosion means.

Output: example_motion.svg
"""

import pypgl as pgl


def main():
    # A chamfered room with three staggered, slanted obstacles. A point could
    # take much tighter routes here than the hexagonal robot below.
    outer = pgl.Polygon([0, 6, 8, 0, 112, 0, 120, 6, 120, 69, 112, 75, 8, 75, 0, 69])
    holes = [
        pgl.Polygon([20, 13, 33, 11, 35, 14, 35, 51, 32, 53, 19, 51, 19, 15]),
        pgl.Polygon([47, 3, 60, 2, 62, 5, 62, 61, 59, 64, 46, 62, 46, 5]),
        pgl.Polygon([92, 11, 95, 15, 95, 66, 92, 53, 78, 51, 78, 15]),
    ]
    room = pgl.PolygonWithHoles(outer, holes)

    if not room.isValid():
        raise SystemExit("the room is not a valid polygon with holes")

    # The robot's reference point is its center, so its footprint is given
    # relative to the origin and `robot + position` is the robot placed there.
    # Convex states the useful geometric fact rather than merely storing it.
    robot = pgl.Convex([-4, 0, -2, -3, 2, -3, 4, 0, 2, 3, -2, 3])

    # An erosion can split a region into several components, so it answers a
    # PolygonSet even when — as here — the free space stays in one piece.
    free_space = room.minkowskiErosion(robot)
    if free_space.componentCount() != 1:
        raise SystemExit("this example expects one connected free space")
    free = free_space.component(0)

    # Deliberately interior points, not free-space vertices.
    source, target = pgl.Point(8, 8), pgl.Point(110, 10)
    if not free.contains(source) or not free.contains(target):
        raise SystemExit("the source or target does not fit the robot in the room")

    # Precisely the free-space vertices where a shortest path may bend, which
    # is a much smaller graph than the complete visibility one.
    graph = free.reducedVisibilityGraph()

    # The reduced graph deliberately omits arbitrary first and final hops, so
    # join both endpoints to every free-space vertex they can see. Adding the
    # vertex first also covers an endpoint that sees no corner at all.
    for endpoint in (source, target):
        graph.addVertex(endpoint)
        for vertex in free.visibleVertices(endpoint):
            graph.addEdge(endpoint, vertex)
    # A clear line of sight to the goal is a legal path with no graph vertex in
    # its interior, so it needs an edge of its own.
    if free.contains(pgl.Segment(source, target)):
        graph.addEdge(source, target)

    length = lambda a, b: a.distance(b)
    # Straight-line distance never overestimates what is left to travel, so it
    # is an admissible lower bound and A* can skip the corners that cannot
    # improve on the route found so far.
    path = graph.shortestPath(source, target, length, length)
    if not path:
        raise SystemExit(f"no collision-free path from {source} to {target}")

    print(f"configuration space: {free.vertexCount()} vertices, "
          f"{free.holeCount()} holes")
    print(f"reduced visibility graph: {graph.vertexCount()} vertices, "
          f"{graph.edgeCount()} edges")
    print(f"shortest motion ({len(path)} waypoints, "
          f"length {sum(length(a, b) for a, b in zip(path, path[1:])):.3f}): "
          + " ".join(str(p) for p in path))

    canvas = pgl.Canvas()

    # The workspace is useful context: its walls and obstacles are what the
    # robot must not touch.
    canvas.stroke("#64748b").strokeWidth("2px").fill("#e2e8f0").fillOpacity("0.8")
    canvas.draw(room)

    # The erosion's boundary is where the robot's center sits when the robot
    # just touches a wall. Drawn before the graph so both stay legible.
    canvas.stroke("#059669").strokeWidth("1.5px").fill("#a7f3d0").fillOpacity("0.35")
    canvas.draw(free)

    canvas.stroke("#93c5fd").strokeWidth("1px").strokeOpacity("0.9").fill("none")
    canvas.draw(pgl.Segment(u, v) for u, v in graph.edges())

    canvas.stroke("none").fillOpacity("15%").fill("#ea580c")
    canvas.draw(pgl.Polyline(path).minkowskiSum(robot))
    canvas.stroke("#ea580c").strokeWidth("3px").fill("none")
    canvas.draw(pgl.Polyline(path))

    # The footprints certify visually what the erosion means: every one of them
    # lies inside the original room.
    canvas.stroke("#c2410c").strokeWidth("1px").fill("#fdba74").fillOpacity("0.4")
    canvas.draw(robot + waypoint for waypoint in path)

    canvas.stroke("#1d4ed8").fill("#1d4ed8").pointRadius("5").draw(source)
    canvas.stroke("#7c2d12").fill("#7c2d12").pointRadius("5").draw(target)

    canvas.writeSVG("example_motion.svg")
    print("wrote example_motion.svg")


if __name__ == "__main__":
    main()
