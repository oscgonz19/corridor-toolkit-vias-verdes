"""
Chainage (abscisas) calculations along corridor axis.

Chainage is the standard civil engineering method for referencing positions
along linear infrastructure (roads, railways, pipelines). In Latin America,
the K+format is commonly used:

    K5+250 = 5 kilometers + 250 meters = 5,250 meters from origin

All distances are in meters. Input geometries must be in a projected CRS
(EPSG:9377 MAGNA-SIRGAS recommended for Colombia).

Functions:
    - format_chainage: Convert meters to K+format string
    - chainage: Calculate chainage for a point
    - generate_chainage_points: Create markers at regular intervals
"""

from typing import List, Tuple, Union

from shapely.geometry import LineString, Point
import geopandas as gpd
import pandas as pd

from .config import DEFAULT_CHAINAGE


def format_chainage(
    distance_m: float,
    template: str = DEFAULT_CHAINAGE.format_template
) -> str:
    """
    Format distance as K+format chainage label.

    Converts a distance in meters to the standard K+format used in
    Latin American civil engineering: K{km}+{meters}.

    Args:
        distance_m: Distance along axis in meters.
            Must be non-negative.
        template: Format string (for advanced customization).
            Default produces "K{km}+{meters:03d}".

    Returns:
        str: Formatted chainage label.
            Format: "K{km}+{meters:03d}"
            Examples: "K0+000", "K5+250", "K11+795"

    Examples:
        >>> format_chainage(0)
        'K0+000'
        >>> format_chainage(5250)
        'K5+250'
        >>> format_chainage(11795)
        'K11+795'
        >>> format_chainage(5250.6)  # Rounds to nearest meter
        'K5+251'

    Note:
        Values are rounded to the nearest meter before formatting.
        For sub-meter precision, use raw distance values.
    """
    km, rest = divmod(int(round(distance_m)), 1000)
    return f"K{km}+{rest:03d}"


def parse_chainage(label: str) -> float:
    """
    Parse K+format chainage label back to meters.

    Args:
        label: Chainage string in K+format (e.g., "K5+250").

    Returns:
        float: Distance in meters.

    Raises:
        ValueError: If label format is invalid.

    Examples:
        >>> parse_chainage("K5+250")
        5250.0
        >>> parse_chainage("K0+000")
        0.0
        >>> parse_chainage("K11+795")
        11795.0
    """
    try:
        # Remove 'K' prefix and split on '+'
        parts = label.upper().replace("K", "").split("+")
        km = int(parts[0])
        rest = int(parts[1])
        return float(km * 1000 + rest)
    except (IndexError, ValueError) as e:
        raise ValueError(f"Invalid chainage format: {label}") from e


def chainage(line: LineString, point: Point) -> Tuple[float, str]:
    """
    Calculate chainage (distance along axis) for a point.

    Projects the point onto the line and measures the distance
    from the line's start vertex to the projection point.

    Args:
        line: Corridor axis LineString.
            Must be in projected CRS (meters).
        point: Point to calculate chainage for.
            Can be on or off the line (projects to nearest point).

    Returns:
        Tuple[float, str]:
            - float: Distance in meters from line start
            - str: Formatted K+format label

    Example:
        >>> line = LineString([(0, 0), (10000, 0)])  # 10 km horizontal
        >>> point = Point(5000, 100)  # 100m offset at K5+000
        >>>
        >>> dist_m, label = chainage(line, point)
        >>> print(f"{label}: {dist_m:.0f} m")
        K5+000: 5000 m

    Note:
        The point is projected to the nearest location on the line.
        For points beyond the line endpoints, chainage will be 0
        or line.length.
    """
    dist_m = line.project(point)
    label = format_chainage(dist_m)
    return dist_m, label


def generate_chainage_points(
    line: LineString,
    interval_m: float = DEFAULT_CHAINAGE.interval_m,
    start_m: float = 0
) -> List[Tuple[Point, float, str]]:
    """
    Generate chainage marker points at regular intervals along axis.

    Creates a series of points along the corridor axis, each with
    its chainage distance and formatted label. Useful for creating
    K+ markers for maps and CAD exports.

    Args:
        line: Corridor axis LineString.
            Must be in projected CRS (meters).
            Total length determines number of points generated.
        interval_m: Distance between markers in meters.
            Default: 500m (produces K0+000, K0+500, K1+000, ...).
            Common values: 100, 250, 500, 1000.
        start_m: Starting chainage offset in meters.
            Default: 0 (start from line beginning).
            Use non-zero for corridor sections that don't start at K0+000.

    Returns:
        List[Tuple[Point, float, str]]: List of marker tuples:
            - Point: Location on the line (in line's CRS)
            - float: Distance in meters from start
            - str: K+format label

    Example:
        >>> line = LineString([(0, 0), (2500, 0)])  # 2.5 km
        >>> markers = generate_chainage_points(line, interval_m=500)
        >>>
        >>> for point, dist_m, label in markers:
        ...     print(f"{label}: ({point.x:.0f}, {point.y:.0f})")
        K0+000: (0, 0)
        K0+500: (500, 0)
        K1+000: (1000, 0)
        K1+500: (1500, 0)
        K2+000: (2000, 0)
        K2+500: (2500, 0)

    Note:
        The last marker is placed at or before line.length.
        If interval doesn't divide evenly, final segment may be shorter.
    """
    total_length = line.length
    points = []

    distance = start_m
    while distance <= total_length:
        point = line.interpolate(distance)
        label = format_chainage(distance)
        points.append((point, distance, label))
        distance += interval_m

    return points


def chainage_points_to_gdf(
    chainage_points: List[Tuple[Point, float, str]],
    crs: Union[str, int]
) -> gpd.GeoDataFrame:
    """
    Convert chainage marker list to GeoDataFrame.

    Transforms the output of `generate_chainage_points()` into a
    GeoDataFrame suitable for export or visualization.

    Args:
        chainage_points: List from generate_chainage_points().
        crs: Coordinate reference system (EPSG code or string).
            Should match the CRS of the source line.

    Returns:
        gpd.GeoDataFrame: Chainage markers with columns:
            - abscisa_m: Distance in meters (float)
            - abscisa_lbl: K+format label (str)
            - geometry: Point geometry

    Example:
        >>> markers = generate_chainage_points(axis_line, interval_m=500)
        >>> markers_gdf = chainage_points_to_gdf(markers, crs=9377)
        >>> markers_gdf.to_file("chainage_markers.gpkg")
    """
    data = {
        "abscisa_m": [p[1] for p in chainage_points],
        "abscisa_lbl": [p[2] for p in chainage_points],
        "geometry": [p[0] for p in chainage_points],
    }

    crs_str = f"EPSG:{crs}" if isinstance(crs, int) else crs
    return gpd.GeoDataFrame(pd.DataFrame(data), crs=crs_str)
