# Architecture

## Data Flow Pipeline

```
INPUT                    PROCESSING                      OUTPUT
─────────────────────────────────────────────────────────────────

KMZ/GeoPackage    ──►  [io_kmz.load_kmz]
                              │
                              ▼
                       [crs.ensure_crs]
                       EPSG:4326 → EPSG:9377
                              │
                              ▼
                       [geometry.extract_single_line]
                       MultiLineString → LineString
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
     [chainage]         [annotate]         [geometry]
     Generate K+        Project to         Centroids,
     markers            axis, calc         distances
                        offset
            │                 │                 │
            └────────┬────────┴────────┬────────┘
                     │                 │
            ┌────────┴────────┐        │
            ▼                 ▼        ▼
     [outputs_maps]    [outputs_dxf]  [outputs_tables]
     PNG 300dpi        DXF CAD        CSV summaries
     cartographic      layers         GeoPackage
```

## Module Responsibilities

### Core Modules (`src/`)

| Module | Responsibility |
|--------|----------------|
| `io_kmz.py` | Load KMZ/KML/GeoPackage files |
| `crs.py` | CRS validation, transformation |
| `geometry.py` | Geometry manipulation (merge, project, centroid) |
| `chainage.py` | Distance calculations, K+format |
| `annotate.py` | Project features to axis, calculate offsets |
| `config.py` | Pydantic configuration models |

### Output Modules (`src/`)

| Module | Responsibility |
|--------|----------------|
| `outputs_maps.py` | Matplotlib cartographic maps |
| `outputs_dxf.py` | Fiona/GeoPandas DXF export |
| `outputs_tables.py` | CSV/GeoPackage tabular export |

### Optional Modules

| Module | Responsibility |
|--------|----------------|
| `geology.py` | Borehole loading, SUCS classification |

## Configuration

Configuration uses Pydantic models for validation:

```python
from src.config import CorridorConfig

config = CorridorConfig(
    tramo="tramo6",
    axis_kmz=Path("eje.kmz"),
    sources_kmz=Path("fuentes.kmz"),
    crs=CRSConfig(calc_epsg=9377, plot_epsg=3857),
    chainage=ChainageConfig(interval_m=500),
    filter=FilterConfig(radius_m=70000),
    output=OutputConfig(dpi=300)
)
```

## Key Algorithms

### Chainage Calculation

```
1. Project point P onto axis line L
2. Calculate distance along L from origin to projected point
3. Format as K{km}+{meters:03d}

Example: 5250m → K5+250
```

### Feature Annotation

```
1. For each feature point P:
   a. Find nearest point on axis (P_axis)
   b. Calculate perpendicular distance: d = P.distance(axis)
   c. Calculate chainage: s = axis.project(P_axis)
   d. Store: (name, d, s, K+format, coords)
```

### Cartographic Output

Map components (in order):
1. Base layer (OpenStreetMap via contextily)
2. Corridor axis (LineString)
3. Feature points/polygons
4. Reference lines (feature → axis projection)
5. Annotations (name, chainage, distance)
6. Legend
7. North arrow
8. Scale bar
9. Coordinate grid (5km intervals)
10. Neatline (border frame)
11. Footer (CRS info, date, source)

## CRS Strategy

| Stage | CRS | Reason |
|-------|-----|--------|
| Input | EPSG:4326 | KML/GPS standard |
| Calculation | EPSG:9377 | Metric, Colombia-accurate |
| Visualization | EPSG:3857 | Web Mercator for basemaps |
| Export (DXF) | EPSG:9377 | CAD needs metric coords |

## Error Handling

- `FileNotFoundError`: Missing input files
- `ValueError`: Invalid geometry, empty KMZ
- CRS validation: Auto-assign 4326 if None
- Geometry cleaning: MultiLineString → LineString

## Extension Points

### Adding New Output Formats

```python
# In src/outputs_xxx.py
def export_xxx(gdf: gpd.GeoDataFrame, path: Path) -> None:
    # Implement export logic
    pass
```

### Adding New Feature Types

```python
# In cli/main.py, add to run command:
boreholes: Optional[Path] = typer.Option(None, "--boreholes")

# Process in pipeline
if boreholes:
    bh_gdf = load_boreholes_csv(boreholes)
    bh_annotated = annotate_to_axis(bh_gdf, axis_line)
```
