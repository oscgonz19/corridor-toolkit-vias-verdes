# Pipeline Explained

## Step-by-Step Guide to Corridor Cartography Processing

---

## Overview

The Vías Verdes pipeline transforms raw geospatial data into engineering deliverables through four main stages:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  INPUT   │ → │  PREPARE │ → │  PROCESS │ → │  EXPORT  │
│          │    │          │    │          │    │          │
│ KMZ/GPKG │    │ CRS/Geom │    │ Chainage │    │ DXF/PNG  │
│          │    │          │    │ Project  │    │ CSV      │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## Stage 1: Input

### Supported Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| KMZ | `.kmz` | Google Earth compressed KML |
| GeoPackage | `.gpkg` | OGC standard, recommended |
| GeoJSON | `.geojson` | Web-friendly JSON format |
| Shapefile | `.shp` | Legacy ESRI format |
| KML | `.kml` | Google Earth markup |

### Loading Data

```python
from src.io_kmz import load_geodata

# Automatic format detection
axis_gdf = load_geodata("corridor.kmz")
features_gdf = load_geodata("features.gpkg")
```

### Input Requirements

**Corridor Axis**:
- Single LineString or MultiLineString geometry
- Should represent the centerline of the corridor
- Direction matters: chainage increases along the line direction

**Features**:
- Point, LineString, or Polygon geometries
- Must have a `Name` field (or specify custom field)
- CRS: WGS84 (EPSG:4326) or projected

---

## Stage 2: Prepare

### CRS Validation and Transformation

All calculations require **projected coordinates** in meters. The pipeline:

1. **Detects** input CRS (or assumes WGS84 if missing)
2. **Transforms** to calculation CRS (default: EPSG:9377 MAGNA-SIRGAS)
3. **Validates** that units are meters

```python
from src.crs import ensure_crs

# Transform to MAGNA-SIRGAS Colombia
axis_gdf = ensure_crs(axis_gdf, target_epsg=9377)
features_gdf = ensure_crs(features_gdf, target_epsg=9377)
```

### CRS Configuration

| EPSG | Name | Usage |
|------|------|-------|
| 4326 | WGS84 | Input (GPS/KML default) |
| 9377 | MAGNA-SIRGAS Origin-National | Calculations (Colombia) |
| 3857 | Web Mercator | Map display with basemaps |

### Geometry Preparation

**Extract single LineString from axis**:

```python
from src.geometry import extract_single_line

axis_line = extract_single_line(axis_gdf)
# Handles MultiLineString by merging components
```

**Get centroids for polygon features**:

```python
from src.geometry import get_centroids

# For projecting polygon features, use their centroids
features_with_centroids = get_centroids(features_gdf)
```

---

## Stage 3: Process

### 3.1 Chainage Generation

Generate K+format markers at regular intervals along the axis:

```python
from src.chainage import generate_chainage_points

markers = generate_chainage_points(
    line=axis_line,
    interval_m=500,  # Every 500 meters
    start_m=0        # Starting chainage
)

# Returns: [(Point, distance_m, label), ...]
# Example: [(Point(...), 0, "K0+000"), (Point(...), 500, "K0+500"), ...]
```

**Chainage formatting**:

```python
from src.chainage import format_chainage, parse_chainage

format_chainage(5250)      # "K5+250"
format_chainage(11795)     # "K11+795"

parse_chainage("K5+250")   # 5250.0
```

### 3.2 Feature Projection

Project each feature to the corridor axis:

```python
from src.annotate import annotate_to_axis

annotated = annotate_to_axis(
    gdf_points=features_gdf,
    axis_line=axis_line,
    name_field="Name"
)
```

**Output columns**:

| Column | Type | Description |
|--------|------|-------------|
| `nombre` | str | Feature identifier |
| `abscisa_m` | float | Distance along axis (meters) |
| `abscisa_lbl` | str | K+format label |
| `dist_m` | float | Perpendicular distance (meters) |
| `x`, `y` | float | Original coordinates |
| `x_axis`, `y_axis` | float | Projection point on axis |
| `geometry` | Point | Original geometry |
| `geometry_axis` | Point | Projected point on axis |

### 3.3 Offset Filtering

Filter features by distance from axis:

```python
from src.annotate import filter_by_radius

# Keep only features within 10 km of axis
nearby = filter_by_radius(annotated, radius_m=10000)
```

### 3.4 Sort by Chainage

Sort features by distance along axis:

```python
from src.annotate import sort_by_chainage

sorted_features = sort_by_chainage(annotated)
```

---

## Stage 4: Export

### 4.1 DXF Export (CAD)

Export to AutoCAD-compatible DXF files:

```python
from src.outputs_dxf import export_corridor_dxf

export_corridor_dxf(
    output_dir="outputs/",
    tramo="DEMO",
    axis_line=axis_line,
    sources_gdf=sources_gdf,
    disposal_gdf=disposal_gdf
)
```

**Layer naming convention**:

| Layer | Content |
|-------|---------|
| `EJE_{ID}` | Corridor centerline |
| `CHAINAGE_{ID}` | K+ markers |
| `FUENTES` | Material sources |
| `ZONAS_DISPOSICION` | Disposal zones |

### 4.2 Map Export (PNG)

Generate publication-ready cartographic maps:

