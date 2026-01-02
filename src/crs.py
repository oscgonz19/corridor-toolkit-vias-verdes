"""
Coordinate Reference System (CRS) utilities.

This module handles CRS validation and transformation for corridor data.
All distance calculations require projected coordinates in meters.

Standard CRS workflow:
    Input (WGS84, EPSG:4326) → Calculation (MAGNA-SIRGAS, EPSG:9377) → Display (Web Mercator, EPSG:3857)

EPSG Codes:
    - 4326: WGS84 (GPS/KML input, degrees)
    - 9377: MAGNA-SIRGAS Colombia Origin-National (calculations, meters)
    - 3857: Web Mercator (basemap display)
    - 32618: UTM Zone 18N (alternative metric)
"""

from typing import Union

import geopandas as gpd

from .config import DEFAULT_CRS


def ensure_crs(
    gdf: gpd.GeoDataFrame,
    target_epsg: int = DEFAULT_CRS.calc_epsg,
    assume_input_epsg: int = DEFAULT_CRS.input_epsg
) -> gpd.GeoDataFrame:
    """
    Validate and transform GeoDataFrame to target CRS.

    This is the primary CRS function for the pipeline. It ensures all
    geometries are in the correct projected CRS before distance calculations.

    Behavior:
        1. If GeoDataFrame has no CRS, assumes `assume_input_epsg` (default: WGS84)
        2. If CRS differs from target, transforms coordinates
        3. If already in target CRS, returns unchanged

    Args:
        gdf: Input GeoDataFrame. May have any CRS or None.
        target_epsg: Target EPSG code for transformation.
            Default: 9377 (MAGNA-SIRGAS Colombia, meters).
            Must be a projected CRS for distance calculations.
        assume_input_epsg: EPSG to assume if input has no CRS.
            Default: 4326 (WGS84, typical for GPS/KML data).

    Returns:
        gpd.GeoDataFrame: GeoDataFrame in target CRS.
            - Coordinates are transformed (not just metadata)
            - Units: meters for EPSG:9377

    Raises:
        ValueError: If transformation fails (invalid geometries).

    Example:
        >>> # Load data (typically WGS84 from KML)
        >>> gdf = load_geodata("corridor.kmz")
        >>> print(gdf.crs)
        EPSG:4326
        >>>
        >>> # Transform to MAGNA-SIRGAS for calculations
        >>> gdf = ensure_crs(gdf, target_epsg=9377)
        >>> print(gdf.crs)
        EPSG:9377
        >>>
        >>> # Now distances are in meters
        >>> print(gdf.geometry.iloc[0].length)
        12500.0  # meters

    Warning:
        Never calculate distances on WGS84 (EPSG:4326) coordinates!
        Geographic coordinates are in degrees, not meters.
    """
    # Handle missing CRS
    if gdf.crs is None:
        gdf = gdf.set_crs(assume_input_epsg)

    # Transform if needed
    current_epsg = gdf.crs.to_epsg()
    if current_epsg != target_epsg:
        return gdf.to_crs(epsg=target_epsg)

    return gdf


def reproject(
    gdf: gpd.GeoDataFrame,
    target_epsg: int
) -> gpd.GeoDataFrame:
    """
    Reproject GeoDataFrame to specified CRS.

    Unlike `ensure_crs`, this function requires input to have a valid CRS
    and performs explicit reprojection without assumptions.

    Args:
        gdf: Input GeoDataFrame with valid CRS.
        target_epsg: Target EPSG code.

    Returns:
        gpd.GeoDataFrame: Reprojected GeoDataFrame.

    Raises:
        ValueError: If input GeoDataFrame has no CRS.

    Example:
        >>> # Reproject to Web Mercator for map display
        >>> gdf_display = reproject(gdf, target_epsg=3857)
    """
    if gdf.crs is None:
        raise ValueError("Input GeoDataFrame has no CRS. Use ensure_crs() instead.")
    return gdf.to_crs(epsg=target_epsg)


def get_crs_info(epsg: int) -> dict:
    """
    Get human-readable CRS information.

    Args:
        epsg: EPSG code.

    Returns:
        dict: CRS metadata with keys:
            - epsg: EPSG code (int)
            - name: Human-readable name (str)
            - units: Coordinate units (str)

    Example:
        >>> info = get_crs_info(9377)
        >>> print(info)
        {'epsg': 9377, 'name': 'MAGNA-SIRGAS Colombia', 'units': 'meters'}
    """
    crs_data = {
        4326: ("WGS84 (GPS)", "degrees"),
        9377: ("MAGNA-SIRGAS Colombia", "meters"),
        32618: ("UTM Zone 18N", "meters"),
        3857: ("Web Mercator", "meters"),
    }

    name, units = crs_data.get(epsg, (f"EPSG:{epsg}", "unknown"))

    return {
        "epsg": epsg,
        "name": name,
        "units": units,
    }


def validate_projected_crs(gdf: gpd.GeoDataFrame) -> bool:
    """
    Check if GeoDataFrame is in a projected (metric) CRS.

    Args:
        gdf: GeoDataFrame to validate.

    Returns:
        bool: True if CRS is projected (uses meters), False if geographic.

    Example:
        >>> gdf = ensure_crs(gdf, target_epsg=9377)
        >>> assert validate_projected_crs(gdf), "Must be in projected CRS!"
    """
    if gdf.crs is None:
        return False
    return gdf.crs.is_projected
