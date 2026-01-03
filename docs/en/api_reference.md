# API Reference

## Complete Documentation of Modules, Classes, and Functions

---

## Module Architecture (SOLID Principles)

The codebase follows SOLID principles for maintainable, extensible design:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CORRIDOR TOOLKIT                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │   io_kmz    │   │    crs      │   │  geometry   │   │   config    │     │
│  │             │   │             │   │             │   │             │     │
│  │ [S] Single  │   │ [S] Single  │   │ [S] Single  │   │ [S] Single  │     │
│  │ Responsib.  │   │ Responsib.  │   │ Responsib.  │   │ Responsib.  │     │
│  │ File I/O    │   │ CRS ops     │   │ Geom ops    │   │ Config mgmt │     │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └─────────────┘     │
│         │                 │                 │                               │
│         └────────────────┬┴─────────────────┘                               │
│                          ▼                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CORE PROCESSING                              │   │
│  │  ┌─────────────┐                      ┌─────────────┐               │   │
│  │  │  chainage   │ ◄──── [O] Open ────► │  annotate   │               │   │
│  │  │             │      for extension   │             │               │   │
│  │  │ K+format    │                      │ Projection  │               │   │
│  │  │ generation  │                      │ to axis     │               │   │
│  │  └─────────────┘                      └─────────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                          │                                                   │
│         ┌────────────────┼────────────────┐                                 │
│         ▼                ▼                ▼                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │outputs_maps │  │ outputs_dxf │  │outputs_table│  [I] Interface          │
│  │             │  │             │  │             │  Segregation            │
│  │ PNG export  │  │ DXF export  │  │ CSV export  │  Each module has        │
│  │             │  │             │  │             │  focused interface      │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
│                                                                              │
│  ┌─────────────┐                                                            │
│  │  geology    │  [D] Dependency Inversion                                  │
│  │             │  High-level modules don't depend on low-level              │
│  │ SUCS/SPT    │  Both depend on abstractions (GeoDataFrame, LineString)   │
│  └─────────────┘                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **S**ingle Responsibility | Each module handles one concern (I/O, CRS, geometry, etc.) |
| **O**pen/Closed | Core functions accept parameters for extension without modification |
| **L**iskov Substitution | GeoDataFrames can be substituted for any geometry type |
| **I**nterface Segregation | Export modules (maps, dxf, tables) have focused interfaces |
| **D**ependency Inversion | High-level modules depend on GeoPandas/Shapely abstractions |

---

## Module: `src.config`

Configuration management using Pydantic models.

### Classes

#### `CRSConfig`

```python
class CRSConfig(BaseModel):
    """Coordinate Reference System configuration."""

    calc_epsg: int = 9377      # EPSG for calculations (MAGNA-SIRGAS)
    plot_epsg: int = 3857      # EPSG for display (Web Mercator)
    input_epsg: int = 4326     # EPSG for input data (WGS84)
```

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `calc_epsg` | `int` | `9377` | EPSG code for distance calculations (meters) |
| `plot_epsg` | `int` | `3857` | EPSG code for map display with basemaps |
| `input_epsg` | `int` | `4326` | EPSG code assumed for input without CRS |

---

#### `ChainageConfig`

```python
class ChainageConfig(BaseModel):
    """Chainage (abscisas) configuration."""

    interval_m: int = 500
    format_template: str = "K{km}+{rest:03d}"
```

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `interval_m` | `int` | `500` | Distance between chainage markers (meters) |
| `format_template` | `str` | `"K{km}+{rest:03d}"` | K+format template string |

---

#### `FilterConfig`

```python
class FilterConfig(BaseModel):
    """Spatial filtering configuration."""

    radius_m: float = 70000
```

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `radius_m` | `float` | `70000` | Maximum offset distance for filtering (meters) |

---

#### `OutputConfig`

```python
class OutputConfig(BaseModel):
    """Output configuration."""

    output_dir: Path = Path("outputs")
    dpi: int = 300
    figure_size: tuple[int, int] = (10, 10)
```

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_dir` | `Path` | `Path("outputs")` | Base output directory |
| `dpi` | `int` | `300` | PNG export resolution |
| `figure_size` | `tuple[int, int]` | `(10, 10)` | Figure dimensions in inches |

---

#### `CorridorConfig`

```python
class CorridorConfig(BaseModel):
    """Complete corridor processing configuration."""

    tramo: str                              # Required: section identifier
    axis_kmz: Path                          # Required: axis file path
    crs: CRSConfig = CRSConfig()
    chainage: ChainageConfig = ChainageConfig()
    filter: FilterConfig = FilterConfig()
    output: OutputConfig = OutputConfig()
    sources_kmz: Optional[Path] = None
    disposal_kmz: Optional[Path] = None
    boreholes_csv: Optional[Path] = None
