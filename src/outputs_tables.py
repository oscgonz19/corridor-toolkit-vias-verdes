"""CSV and tabular output generation."""

from pathlib import Path

import pandas as pd
import geopandas as gpd


def export_summary_csv(
    gdf: gpd.GeoDataFrame,
    output_path: str | Path,
    drop_geometry_axis: bool = True
) -> None:
    """
    Export annotated GeoDataFrame to CSV summary.

    Args:
        gdf: Annotated GeoDataFrame from annotate_to_axis()
        output_path: Output CSV path
        drop_geometry_axis: Drop the geometry_axis column
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = gdf.copy()

    # Drop geometry columns for clean CSV
    cols_to_drop = []
    if drop_geometry_axis and "geometry_axis" in df.columns:
        cols_to_drop.append("geometry_axis")

    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    df.to_csv(output_path, index=False)


def export_geopackage(
    gdf: gpd.GeoDataFrame,
    output_path: str | Path,
    layer_name: str = "features"
) -> None:
    """
    Export GeoDataFrame to GeoPackage.

    Args:
        gdf: GeoDataFrame to export
        output_path: Output GeoPackage path
        layer_name: Layer name in GeoPackage
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # GeoPackage doesn't support multiple geometry columns, drop geometry_axis
    df = gdf.copy()
    if "geometry_axis" in df.columns:
        df = df.drop(columns=["geometry_axis"])

    df.to_file(output_path, layer=layer_name, driver="GPKG")


def create_chainage_table(
    chainage_points: list[tuple],
    crs_epsg: int
) -> pd.DataFrame:
    """
    Create summary table of chainage points.

    Args:
        chainage_points: List of (Point, distance_m, label) tuples
        crs_epsg: CRS EPSG code for coordinate display

    Returns:
        DataFrame with chainage summary
    """
    records = []
    for point, dist_m, label in chainage_points:
        records.append({
            "abscisa": label,
            "distancia_m": dist_m,
            "x": point.x,
            "y": point.y,
            "crs": f"EPSG:{crs_epsg}"
        })
    return pd.DataFrame(records)
