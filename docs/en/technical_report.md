# Technical Report

## Vías Verdes: Corridor Cartography Engine

**Version**: 0.1.0
**Date**: 2024
**Classification**: Open Source / Portfolio Project

---

## 1. Introduction

### 1.1 Purpose

This document provides comprehensive technical documentation for the Vías Verdes corridor cartography engine. It covers system architecture, algorithms, data models, and implementation details.

### 1.2 Scope

The system processes linear infrastructure corridors to produce:
- Chainage (distance along axis) calculations
- Feature projection to corridor axis
- CAD-compatible deliverables (DXF)
- Cartographic maps (300dpi PNG)
- Tabular summaries (CSV)

### 1.3 Background

Developed for Colombian infrastructure corridor projects ("Vías Verdes"), the engine addresses the need for automated, reproducible geospatial processing in civil engineering workflows.

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLI LAYER                                  │
│  cli/main.py - Typer commands: run, chainage, export-dxf, info     │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CORE LIBRARY                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │   io     │  │   crs    │  │ geometry │  │  config  │            │
│  │          │  │          │  │          │  │          │            │
│  │ read/    │  │ ensure/  │  │ extract/ │  │ Pydantic │            │
│  │ write    │  │ reproject│  │ centroid │  │ models   │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                          │
│  │ chainage │  │projection│  │ geotech  │                          │
│  │          │  │          │  │          │                          │
│  │ K+format │  │ project  │  │ SUCS/SPT │                          │
│  │ markers  │  │ to axis  │  │ analysis │                          │
│  └──────────┘  └──────────┘  └──────────┘                          │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     export/                                  │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                      │   │
│  │  │   dxf   │  │  maps   │  │ tables  │                      │   │
│  │  │ CAD out │  │ PNG out │  │ CSV out │                      │   │
│  │  └─────────┘  └─────────┘  └─────────┘                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL DEPENDENCIES                           │
│  GeoPandas │ Shapely │ Fiona │ Matplotlib │ Contextily │ Typer     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `src.io_kmz` | Multi-format geospatial I/O (KMZ, GPKG, GeoJSON, SHP) |
| `src.crs` | CRS validation, transformation, metadata |
| `src.geometry` | Line merging, centroid extraction, projection |
| `src.chainage` | K+format chainage, marker generation |
| `src.annotate` | Feature-to-axis projection, offset calculation |
| `src.geology` | SUCS classification, SPT analysis, borehole integration |
| `src.outputs_dxf` | DXF/CAD file generation |
| `src.outputs_maps` | Cartographic PNG generation |
| `src.outputs_tables` | CSV summary export |
| `src.config` | Pydantic configuration models |

### 2.3 Data Flow

```
Input Files                    Processing                      Outputs
───────────                    ──────────                      ───────

corridor.gpkg ──┐
                │
                ▼
            ┌───────────┐
            │ io.read   │
            │ geodata() │
            └─────┬─────┘
                  │
                  ▼
            ┌───────────┐
            │crs.ensure │
            │  _crs()   │
            └─────┬─────┘
                  │
                  ▼
            ┌───────────┐       ┌─────────────┐
            │ geometry. │──────▶│ chainage.   │──▶ markers[]
            │ extract   │       │ generate_   │
            │ _single   │       │ points()    │
            │ _line()   │       └─────────────┘
            └─────┬─────┘
                  │
features.gpkg ────┤
                  │
                  ▼
            ┌───────────┐
            │projection.│
            │ project_  │
            │ to_axis() │
            └─────┬─────┘
                  │
                  ├──────────────────────────────┐
                  │                              │
                  ▼                              ▼
            ┌───────────┐                  ┌───────────┐
            │ export.   │                  │ export.   │
            │ dxf       │                  │ maps      │
            └─────┬─────┘                  └─────┬─────┘
                  │                              │
                  ▼                              ▼
            *.dxf files                    *.png maps
```

---

## 3. Data Models

### 3.1 Core Types

```python
# Corridor axis
axis: shapely.LineString  # In EPSG:9377 (meters)

# Feature collection
features: geopandas.GeoDataFrame
# Required columns: geometry, Name (or configurable)
# CRS: Any (transformed to calculation CRS)

# Chainage marker
Marker = tuple[shapely.Point, float, str]
# (point_on_axis, distance_m, label)
# Example: (Point(1005000, 1003000), 5000, "K5+000")
```

### 3.2 Projection Result

```python
@dataclass
class ProjectionResult:
    name: str               # Feature identifier
    chainage_m: float       # Distance along axis (meters)
    chainage_label: str     # K+format label
    offset_m: float         # Perpendicular distance (meters)
    side: Literal["L", "R"] # Left or right of axis

    # Coordinates
    x: float               # Original X
    y: float               # Original Y
    x_axis: float          # Projection X on axis
    y_axis: float          # Projection Y on axis
```

### 3.3 Configuration Models