```

**Attributes:**

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `tramo` | `str` | Yes | Corridor section identifier (e.g., "tramo6") |
| `axis_kmz` | `Path` | Yes | Path to corridor axis file |
| `crs` | `CRSConfig` | No | CRS configuration |
| `chainage` | `ChainageConfig` | No | Chainage configuration |
| `filter` | `FilterConfig` | No | Filtering configuration |
| `output` | `OutputConfig` | No | Output configuration |
| `sources_kmz` | `Optional[Path]` | No | Material sources file |
| `disposal_kmz` | `Optional[Path]` | No | Disposal zones file |
| `boreholes_csv` | `Optional[Path]` | No | Borehole data CSV |

**Methods:**

```python
def get_output_dir(self) -> Path:
    """Get output directory for this tramo."""
```

---

### Default Instances

```python
DEFAULT_CRS = CRSConfig()
DEFAULT_CHAINAGE = ChainageConfig()
DEFAULT_FILTER = FilterConfig()
DEFAULT_OUTPUT = OutputConfig()
```

---

## Module: `src.io_kmz`

Multi-format geospatial I/O operations.

### Functions

#### `load_geodata`

```python
def load_geodata(
    path: Union[str, Path],
    layer: Optional[str] = None
) -> gpd.GeoDataFrame
```

Load geospatial data from various formats with automatic detection.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `Union[str, Path]` | Required | Path to geospatial file |
| `layer` | `Optional[str]` | `None` | Layer name for multi-layer formats |

**Returns:** `gpd.GeoDataFrame` - Features with geometry column

**Supported Formats:**
- `.kmz` - Google Earth compressed KML
- `.gpkg` - GeoPackage (recommended)
- `.geojson`, `.json` - GeoJSON
- `.shp` - Shapefile
- `.kml` - KML

**Raises:**
- `FileNotFoundError` - If file does not exist
- `ValueError` - If format cannot be determined

**Example:**
```python
gdf = load_geodata("corridor.gpkg")
gdf = load_geodata("data.kmz")
```

---

#### `load_kmz`

```python
def load_kmz(
    kmz_path: Union[str, Path],
    temp_dir: Optional[str] = None
) -> gpd.GeoDataFrame
```

Extract and load KML from a KMZ archive.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `kmz_path` | `Union[str, Path]` | Required | Path to KMZ file |
| `temp_dir` | `Optional[str]` | `None` | Directory for KML extraction |

**Returns:** `gpd.GeoDataFrame` - Features from KMZ

**Raises:**
- `FileNotFoundError` - If KMZ file doesn't exist
- `ValueError` - If no KML file found in archive

---

#### `load_geopackage`

```python
def load_geopackage(
    gpkg_path: Union[str, Path],
    layer: Optional[str] = None
) -> gpd.GeoDataFrame
```

Load features from a GeoPackage file.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gpkg_path` | `Union[str, Path]` | Required | Path to GeoPackage file |
| `layer` | `Optional[str]` | `None` | Layer name (first layer if None) |

**Returns:** `gpd.GeoDataFrame` - Features from specified layer

---

#### `save_geopackage`

```python
def save_geopackage(
    gdf: gpd.GeoDataFrame,
    gpkg_path: Union[str, Path],
    layer: str = "features"
) -> Path
```

Save GeoDataFrame to GeoPackage format.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gdf` | `gpd.GeoDataFrame` | Required | GeoDataFrame to save |
| `gpkg_path` | `Union[str, Path]` | Required | Output path |
| `layer` | `str` | `"features"` | Layer name |

**Returns:** `Path` - Absolute path to saved file

---

## Module: `src.crs`

Coordinate Reference System utilities.

### Functions

#### `ensure_crs`

```python
def ensure_crs(
    gdf: gpd.GeoDataFrame,
    target_epsg: int = 9377,
    assume_input_epsg: int = 4326
) -> gpd.GeoDataFrame
```

Validate and transform GeoDataFrame to target CRS.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gdf` | `gpd.GeoDataFrame` | Required | Input GeoDataFrame |
| `target_epsg` | `int` | `9377` | Target EPSG code |
| `assume_input_epsg` | `int` | `4326` | EPSG to assume if input has no CRS |

