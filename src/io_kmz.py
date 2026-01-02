"""
Geospatial I/O operations for corridor data.

Supports loading corridor data from multiple formats:
- KMZ (Google Earth compressed KML)
- GeoPackage (OGC standard, recommended)
- GeoJSON, Shapefile, KML

All functions return GeoDataFrames. CRS is preserved from source file;
use `crs.ensure_crs()` to transform to calculation CRS (EPSG:9377).
"""

import os
import zipfile
import tempfile
from pathlib import Path
from typing import Optional, Union

import geopandas as gpd


def load_geodata(
    path: Union[str, Path],
    layer: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Load geospatial data from various formats.

    Automatically detects format based on file extension and delegates
    to the appropriate loader. Supported formats: KMZ, GPKG, GeoJSON,
    Shapefile, KML.

    Args:
        path: Path to geospatial file. Supports:
            - .kmz (Google Earth)
            - .gpkg (GeoPackage - recommended)
            - .geojson, .json (GeoJSON)
            - .shp (Shapefile)
            - .kml (KML)
        layer: Optional layer name for multi-layer formats (GPKG).
            If None, reads the first/default layer.

    Returns:
        gpd.GeoDataFrame: Features with geometry column.
            CRS is preserved from source file.
            Common columns: 'Name', 'description', 'geometry'.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If format cannot be determined or read.

    Example:
        >>> gdf = load_geodata("corridor.gpkg")
        >>> print(gdf.crs)
        EPSG:4326
        >>> gdf = ensure_crs(gdf, target_epsg=9377)  # Transform to MAGNA-SIRGAS

    Note:
        Input CRS is typically WGS84 (EPSG:4326) from GPS/KML sources.
        Always use `ensure_crs()` before distance calculations.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".kmz":
        return load_kmz(path)
    elif suffix == ".gpkg":
        return load_geopackage(path, layer)
    elif suffix in (".geojson", ".json"):
        return gpd.read_file(path)
    elif suffix == ".shp":
        return gpd.read_file(path)
    elif suffix == ".kml":
        return gpd.read_file(path, driver="KML")
    else:
        # Try generic read
        return gpd.read_file(path)


def load_kmz(
    kmz_path: Union[str, Path],
    temp_dir: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Extract and load KML from a KMZ archive.

    KMZ files are ZIP archives containing KML (Keyhole Markup Language)
    files, typically exported from Google Earth. This function extracts
    the KML to a temporary directory and loads it as a GeoDataFrame.

    Args:
        kmz_path: Path to KMZ file.
        temp_dir: Optional directory for KML extraction.
            If None, uses system temp directory.
            Temporary files are not automatically cleaned up.

    Returns:
        gpd.GeoDataFrame: Features from KMZ.
            CRS: Typically EPSG:4326 (WGS84) from Google Earth.
            Columns: 'Name', 'description', 'geometry' (standard KML fields).

    Raises:
        FileNotFoundError: If KMZ file doesn't exist.
        ValueError: If no KML file found in archive.

    Example:
        >>> gdf = load_kmz("corridor_axis.kmz")
        >>> print(gdf.crs)
        EPSG:4326
        >>> print(gdf.geometry.iloc[0].geom_type)
        'LineString'

    Note:
        For new projects, prefer GeoPackage (.gpkg) over KMZ.
        KMZ is useful for data exported from Google Earth.
    """
    kmz_path = Path(kmz_path)
    if not kmz_path.exists():
        raise FileNotFoundError(f"KMZ file not found: {kmz_path}")

    if temp_dir is None:
        temp_dir = tempfile.mkdtemp(prefix="vias_verdes_kmz_")

    with zipfile.ZipFile(kmz_path) as kmz:
        kml_files = [n for n in kmz.namelist() if n.endswith(".kml")]
        if not kml_files:
            raise ValueError(f"No KML file found in {kmz_path}")

        kml = kml_files[0]
        kmz.extract(kml, temp_dir)

    kml_path = os.path.join(temp_dir, kml)
    gdf = gpd.read_file(kml_path, driver="KML")

    return gdf


def load_geopackage(
    gpkg_path: Union[str, Path],
    layer: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Load features from a GeoPackage file.

    GeoPackage is the recommended format for corridor data. It supports
    multiple layers, preserves CRS metadata, and handles large datasets
    efficiently.

    Args:
        gpkg_path: Path to GeoPackage (.gpkg) file.
        layer: Optional layer name. If None, reads the first layer.
            Use `fiona.listlayers(gpkg_path)` to list available layers.

    Returns:
        gpd.GeoDataFrame: Features from specified layer.
            CRS is preserved from file metadata.

    Raises:
        FileNotFoundError: If GeoPackage file doesn't exist.

    Example:
        >>> # Load corridor axis
        >>> axis_gdf = load_geopackage("demo_data/demo_axis.gpkg")
        >>>
        >>> # Load specific layer from multi-layer file
        >>> features = load_geopackage("project.gpkg", layer="boreholes")
    """
    gpkg_path = Path(gpkg_path)
    if not gpkg_path.exists():
        raise FileNotFoundError(f"GeoPackage not found: {gpkg_path}")

    if layer:
        return gpd.read_file(gpkg_path, layer=layer)
    return gpd.read_file(gpkg_path)


def save_geopackage(
    gdf: gpd.GeoDataFrame,
    gpkg_path: Union[str, Path],
    layer: str = "features"
) -> Path:
    """
    Save GeoDataFrame to GeoPackage format.

    Creates parent directories if they don't exist. Overwrites
    existing layer if present.

    Args:
        gdf: GeoDataFrame to save. Must have valid CRS set.
        gpkg_path: Output path for GeoPackage file.
        layer: Layer name within GeoPackage.

    Returns:
        Path: Absolute path to saved file.

    Example:
        >>> save_geopackage(projected_features, "outputs/features.gpkg", layer="sources")
    """
    gpkg_path = Path(gpkg_path)
    gpkg_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(gpkg_path, layer=layer, driver="GPKG")
    return gpkg_path.absolute()
