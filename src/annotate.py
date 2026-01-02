"""
Feature annotation relative to corridor axis.

Projects features (boreholes, structures, sources, etc.) onto the corridor
axis and calculates:
    - Chainage: Distance along axis (K+format)
    - Offset: Perpendicular distance from axis
    - Coordinates: Original and projected positions

All distances are in meters. Input must be in projected CRS (EPSG:9377).

Main function: annotate_to_axis()
"""

from typing import Optional

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString

from .chainage import chainage
from .geometry import project_point_to_line, perpendicular_distance
from .config import DEFAULT_CRS


def annotate_to_axis(
    gdf_points: gpd.GeoDataFrame,
    axis_line: LineString,
    name_field: str = "Name",
    crs_epsg: int = DEFAULT_CRS.calc_epsg
) -> gpd.GeoDataFrame:
    """
    Project features to corridor axis and calculate chainage/offset.

    This is the main annotation function. For each feature:
    1. Projects it onto the axis (finds nearest point on axis)
    2. Calculates perpendicular distance (offset from axis)
    3. Calculates chainage (distance along axis)

    Args:
        gdf_points: GeoDataFrame with point features to annotate.
            Must be in projected CRS (EPSG:9377 recommended).
            For polygon/line features, use get_centroids() first.
        axis_line: Corridor axis LineString.
            Must be in same CRS as gdf_points.
            Direction determines chainage direction (increasing).
        name_field: Column name containing feature identifiers.
            Default: "Name" (standard KML/GeoJSON field).
            If column missing, features labeled "sin_nombre".
        crs_epsg: EPSG code for output GeoDataFrame.
            Default: 9377 (MAGNA-SIRGAS Colombia).

    Returns:
        gpd.GeoDataFrame: Annotated features with columns:
            - nombre (str): Feature name/identifier
            - dist_m (float): Perpendicular offset from axis (meters)
            - abscisa_m (float): Distance along axis (meters)
            - abscisa_lbl (str): K+format chainage label
            - x, y (float): Original feature coordinates
            - x_axis, y_axis (float): Projected point on axis
            - geometry (Point): Original point geometry
            - geometry_axis (Point): Projected point on axis

    Example:
        >>> # Load and prepare data
        >>> axis_gdf = load_geodata("corridor.gpkg")
        >>> axis_gdf = ensure_crs(axis_gdf, target_epsg=9377)
        >>> axis_line = extract_single_line(axis_gdf)
        >>>
        >>> # Load features (boreholes, sources, etc.)
        >>> features = load_geodata("boreholes.gpkg")
        >>> features = ensure_crs(features, target_epsg=9377)
        >>>
        >>> # Annotate to axis
        >>> annotated = annotate_to_axis(features, axis_line)
        >>>
        >>> # View results
        >>> print(annotated[["nombre", "abscisa_lbl", "dist_m"]])
              nombre abscisa_lbl   dist_m
        0  Borehole A     K2+150   125.3
        1  Borehole B     K5+780   342.1
        2  Borehole C     K8+430    87.6

    Note:
        - dist_m is always positive (absolute offset)
        - For signed offset (left/right of axis), use cross-product
        - Polygon features should be converted to centroids first
    """
    records = []

    for _, row in gdf_points.iterrows():
        point = row.geometry

        # Project to axis
        point_on_axis, dist_along = project_point_to_line(point, axis_line)

        # Calculate distances
        perp_dist = perpendicular_distance(point, axis_line)
        dist_m, chainage_lbl = chainage(axis_line, point_on_axis)

        # Get name (handle missing field)
        name = row.get(name_field, "sin_nombre")
        if pd.isna(name):
            name = "sin_nombre"

        records.append({
            "nombre": name,
            "dist_m": perp_dist,
            "abscisa_m": dist_m,
            "abscisa_lbl": chainage_lbl,
            "x": point.x,
            "y": point.y,
            "x_axis": point_on_axis.x,
            "y_axis": point_on_axis.y,
        })

    df = pd.DataFrame(records)

    # Create GeoDataFrame with original point geometry
    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df.x, df.y)],
        crs=f"EPSG:{crs_epsg}"
    )

    # Add projected geometry as separate column
    gdf["geometry_axis"] = [Point(xy) for xy in zip(df.x_axis, df.y_axis)]

    return gdf


def filter_by_radius(
    gdf: gpd.GeoDataFrame,
    radius_m: float,
    distance_col: str = "dist_m"
) -> gpd.GeoDataFrame:
    """
    Filter annotated features by distance from axis.

    Keeps only features within the specified offset distance.
    Useful for focusing on features in the corridor influence zone.

    Args:
        gdf: Annotated GeoDataFrame from annotate_to_axis().
        radius_m: Maximum perpendicular distance in meters.
            Features farther than this are excluded.
        distance_col: Column containing offset values.
            Default: "dist_m" (output from annotate_to_axis).

    Returns:
        gpd.GeoDataFrame: Filtered copy with only nearby features.

    Example:
        >>> # Keep only features within 1 km of axis
        >>> nearby = filter_by_radius(annotated, radius_m=1000)
        >>> print(f"Features within 1 km: {len(nearby)}")

        >>> # Filter for immediate corridor (100m buffer)
        >>> immediate = filter_by_radius(annotated, radius_m=100)
    """
    return gdf[gdf[distance_col] <= radius_m].copy()


def sort_by_chainage(
    gdf: gpd.GeoDataFrame,
    chainage_col: str = "abscisa_m"
) -> gpd.GeoDataFrame:
    """
    Sort annotated features by chainage (distance along axis).

    Args:
        gdf: Annotated GeoDataFrame from annotate_to_axis().
        chainage_col: Column containing chainage values.
            Default: "abscisa_m".

    Returns:
        gpd.GeoDataFrame: Sorted copy (ascending chainage).

    Example:
        >>> # Sort boreholes from start to end of corridor
        >>> sorted_bh = sort_by_chainage(annotated_boreholes)
    """
    return gdf.sort_values(chainage_col).reset_index(drop=True)