**Returns:** `gpd.GeoDataFrame` - GeoDataFrame in target CRS

**Behavior:**
1. If GeoDataFrame has no CRS, assumes `assume_input_epsg`
2. If CRS differs from target, transforms coordinates
3. If already in target CRS, returns unchanged

**Example:**
```python
gdf = load_geodata("data.kmz")         # Typically EPSG:4326
gdf = ensure_crs(gdf, target_epsg=9377)  # Transform to meters
```

---

#### `reproject`

```python
def reproject(
    gdf: gpd.GeoDataFrame,
    target_epsg: int
) -> gpd.GeoDataFrame
```

Reproject GeoDataFrame to specified CRS.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gdf` | `gpd.GeoDataFrame` | Required | Input with valid CRS |
| `target_epsg` | `int` | Required | Target EPSG code |

**Returns:** `gpd.GeoDataFrame` - Reprojected GeoDataFrame

**Raises:** `ValueError` - If input has no CRS

---

#### `validate_projected_crs`

```python
def validate_projected_crs(
    gdf: gpd.GeoDataFrame
) -> bool
```

Check if GeoDataFrame is in a projected (metric) CRS.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `gdf` | `gpd.GeoDataFrame` | GeoDataFrame to validate |

**Returns:** `bool` - True if CRS is projected (meters), False if geographic

---

#### `get_crs_info`

```python
def get_crs_info(epsg: int) -> dict
```

Get human-readable CRS information.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `epsg` | `int` | EPSG code |

**Returns:** `dict` with keys: `epsg`, `name`, `units`

---

## Module: `src.geometry`

Geometry manipulation utilities.

### Functions

#### `to_single_line`

```python
def to_single_line(
    geom: Union[LineString, MultiLineString]
) -> LineString
```

Convert geometry to a single LineString.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `geom` | `Union[LineString, MultiLineString]` | Input geometry |

**Returns:** `LineString` - Single continuous line

**Raises:** `TypeError` - If geometry is not a line type

---

#### `extract_single_line`

```python
def extract_single_line(
    gdf: gpd.GeoDataFrame
) -> LineString
```

Extract corridor axis as a single LineString from GeoDataFrame.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `gdf` | `gpd.GeoDataFrame` | GeoDataFrame containing corridor axis |

**Returns:** `LineString` - Corridor axis as single line

**Raises:**
- `IndexError` - If GeoDataFrame is empty
- `TypeError` - If first geometry is not a line type

---

#### `get_centroids`

```python
def get_centroids(
    gdf: gpd.GeoDataFrame
) -> gpd.GeoDataFrame
```

Replace geometries with their centroids, preserving originals.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `gdf` | `gpd.GeoDataFrame` | Input with any geometry type |

**Returns:** `gpd.GeoDataFrame` with:
- `geometry`: Centroid points
- `geom_ori`: Original geometries (new column)

---

#### `project_point_to_line`

```python
def project_point_to_line(
    point: Point,
    line: LineString
) -> Tuple[Point, float]
```

Project a point onto a line, finding the nearest point.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `point` | `Point` | Point to project |
| `line` | `LineString` | Reference line |

**Returns:** `Tuple[Point, float]`:
- `Point`: Projected point on the line
- `float`: Distance along line from start (meters)

---

#### `perpendicular_distance`

```python
def perpendicular_distance(
    point: Point,
    line: LineString
) -> float
```

Calculate perpendicular (shortest) distance from point to line.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `point` | `Point` | Point to measure from |
| `line` | `LineString` | Reference line |

**Returns:** `float` - Shortest distance in meters (always positive)

---

## Module: `src.chainage`

Chainage (abscisas) calculations.

### Functions

#### `format_chainage`

```python
def format_chainage(
    distance_m: float,
    template: str = "K{km}+{rest:03d}"
) -> str
```

Format distance as K+format chainage label.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `distance_m` | `float` | Required | Distance in meters |
| `template` | `str` | `"K{km}+{rest:03d}"` | Format template |

**Returns:** `str` - Formatted label (e.g., "K5+250")

**Examples:**
```python
format_chainage(0)      # "K0+000"
format_chainage(5250)   # "K5+250"
format_chainage(11795)  # "K11+795"
```

---

#### `parse_chainage`

```python
def parse_chainage(label: str) -> float
```

Parse K+format chainage label back to meters.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `label` | `str` | Chainage string (e.g., "K5+250") |

**Returns:** `float` - Distance in meters

**Raises:** `ValueError` - If label format is invalid

**Examples:**
```python
parse_chainage("K5+250")   # 5250.0
parse_chainage("K0+000")   # 0.0
```

---

#### `chainage`

```python
def chainage(
    line: LineString,
    point: Point
) -> Tuple[float, str]
```

Calculate chainage (distance along axis) for a point.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `line` | `LineString` | Corridor axis |
| `point` | `Point` | Point to calculate chainage for |

**Returns:** `Tuple[float, str]`:
- `float`: Distance in meters from line start
- `str`: Formatted K+format label

---

#### `generate_chainage_points`

```python
def generate_chainage_points(
    line: LineString,
    interval_m: float = 500,
    start_m: float = 0
) -> List[Tuple[Point, float, str]]
```

Generate chainage marker points at regular intervals.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `line` | `LineString` | Required | Corridor axis |
| `interval_m` | `float` | `500` | Distance between markers |
| `start_m` | `float` | `0` | Starting chainage offset |

**Returns:** `List[Tuple[Point, float, str]]` - List of (point, distance, label)

---

#### `chainage_points_to_gdf`

```python
def chainage_points_to_gdf(
    chainage_points: List[Tuple[Point, float, str]],
    crs: Union[str, int]
) -> gpd.GeoDataFrame
```

Convert chainage marker list to GeoDataFrame.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `chainage_points` | `List[Tuple]` | Output from generate_chainage_points() |
| `crs` | `Union[str, int]` | Coordinate reference system |

**Returns:** `gpd.GeoDataFrame` with columns: `abscisa_m`, `abscisa_lbl`, `geometry`

---

## Module: `src.annotate`

Feature annotation and projection to corridor axis.

### Functions

#### `annotate_to_axis`

```python
def annotate_to_axis(
    gdf_points: gpd.GeoDataFrame,
    axis_line: LineString,
    name_field: str = "Name",
    crs_epsg: int = 9377
) -> gpd.GeoDataFrame
```

Project features to corridor axis and calculate chainage/offset.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gdf_points` | `gpd.GeoDataFrame` | Required | Point features to annotate |
| `axis_line` | `LineString` | Required | Corridor axis |
| `name_field` | `str` | `"Name"` | Column name for identifiers |
| `crs_epsg` | `int` | `9377` | Output CRS EPSG code |