```python
class CRSConfig(BaseModel):
    calc_epsg: int = 9377   # Calculation CRS
    plot_epsg: int = 3857   # Display CRS
    input_epsg: int = 4326  # Default input CRS

class ChainageConfig(BaseModel):
    interval_m: int = 500   # Marker spacing
    format_template: str = "K{km}+{rest:03d}"

class CorridorConfig(BaseModel):
    tramo: str              # Corridor identifier
    axis_kmz: Path          # Axis file path
    sources_kmz: Path = None
    disposal_kmz: Path = None
    crs: CRSConfig = CRSConfig()
    chainage: ChainageConfig = ChainageConfig()
```

---

## 4. Algorithms

### 4.1 Chainage Calculation

**Input**: LineString `L`, Point `Q`
**Output**: (distance_m, label)

```
1. Project Q onto L:
   Q' = nearest_point_on_line(L, Q)

2. Calculate distance along L from origin to Q':
   d = line_distance_to_point(L, Q')

3. Format as K+:
   km = floor(d / 1000)
   rest = d mod 1000
   label = f"K{km}+{rest:03d}"

4. Return (d, label)
```

**Complexity**: O(n) where n = number of line segments

### 4.2 Feature Projection with Side Detection

**Input**: Point `Q`, LineString `L`
**Output**: ProjectionResult

```
1. Find projection point:
   Q' = L.interpolate(L.project(Q))

2. Calculate offset:
   offset = distance(Q, Q')

3. Determine side:
   a. Get axis direction at Q':
      t = L.project(Q')
      P1 = L.interpolate(max(0, t - 1))
      P2 = L.interpolate(min(L.length, t + 1))
      v = (P2.x - P1.x, P2.y - P1.y)

   b. Get vector from Q' to Q:
      u = (Q.x - Q'.x, Q.y - Q'.y)

   c. Cross product:
      cross = v.x * u.y - v.y * u.x

   d. Side:
      if cross > 0: side = "L"
      else: side = "R"

4. Calculate chainage:
   chainage_m, chainage_label = chainage(L, Q')

5. Return ProjectionResult(...)
```

### 4.3 Chainage Point Generation

**Input**: LineString `L`, interval `Δ`
**Output**: List[Marker]

```
markers = []
d = 0
while d <= L.length:
    P = L.interpolate(d)
    label = format_chainage(d)
    markers.append((P, d, label))
    d += Δ
return markers
```

---

## 5. File Formats

### 5.1 Input Formats

| Format | Driver | Notes |
|--------|--------|-------|
| KMZ | KML (extracted) | Compressed KML archive |
| GeoPackage | GPKG | Recommended, supports layers |
| GeoJSON | GeoJSON | UTF-8, web-friendly |
| Shapefile | ESRI Shapefile | Legacy, avoid for new projects |
| KML | KML | XML-based |

### 5.2 Output Formats

**DXF (CAD)**:
- AutoCAD DXF R12/R2000 format
- UTF-8 encoding for Spanish characters
- Organized by layers (EJE_, CHAINAGE_, feature types)

**PNG (Maps)**:
- 300 DPI resolution (configurable)
- RGB color space
- Includes: basemap, features, annotations, legend, scale bar

**CSV (Tables)**:
- UTF-8 encoding
- Comma-separated
- Headers: name, chainage_label, chainage_m, offset_m, side, x, y

---

## 6. Coordinate Reference Systems

### 6.1 CRS Strategy

```
Input (WGS84)          Calculation            Display
EPSG:4326       →      EPSG:9377       →      EPSG:3857
Geographic            MAGNA-SIRGAS           Web Mercator
                      (meters)
```

### 6.2 MAGNA-SIRGAS Colombia (EPSG:9377)

**Parameters**:
- Projection: Transverse Mercator
- Latitude of origin: 4°N
- Central meridian: -73°
- Scale factor: 0.9992
- False easting: 5,000,000 m
- False northing: 2,000,000 m

**Accuracy**: Sub-meter for engineering applications

### 6.3 Transformation Handling

```python
def ensure_crs(gdf, target_epsg=9377, assume_input_epsg=4326):
    if gdf.crs is None:
        gdf = gdf.set_crs(assume_input_epsg)
    if gdf.crs.to_epsg() != target_epsg:
        return gdf.to_crs(epsg=target_epsg)
    return gdf
```

---

## 7. Geotechnical Module

### 7.1 SUCS Classification

Standard soil classification codes per ASTM D2487:

| Code | Description (EN) | Description (ES) |
|------|------------------|------------------|
| GW | Well-graded gravel | Grava bien gradada |
| GP | Poorly-graded gravel | Grava mal gradada |
| GM | Silty gravel | Grava limosa |
| GC | Clayey gravel | Grava arcillosa |
| SW | Well-graded sand | Arena bien gradada |
| SP | Poorly-graded sand | Arena mal gradada |
| SM | Silty sand | Arena limosa |
| SC | Clayey sand | Arena arcillosa |
| ML | Low-plasticity silt | Limo de baja plasticidad |
| CL | Low-plasticity clay | Arcilla de baja plasticidad |
| MH | High-plasticity silt | Limo de alta plasticidad |
| CH | High-plasticity clay | Arcilla de alta plasticidad |
| OL | Organic (low plasticity) | Suelo orgánico (baja) |
| OH | Organic (high plasticity) | Suelo orgánico (alta) |
| PT | Peat | Turba |

