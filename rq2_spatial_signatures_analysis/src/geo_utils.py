"""Geometry helpers for the 800 m Voronoi-clipped Rail catchments."""

from __future__ import annotations

import numpy as np
from scipy.spatial import Voronoi


def finite_voronoi_polygons(vor: Voronoi, radius: float | None = None):
    """Convert a 2-D SciPy Voronoi diagram to finite polygons in point order."""
    if vor.points.shape[1] != 2:
        raise ValueError("Voronoi input must be two-dimensional")

    new_regions: list[list[int]] = []
    new_vertices = vor.vertices.tolist()
    centre = vor.points.mean(axis=0)
    if radius is None:
        radius = float(np.ptp(vor.points, axis=0).max() * 2)

    all_ridges: dict[int, list[tuple[int, int, int]]] = {}
    for (point_1, point_2), (vertex_1, vertex_2) in zip(
        vor.ridge_points, vor.ridge_vertices, strict=True
    ):
        all_ridges.setdefault(point_1, []).append((point_2, vertex_1, vertex_2))
        all_ridges.setdefault(point_2, []).append((point_1, vertex_1, vertex_2))

    for point_index, region_index in enumerate(vor.point_region):
        vertices = vor.regions[region_index]
        if all(vertex >= 0 for vertex in vertices):
            new_regions.append(vertices)
            continue

        ridges = all_ridges[point_index]
        new_region = [vertex for vertex in vertices if vertex >= 0]
        for point_2, vertex_1, vertex_2 in ridges:
            if vertex_2 < 0:
                vertex_1, vertex_2 = vertex_2, vertex_1
            if vertex_1 >= 0:
                continue
            tangent = vor.points[point_2] - vor.points[point_index]
            tangent /= np.linalg.norm(tangent)
            normal = np.array([-tangent[1], tangent[0]])
            midpoint = vor.points[[point_index, point_2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - centre, normal)) * normal
            far_point = vor.vertices[vertex_2] + direction * radius
            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        polygon_vertices = np.asarray([new_vertices[v] for v in new_region])
        polygon_centre = polygon_vertices.mean(axis=0)
        angles = np.arctan2(
            polygon_vertices[:, 1] - polygon_centre[1],
            polygon_vertices[:, 0] - polygon_centre[0],
        )
        new_region = np.asarray(new_region)[np.argsort(angles)].tolist()
        new_regions.append(new_region)

    return new_regions, np.asarray(new_vertices)