**Returns:** `gpd.GeoDataFrame` with columns:

| Column | Type | Description |
|--------|------|-------------|
| `nombre` | `str` | Feature name/identifier |
| `dist_m` | `float` | Perpendicular offset (meters) |
| `abscisa_m` | `float` | Distance along axis (meters) |
| `abscisa_lbl` | `str` | K+format chainage label |
| `x`, `y` | `float` | Original coordinates |
| `x_axis`, `y_axis` | `float` | Projected point on axis |
| `geometry` | `Point` | Original point geometry |
| `geometry_axis` | `Point` | Projected point on axis |

---

#### `filter_by_radius`

```python
def filter_by_radius(
    gdf: gpd.GeoDataFrame,
    radius_m: float,
    distance_col: str = "dist_m"
) -> gpd.GeoDataFrame
```

Filter annotated features by distance from axis.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gdf` | `gpd.GeoDataFrame` | Required | Annotated GeoDataFrame |
| `radius_m` | `float` | Required | Maximum distance in meters |
| `distance_col` | `str` | `"dist_m"` | Column with offset values |

**Returns:** `gpd.GeoDataFrame` - Filtered copy with nearby features

---

#### `sort_by_chainage`

```python
def sort_by_chainage(
    gdf: gpd.GeoDataFrame,
    chainage_col: str = "abscisa_m"
) -> gpd.GeoDataFrame
```

Sort annotated features by chainage (distance along axis).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gdf` | `gpd.GeoDataFrame` | Required | Annotated GeoDataFrame |
| `chainage_col` | `str` | `"abscisa_m"` | Column with chainage values |

**Returns:** `gpd.GeoDataFrame` - Sorted copy (ascending chainage)

---

## Module: `src.geology`

Geotechnical data processing and SUCS classification.

### Constants

#### `SUCS_CODES`

```python
SUCS_CODES = {
    "GW": "Grava bien gradada",
    "GP": "Grava mal gradada",
    "GM": "Grava limosa",
    "GC": "Grava arcillosa",
    "SW": "Arena bien gradada",
    "SP": "Arena mal gradada",
    "SM": "Arena limosa",
    "SC": "Arena arcillosa",
    "ML": "Limo de baja plasticidad",
    "CL": "Arcilla de baja plasticidad",
    "OL": "Suelo orgánico de baja plasticidad",
    "MH": "Limo de alta plasticidad",
    "CH": "Arcilla de alta plasticidad",
    "OH": "Suelo orgánico de alta plasticidad",
    "PT": "Turba",
}
```

