"""DXF (CAD) export functionality."""

from pathlib import Path
from typing import Optional

import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon, MultiPolygon

from .config import DEFAULT_CRS


def export_axis_dxf(
    axis_line: LineString,
    output_path: str | Path,
    layer_name: str = "EJE",
    crs_epsg: int = DEFAULT_CRS.calc_epsg
) -> None:
    """
    Export corridor axis to DXF.

    Args:
        axis_line: Corridor centerline
        output_path: Output DXF path
        layer_name: CAD layer name
        crs_epsg: CRS EPSG code
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    gdf = gpd.GeoDataFrame(
        {"Layer": [layer_name]},
        geometry=[axis_line],
        crs=f"EPSG:{crs_epsg}"
    )
    gdf.to_file(output_path, driver="DXF", engine="fiona")


def export_points_dxf(
    gdf: gpd.GeoDataFrame,
    output_path: str | Path,
    layer_name: str = "POINTS",
    geometry_col: str = "geometry"
) -> None:
    """
    Export point features to DXF.

    Args:
        gdf: GeoDataFrame with point geometries
        output_path: Output DXF path
        layer_name: CAD layer name
        geometry_col: Geometry column to use
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use specified geometry column
    if geometry_col != "geometry" and geometry_col in gdf.columns:
        export_gdf = gdf.set_geometry(geometry_col)
    else:
        export_gdf = gdf.copy()

    # Create clean GDF with just layer and geometry
    dxf_gdf = gpd.GeoDataFrame(
        {"Layer": [layer_name] * len(export_gdf)},
        geometry=export_gdf.geometry.tolist(),
        crs=export_gdf.crs
    )
    dxf_gdf.to_file(output_path, driver="DXF", engine="fiona")


def export_polygons_dxf(
    gdf: gpd.GeoDataFrame,
    output_path: str | Path,
    layer_name: str = "POLYGONS",
    geometry_col: Optional[str] = None
) -> None:
    """
    Export polygon features to DXF.

    Args:
        gdf: GeoDataFrame with polygon geometries
        output_path: Output DXF path
        layer_name: CAD layer name
        geometry_col: Optional alternative geometry column (e.g., 'geom_ori')
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use original geometry if specified
    if geometry_col and geometry_col in gdf.columns:
        export_gdf = gdf.set_geometry(geometry_col)
    else:
        export_gdf = gdf.copy()

    dxf_gdf = gpd.GeoDataFrame(
        {"Layer": [layer_name] * len(export_gdf)},
        geometry=export_gdf.geometry.tolist(),
        crs=export_gdf.crs
    )
    dxf_gdf.to_file(output_path, driver="DXF", engine="fiona")


def export_corridor_dxf(
    output_dir: str | Path,
    tramo: str,
    axis_line: LineString,
    sources_gdf: Optional[gpd.GeoDataFrame] = None,
    disposal_gdf: Optional[gpd.GeoDataFrame] = None,
    crs_epsg: int = DEFAULT_CRS.calc_epsg
) -> dict[str, Path]:
    """
    Export complete corridor to multiple DXF files.

    Args:
        output_dir: Output directory
        tramo: Corridor section identifier
        axis_line: Corridor centerline
        sources_gdf: Material sources GeoDataFrame
        disposal_gdf: Disposal zones GeoDataFrame
        crs_epsg: CRS EPSG code

    Returns:
        Dict mapping layer type to output path
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {}

    # Axis
    axis_path = output_dir / f"EJE_{tramo.upper()}.dxf"
    export_axis_dxf(axis_line, axis_path, f"EJE_{tramo.upper()}", crs_epsg)
    outputs["axis"] = axis_path

    # Sources
    if sources_gdf is not None and len(sources_gdf) > 0:
        sources_path = output_dir / "FUENTES.dxf"
        geometry_col = "geom_ori" if "geom_ori" in sources_gdf.columns else "geometry"
        export_polygons_dxf(sources_gdf, sources_path, "FUENTES", geometry_col)
        outputs["sources"] = sources_path

    # Disposal
    if disposal_gdf is not None and len(disposal_gdf) > 0:
        disposal_path = output_dir / "ZONAS_DISPOSICION.dxf"
        geometry_col = "geom_ori" if "geom_ori" in disposal_gdf.columns else "geometry"
        export_polygons_dxf(disposal_gdf, disposal_path, "ZONAS_DISPOSICION", geometry_col)
        outputs["disposal"] = disposal_path

    return outputs