```python
from src.outputs_maps import create_corridor_map, save_corridor_map

fig, ax = create_corridor_map(
    axis_gdf=axis_gdf,
    features_gdf=features_gdf,
    title="Corridor Location Map",
    figsize=(12, 12)
)

save_corridor_map(fig, "outputs/corridor_map.png", dpi=300)
```

**Map elements**:
- OpenStreetMap basemap
- Corridor axis with styling
- Feature symbols by type
- Chainage labels at projection points
- Offset distances in annotations
- Scale bar and north arrow
- Coordinate grid
- Legend and metadata footer

### 4.3 Table Export (CSV)

Export summary tables:

```python
from src.outputs_tables import export_summary_csv

export_summary_csv(
    gdf=annotated,
    output_path="outputs/features_summary.csv"
)
```

**CSV columns**:
- `nombre`: Feature name
- `abscisa_lbl`: K+format position
- `abscisa_m`: Position in meters
- `dist_m`: Distance from axis
- `x`, `y`: Original coordinates

---

## Complete Pipeline Example

### CLI Usage

```bash
# Full pipeline with all outputs
vv run \
    --tramo DEMO \
    --axis corridor.gpkg \
    --sources sources.gpkg \
    --disposal disposal.gpkg \
    --radius 20000 \
    --interval 500 \
    --dpi 300 \
    --out outputs/
```

### Python Script

```python
#!/usr/bin/env python3
"""Complete corridor processing pipeline."""

from pathlib import Path
from src.io_kmz import load_geodata
from src.crs import ensure_crs
from src.geometry import extract_single_line, get_centroids
from src.chainage import generate_chainage_points
from src.annotate import annotate_to_axis, filter_by_radius, sort_by_chainage

# Configuration
CORRIDOR_ID = "DEMO"
OUTPUT_DIR = Path("outputs")
CHAINAGE_INTERVAL = 500
MAX_OFFSET = 20000

# 1. Load data
print("Loading data...")
axis_gdf = load_geodata("corridor.gpkg")
sources_gdf = load_geodata("sources.gpkg")
disposal_gdf = load_geodata("disposal.gpkg")

# 2. Prepare: CRS transformation
print("Transforming CRS...")
axis_gdf = ensure_crs(axis_gdf, target_epsg=9377)
sources_gdf = ensure_crs(sources_gdf, target_epsg=9377)
disposal_gdf = ensure_crs(disposal_gdf, target_epsg=9377)

# 3. Extract axis line
axis_line = extract_single_line(axis_gdf)
print(f"Corridor length: {axis_line.length/1000:.1f} km")

# 4. Generate chainage markers
markers = generate_chainage_points(axis_line, CHAINAGE_INTERVAL)
print(f"Generated {len(markers)} chainage markers")

# 5. Project features to axis
sources_centroids = get_centroids(sources_gdf)
disposal_centroids = get_centroids(disposal_gdf)

sources_annotated = annotate_to_axis(sources_centroids, axis_line, name_field="Name")
disposal_annotated = annotate_to_axis(disposal_centroids, axis_line, name_field="Name")

# 6. Filter by offset
sources_annotated = filter_by_radius(sources_annotated, radius_m=MAX_OFFSET)
disposal_annotated = filter_by_radius(disposal_annotated, radius_m=MAX_OFFSET)

# 7. Sort by chainage
sources_annotated = sort_by_chainage(sources_annotated)
disposal_annotated = sort_by_chainage(disposal_annotated)

print(f"Sources within range: {len(sources_annotated)}")
print(f"Disposal zones within range: {len(disposal_annotated)}")

# 8. Export results
print("Exporting...")
output_path = OUTPUT_DIR / f"salidas_{CORRIDOR_ID}"
output_path.mkdir(parents=True, exist_ok=True)

sources_annotated.to_csv(output_path / "fuentes_resumen.csv", index=False)
disposal_annotated.to_csv(output_path / "dispos_resumen.csv", index=False)

print(f"\nComplete! Outputs in: {output_path}")
```

---

## Pipeline Configuration

### Using Pydantic Models

```python
from src.config import CorridorConfig, CRSConfig, ChainageConfig

config = CorridorConfig(
    tramo="DEMO",
    axis_kmz=Path("corridor.gpkg"),
    sources_kmz=Path("sources.gpkg"),
    disposal_kmz=Path("disposal.gpkg"),
    crs=CRSConfig(
        calc_epsg=9377,
        plot_epsg=3857,
        input_epsg=4326
    ),
    chainage=ChainageConfig(
        interval_m=500,
        format_template="K{km}+{rest:03d}"
    )
)
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Empty output | No features within radius | Increase `--radius` parameter |
| CRS warning | Missing CRS in input | Specify `assume_input_epsg=4326` |
| DXF encoding error | Spanish characters | Ensure UTF-8 encoding |
| Map basemap missing | No internet / contextily | Set `add_basemap=False` |

### Debugging

```python
from src.crs import validate_projected_crs

# Check CRS
print(f"Axis CRS: {axis_gdf.crs}")
print(f"Features CRS: {features_gdf.crs}")

# Validate projected CRS
assert validate_projected_crs(axis_gdf), "Axis must be in projected CRS"

# Check geometry types
print(f"Axis geometry: {axis_gdf.geometry.iloc[0].geom_type}")

# Validate axis
print(f"Axis length: {axis_line.length} meters")
print(f"Axis is valid: {axis_line.is_valid}")
```