### Functions

#### `load_boreholes_csv`

```python
def load_boreholes_csv(
    csv_path: str | Path,
    x_col: str = "X",
    y_col: str = "Y",
    id_col: str = "id",
    crs_epsg: int = 9377
) -> gpd.GeoDataFrame
```

Load borehole data from CSV with coordinates.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `csv_path` | `str \| Path` | Required | Path to CSV file |
| `x_col` | `str` | `"X"` | X coordinate column |
| `y_col` | `str` | `"Y"` | Y coordinate column |
| `id_col` | `str` | `"id"` | Borehole ID column |
| `crs_epsg` | `int` | `9377` | CRS EPSG code |

**Returns:** `gpd.GeoDataFrame` - Borehole points

---

#### `parse_depth_range`

```python
def parse_depth_range(depth_str: str) -> tuple[float, float, float]
```

Parse depth range string to numeric values.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `depth_str` | `str` | Depth string (e.g., "1,00 - 1,50") |

**Returns:** `tuple[float, float, float]` - (min_depth, max_depth, mid_depth)

---

#### `get_sucs_description`

```python
def get_sucs_description(code: str) -> str
```

Get SUCS soil classification description.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | `str` | SUCS code (e.g., "CH", "SC") |

**Returns:** `str` - Description in Spanish

---

#### `summarize_by_sucs`

```python
def summarize_by_sucs(
    df: pd.DataFrame,
    sucs_col: str = "SUCS"
) -> pd.DataFrame
```

Summarize data by SUCS classification.

**Returns:** DataFrame with columns: `SUCS`, `Conteo`, `Porcentaje`, `Descripcion`

---

#### `summarize_spt_by_sucs`

```python
def summarize_spt_by_sucs(
    df: pd.DataFrame,
    sucs_col: str = "SUCS",
    spt_col: str = "N_SPT"
) -> pd.DataFrame
```

Summarize SPT N-values by SUCS classification.

**Returns:** DataFrame with columns: `SUCS`, `n`, `N_SPT_medio`, `N_SPT_std`, `N_SPT_min`, `N_SPT_max`, `Descripcion`

---

#### `assign_unique_ids`

```python
def assign_unique_ids(
    df: pd.DataFrame,
    id_col: str = "id",
    marker: str = "S1"
) -> pd.DataFrame
```

Assign continuous unique IDs detecting group restarts.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | `pd.DataFrame` | Required | DataFrame with ID column |
| `id_col` | `str` | `"id"` | ID column name |
| `marker` | `str` | `"S1"` | Marker indicating group restart |

**Returns:** DataFrame with `grupo` and `id_unico` columns added

---

## Module: `src.outputs_dxf`

DXF (CAD) export functionality.

### Functions

#### `export_axis_dxf`

```python
def export_axis_dxf(
    axis_line: LineString,
    output_path: str | Path,
    layer_name: str = "EJE",
    crs_epsg: int = 9377
) -> None
```

Export corridor axis to DXF.

---

#### `export_points_dxf`

```python
def export_points_dxf(
    gdf: gpd.GeoDataFrame,
    output_path: str | Path,
    layer_name: str = "POINTS",
    geometry_col: str = "geometry"
) -> None
```

Export point features to DXF.

---

#### `export_polygons_dxf`

```python
def export_polygons_dxf(
    gdf: gpd.GeoDataFrame,
    output_path: str | Path,
    layer_name: str = "POLYGONS",
    geometry_col: Optional[str] = None
) -> None
```

Export polygon features to DXF.

---

#### `export_corridor_dxf`

```python
def export_corridor_dxf(
    output_dir: str | Path,
    tramo: str,
    axis_line: LineString,
    sources_gdf: Optional[gpd.GeoDataFrame] = None,
    disposal_gdf: Optional[gpd.GeoDataFrame] = None,
    crs_epsg: int = 9377
) -> dict[str, Path]
```