### 7.2 SPT Corrections

**Energy correction (N60)**:

$$N_{60} = N_{field} \times \frac{E_r}{60}$$

**Full correction**:

$$N_{60} = N_{field} \times C_E \times C_B \times C_R \times C_S$$

| Factor | Description | Typical Range |
|--------|-------------|---------------|
| $C_E$ | Energy ratio | 0.75 - 1.33 |
| $C_B$ | Borehole diameter | 1.0 |
| $C_R$ | Rod length | 0.75 - 1.0 |
| $C_S$ | Sampler type | 1.0 - 1.2 |

---

## 8. Performance Considerations

### 8.1 Benchmarks

| Operation | Typical Time | Notes |
|-----------|--------------|-------|
| Load 10 MB GPKG | < 1 s | |
| Chainage (1000 points) | < 0.5 s | |
| Projection (1000 features) | < 2 s | |
| DXF export | < 1 s | Per layer |
| Map generation | 5-10 s | With basemap |

### 8.2 Memory Usage

- GeoDataFrame: ~1 MB per 10,000 features
- Matplotlib figure: ~50 MB at 300 DPI
- Peak usage: < 500 MB for typical corridors

### 8.3 Optimization Strategies

1. **Spatial indexing**: Use `sindex` for filtering
2. **Chunked processing**: For very long corridors
3. **Basemap caching**: Contextily caches tiles locally

---

## 9. Testing Strategy

### 9.1 Test Categories

| Category | Coverage | Location |
|----------|----------|----------|
| Unit tests | Core functions | `tests/test_*.py` |
| Integration tests | Full pipeline | `tests/test_integration.py` |
| Fixtures | Synthetic data | `tests/conftest.py` |

### 9.2 Key Test Cases

**Chainage**:
- Format round-trip: `parse(format(x)) == x`
- Boundary cases: 0 m, 999 m, 1000 m
- Large values: > 100 km

**Projection**:
- Point on axis: offset = 0
- Point left of axis: side = "L"
- Point right of axis: side = "R"

**CRS**:
- Missing CRS handling
- Transform accuracy (< 1 m error)
- Round-trip: input → calc → input

### 9.3 Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Specific module
pytest tests/test_chainage.py -v

# Single test
pytest tests/test_chainage.py::TestChainage::test_format_basic -v
```

---

## 10. Deployment

### 10.1 Installation

```bash
# From source
git clone https://github.com/user/vias-verdes.git
cd vias-verdes
pip install -e ".[dev]"

# From PyPI (future)
pip install vias-verdes
```

### 10.2 Dependencies

**Required**:
```
geopandas>=0.14.0
shapely>=2.0.0
pandas>=2.0.0
matplotlib>=3.7.0
contextily>=1.4.0
fiona>=1.9.0
pydantic>=2.0.0
typer[all]>=0.9.0
```

**Development**:
```
pytest>=7.0.0
pytest-cov>=4.0.0
ruff>=0.1.0
mypy>=1.0.0
```

### 10.3 Environment

```bash
# Conda (recommended)
conda create -n vias_verdes python=3.11
conda activate vias_verdes
pip install -e ".[dev]"
```

---

## 11. Future Roadmap

### 11.1 Planned Features

| Priority | Feature | Status |
|----------|---------|--------|
| High | Interactive web map (Folium) | Planned |
| High | PDF report generation | Planned |
| Medium | QGIS plugin | Conceptual |
| Medium | 3D profile visualization | Conceptual |
| Low | Real-time collaboration | Future |

### 11.2 API Stability

- **Stable**: `chainage`, `projection`, `io` modules
- **Evolving**: `export.maps` styling options
- **Experimental**: `geotech` SPT correlations

---

## 12. References

1. Shapely User Manual (https://shapely.readthedocs.io/)
2. GeoPandas Documentation (https://geopandas.org/)
3. ASTM D2487 - Standard Practice for Classification of Soils (SUCS)
4. ASTM D1586 - Standard Test Method for SPT
5. IGAC - MAGNA-SIRGAS Documentation

---

## Appendix A: CLI Reference

```bash
# Run full pipeline
vv run --tramo ID --axis FILE --sources FILE --disposal FILE --out DIR

# Generate chainage table
vv chainage --axis FILE --interval 500 --out FILE.csv

# Export DXF only
vv export-dxf --tramo ID --axis FILE --sources FILE --out DIR

# Show corridor info
vv info --axis FILE

# Show version
vv version
```

## Appendix B: Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VIAS_VERDES_CRS` | 9377 | Default calculation CRS |
| `VIAS_VERDES_INTERVAL` | 500 | Default chainage interval |
| `VIAS_VERDES_DPI` | 300 | Default map resolution |
