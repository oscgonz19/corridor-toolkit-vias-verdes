"""
Geometry manipulation utilities for corridor processing.

Functions for extracting, merging, and projecting geometries.
All functions assume input is in a projected CRS (meters).

Key concepts:
    - Corridor axis: A single LineString representing the centerline
    - Feature projection: Finding the nearest point on the axis
    - Perpendicular distance: Shortest distance from feature to axis
"""

from typing import Union, Tuple

from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import linemerge
import geopandas as gpd


def to_single_line(geom: Union[LineString, MultiLineString]) -> LineString:
    """
    Convert geometry to a single LineString.

    MultiLineStrings (common in KML exports) are merged into a single
    continuous line. If segments are connected, uses `linemerge` for
    proper topology. Otherwise, concatenates coordinates.

    Args:
        geom: Input geometry. Must be LineString or MultiLineString.

    Returns:
        LineString: Single continuous line.
            Coordinate order is preserved from input.

    Raises:
        TypeError: If geometry is not a line type.

    Example:
        >>> # KML often exports fragmented lines
        >>> multi = MultiLineString([[(0,0), (1,1)], [(1,1), (2,0)]])
        >>> line = to_single_line(multi)
        >>> print(line.geom_type)
        'LineString'
        >>> print(len(list(line.coords)))
        3

    Note:
        This function does not reorder disconnected segments.
        For disconnected geometries, consider manual inspection.
    """
    if geom.geom_type == "LineString":
        return geom

    if geom.geom_type == "MultiLineString":
        # Try linemerge first for properly connected lines
        merged = linemerge(geom)
        if merged.geom_type == "LineString":
            return merged

        # Fallback: concatenate all coordinates in order
        coords = [pt for ln in geom.geoms for pt in ln.coords]
        return LineString(coords)

    raise TypeError(f"Expected LineString or MultiLineString, got {geom.geom_type}")


def extract_single_line(gdf: gpd.GeoDataFrame) -> LineString:
    """
    Extract corridor axis as a single LineString from GeoDataFrame.

    Takes the first geometry and ensures it's a single LineString.
    Use this to extract the corridor centerline from loaded data.

    Args:
        gdf: GeoDataFrame containing corridor axis.
            Must have at least one geometry.
            First geometry should be a LineString or MultiLineString.
            CRS should be projected (EPSG:9377) for distance calculations.

    Returns:
        LineString: Corridor axis as single line.
            Units: meters (if CRS is projected)
            Length: `line.length` gives total corridor length

    Raises:
        IndexError: If GeoDataFrame is empty.
        TypeError: If first geometry is not a line type.

    Example:
        >>> axis_gdf = load_geodata("corridor.gpkg")
        >>> axis_gdf = ensure_crs(axis_gdf, target_epsg=9377)
        >>> axis_line = extract_single_line(axis_gdf)
        >>>
        >>> print(f"Corridor length: {axis_line.length/1000:.1f} km")
        Corridor length: 12.5 km

    Note:
        The line direction matters for chainage calculations.
        Chainage increases from the first vertex to the last.
    """
    if len(gdf) == 0:
        raise IndexError("GeoDataFrame is empty, cannot extract axis")

    geom = gdf.geometry.iloc[0]
    return to_single_line(geom)


def get_centroids(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Replace geometries with their centroids, preserving originals.

    Useful for projecting polygon/line features to the corridor axis.
    The centroid is used for distance calculations while the original
    geometry is preserved for visualization.

    Args:
        gdf: Input GeoDataFrame with any geometry type.

    Returns:
        gpd.GeoDataFrame: Copy with:
            - 'geometry': Centroid points
            - 'geom_ori': Original geometries (new column)

    Example:
        >>> # Project polygon features using their centroids
        >>> sources_gdf = load_geodata("quarries.gpkg")
        >>> sources_gdf = ensure_crs(sources_gdf)
        >>> sources_cent = get_centroids(sources_gdf)
        >>>
        >>> # Now project centroids to axis
        >>> annotated = annotate_to_axis(sources_cent, axis_line)

    Note:
        Centroid is the geometric center, which may fall outside
        the polygon for concave shapes.
    """
    result = gdf.copy()
    result["geom_ori"] = result.geometry
    result["geometry"] = result.geometry.centroid
    return result


def project_point_to_line(
    point: Point,
    line: LineString
) -> Tuple[Point, float]:
    """
    Project a point onto a line, finding the nearest point.

    Uses Shapely's `project` and `interpolate` for efficient
    nearest-point calculation.

    Args:
        point: Point to project. Must be in same CRS as line.
        line: Reference line (corridor axis).
            Should be in projected CRS (meters).

    Returns:
        Tuple[Point, float]:
            - Point: Projected point on the line (nearest point)
            - float: Distance along line from start to projected point (meters)

    Example:
        >>> # Find where a borehole projects onto the corridor
        >>> borehole = Point(1005000, 1003500)
        >>> projected, chainage_m = project_point_to_line(borehole, axis_line)
        >>>
        >>> print(f"Projects to: ({projected.x:.0f}, {projected.y:.0f})")
        >>> print(f"Chainage: K{int(chainage_m/1000)}+{int(chainage_m%1000):03d}")

    Note:
        The distance returned is the chainage (distance along axis),
        NOT the perpendicular distance. Use `perpendicular_distance()`
        for the offset from axis.
    """
    dist_along = line.project(point)
    projected = line.interpolate(dist_along)
    return projected, dist_along


def perpendicular_distance(point: Point, line: LineString) -> float:
    """
    Calculate perpendicular (shortest) distance from point to line.

    This is the offset distance used in corridor annotation.

    Args:
        point: Point to measure from.
        line: Reference line (corridor axis).
            Both must be in same projected CRS.

    Returns:
        float: Shortest distance in coordinate units (meters for projected CRS).
            Always positive (absolute distance).

    Example:
        >>> offset = perpendicular_distance(borehole, axis_line)
        >>> print(f"Offset: {offset:.0f} m from axis")

    Note:
        Returns absolute distance. For signed offset (left/right),
        use cross-product calculation in projection module.
    """
    return point.distance(line)