Export complete corridor to multiple DXF files.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_dir` | `str \| Path` | Required | Output directory |
| `tramo` | `str` | Required | Corridor section identifier |
| `axis_line` | `LineString` | Required | Corridor centerline |
| `sources_gdf` | `Optional[gpd.GeoDataFrame]` | `None` | Material sources |
| `disposal_gdf` | `Optional[gpd.GeoDataFrame]` | `None` | Disposal zones |
| `crs_epsg` | `int` | `9377` | CRS EPSG code |

**Returns:** `dict[str, Path]` - Mapping layer type to output path

---

## Module: `src.outputs_maps`

Cartographic map generation (PNG output).

### Functions

#### `create_corridor_map`

```python
def create_corridor_map(
    axis_gdf: gpd.GeoDataFrame,
    sources_gdf: Optional[gpd.GeoDataFrame] = None,
    disposal_gdf: Optional[gpd.GeoDataFrame] = None,
    sources_annotated: Optional[gpd.GeoDataFrame] = None,
    disposal_annotated: Optional[gpd.GeoDataFrame] = None,
    title: str = "Corridor Location Map",
    tramo: str = "tramo",
    calc_epsg: int = 9377,
    plot_epsg: int = 3857,
    figsize: tuple[int, int] = (10, 10),
    dpi: int = 300,
    add_basemap: bool = True,
    margin_m: float = 500,
    grid_interval_m: float = 5000
) -> tuple[plt.Figure, plt.Axes]
```

Create a publication-ready corridor map.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `axis_gdf` | `gpd.GeoDataFrame` | Required | Corridor axis |
| `sources_gdf` | `Optional[gpd.GeoDataFrame]` | `None` | Material sources |
| `disposal_gdf` | `Optional[gpd.GeoDataFrame]` | `None` | Disposal zones |
| `sources_annotated` | `Optional[gpd.GeoDataFrame]` | `None` | Annotated sources |
| `disposal_annotated` | `Optional[gpd.GeoDataFrame]` | `None` | Annotated disposal |
| `title` | `str` | `"Corridor Location Map"` | Map title |
| `tramo` | `str` | `"tramo"` | Section identifier |
| `calc_epsg` | `int` | `9377` | Calculation CRS |
| `plot_epsg` | `int` | `3857` | Display CRS |
| `figsize` | `tuple[int, int]` | `(10, 10)` | Figure size in inches |
| `dpi` | `int` | `300` | Resolution |
| `add_basemap` | `bool` | `True` | Add OpenStreetMap basemap |
| `margin_m` | `float` | `500` | Margin around features |
| `grid_interval_m` | `float` | `5000` | Grid interval |

**Returns:** `tuple[plt.Figure, plt.Axes]` - Matplotlib figure and axes

---

#### `save_corridor_map`

```python
def save_corridor_map(
    fig: plt.Figure,
    output_path: str | Path,
    dpi: int = 300
) -> None
```

Save corridor map to PNG file.

---

## Module: `src.outputs_tables`

CSV and tabular output generation.

### Functions

#### `export_summary_csv`

```python
def export_summary_csv(
    gdf: gpd.GeoDataFrame,
    output_path: str | Path,
    drop_geometry_axis: bool = True
) -> None
```

Export annotated GeoDataFrame to CSV summary.

---

#### `export_geopackage`

```python
def export_geopackage(
    gdf: gpd.GeoDataFrame,
    output_path: str | Path,
    layer_name: str = "features"
) -> None
```

Export GeoDataFrame to GeoPackage.

---

#### `create_chainage_table`

```python
def create_chainage_table(
    chainage_points: list[tuple],
    crs_epsg: int
) -> pd.DataFrame
```

Create summary table of chainage points.

**Returns:** DataFrame with columns: `abscisa`, `distancia_m`, `x`, `y`, `crs`

---

## CLI Reference

### Commands

```bash
# Full pipeline
vv run --tramo ID --axis FILE --sources FILE --disposal FILE --out DIR

# Generate chainage markers
vv chainage --axis FILE --interval 500 --out FILE.csv

# Export DXF only
vv export-dxf --tramo ID --axis FILE --sources FILE --out DIR

# Show corridor info
vv info --axis FILE

# Show version
vv version
```

### Options

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--tramo` | `-t` | `str` | Corridor section identifier |
| `--axis` | `-a` | `Path` | Corridor axis file |
| `--sources` | `-s` | `Path` | Material sources file |
| `--disposal` | `-d` | `Path` | Disposal zones file |
| `--out` | `-o` | `Path` | Output directory |
| `--radius` | `-r` | `float` | Search radius (meters) |
| `--interval` | `-i` | `int` | Chainage interval (meters) |
| `--dpi` | | `int` | PNG resolution |
