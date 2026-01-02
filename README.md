# Vías Verdes

**Geospatial analysis and cartographic mapping for linear infrastructure corridors**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A reproducible geospatial pipeline for infrastructure corridor analysis. Transforms raw survey data (KMZ, GeoPackage) into engineering deliverables: chainage markers, feature annotations, cartographic maps (300dpi), CAD files (DXF), and summary tables.

---

## Overview

Infrastructure projects (roads, railways, pipelines) require precise linear referencing along a corridor axis. **Vías Verdes** automates the standard engineering workflow:

1. **Load** corridor data from KMZ/GeoPackage
2. **Transform** to projected CRS (EPSG:9377 MAGNA-SIRGAS for Colombia)
3. **Generate** chainage markers at regular intervals (K+format)
4. **Project** features (sources, disposal sites, boreholes) onto the axis
5. **Calculate** perpendicular offsets and distances
6. **Export** to PNG maps, DXF CAD files, and CSV tables

### Key Concepts

| Term | Description |
|------|-------------|
| **Chainage** (Abscisas) | Distance along corridor axis. Format: `K5+250` = 5 km + 250 m = 5,250 m |
| **Offset** | Perpendicular distance from feature to axis |
| **Projection** | Finding the nearest point on the axis for a given feature |

---

## Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/vias-verdes.git
cd vias-verdes

# Create environment (recommended)
conda create -n geo_env python=3.10 -y
conda activate geo_env

# Install package
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

### Requirements

- Python 3.10+
- GeoPandas, Shapely, Fiona
- Matplotlib (maps), ezdxf (CAD)
- Typer (CLI)

---

## Quick Start

```bash
# Generate synthetic demo data
python examples/generate_demo_data.py

# Run complete pipeline
vv run --tramo demo \
    --axis examples/demo_data/demo_axis.gpkg \
    --sources examples/demo_data/demo_sources.gpkg \
    --disposal examples/demo_data/demo_disposal.gpkg \
    --out outputs/

# Or use Makefile
make demo-data && make demo
```

### CLI Commands

```bash
# Full pipeline (map + DXF + CSV)
vv run --tramo T01 --axis corridor.gpkg --sources sources.gpkg

# Generate chainage markers
vv chainage --axis corridor.gpkg --interval 500 --out markers.csv

# Export to AutoCAD DXF
vv export-dxf --tramo T01 --axis corridor.gpkg --out exports/

# Display corridor info
vv info --axis corridor.gpkg
```

---

## Python API

```python
from src.io_kmz import load_geodata
from src.crs import ensure_crs
from src.geometry import extract_single_line
from src.chainage import generate_chainage_points, format_chainage
from src.annotate import annotate_to_axis, filter_by_radius, sort_by_chainage

# Load and transform corridor axis
axis_gdf = load_geodata("corridor.gpkg")
axis_gdf = ensure_crs(axis_gdf, target_epsg=9377)  # MAGNA-SIRGAS Colombia
axis_line = extract_single_line(axis_gdf)

print(f"Corridor length: {axis_line.length / 1000:.2f} km")

# Generate chainage markers every 500m
markers = generate_chainage_points(axis_line, interval_m=500)
for point, dist_m, label in markers[:5]:
    print(f"  {label}: ({point.x:.0f}, {point.y:.0f})")

# Annotate features to corridor axis
features = load_geodata("sources.gpkg")
features = ensure_crs(features, target_epsg=9377)

annotated = annotate_to_axis(features, axis_line, name_field="Name")
annotated = filter_by_radius(annotated, radius_m=15000)  # Within 15km
annotated = sort_by_chainage(annotated)

print(annotated[["nombre", "abscisa_lbl", "dist_m"]].to_string())
```

### Output Columns

The `annotate_to_axis()` function returns a GeoDataFrame with:

| Column | Type | Description |
|--------|------|-------------|
| `nombre` | str | Feature name/identifier |
| `abscisa_m` | float | Distance along axis (meters) |
| `abscisa_lbl` | str | K+format chainage label |
| `dist_m` | float | Perpendicular offset from axis (meters) |
| `x`, `y` | float | Original feature coordinates |
| `x_axis`, `y_axis` | float | Projected point on axis |

---

## Project Structure

```
vias-verdes/
├── src/                        # Core library
│   ├── io_kmz.py              # load_geodata(), load_kmz(), save_geopackage()
│   ├── crs.py                 # ensure_crs(), reproject(), validate_projected_crs()
│   ├── geometry.py            # extract_single_line(), get_centroids(), project_point_to_line()
│   ├── chainage.py            # format_chainage(), parse_chainage(), generate_chainage_points()
│   ├── annotate.py            # annotate_to_axis(), filter_by_radius(), sort_by_chainage()
│   ├── geology.py             # Borehole data & SUCS classification
│   ├── outputs_maps.py        # create_corridor_map(), save_corridor_map()
│   ├── outputs_dxf.py         # export_corridor_dxf()
│   ├── outputs_tables.py      # export_summary_csv()
│   └── config.py              # Pydantic configuration models
├── cli/main.py                # Typer CLI application
├── examples/
│   ├── generate_demo_data.py  # Synthetic data generator
│   └── demo_data/             # Generated demo files
├── tests/                     # Pytest test suite
├── docs/                      # Documentation (EN/ES)
└── notebooks/                 # Research notebooks
```

---

## Coordinate Reference Systems

All distance calculations require projected coordinates (meters). The pipeline handles CRS transformations automatically:

| Stage | CRS | EPSG | Description |
|-------|-----|------|-------------|
| **Input** | WGS84 | 4326 | GPS/KML data (degrees) |
| **Calculation** | MAGNA-SIRGAS | 9377 | Colombia national grid (meters) |
| **Display** | Web Mercator | 3857 | Basemap overlay |

```python
from src.crs import ensure_crs, validate_projected_crs

gdf = load_geodata("data.kmz")           # Typically EPSG:4326
gdf = ensure_crs(gdf, target_epsg=9377)  # Transform to meters

assert validate_projected_crs(gdf), "Must be projected CRS for distance calculations"
```

---

## Output Files

```
outputs/salidas_T01/
├── plano_localizacion_T01.png      # 300dpi cartographic map
├── EJE_T01.dxf                     # Corridor axis (CAD)
├── FUENTES.dxf                     # Material sources (CAD)
├── ZONAS_DISPOSICION.dxf           # Disposal zones (CAD)
├── chainage_markers.gpkg           # K+format markers
├── fuentes_resumen.csv             # Sources with chainage/offset
└── dispos_resumen.csv              # Disposal zones summary
```

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run specific test class
pytest tests/test_core.py::TestChainage -v

# Lint and format
make lint
make format

# Full check (lint + test + typecheck)
make check
```

### Test Coverage

The test suite covers all core modules:

- `TestChainage`: K+format formatting, parsing, marker generation
- `TestAnnotate`: Feature projection, offset calculation, filtering
- `TestCRS`: CRS transformation, validation
- `TestGeometry`: Line extraction, centroids, point projection
- `TestIntegration`: End-to-end workflow tests

---

## Documentation

Detailed documentation available in [`docs/`](docs/):

- **English**: [`docs/en/`](docs/en/)
  - [Executive Summary](docs/en/executive_summary.md)
  - [Technical Report](docs/en/technical_report.md)
  - [Pipeline Explained](docs/en/pipeline_explained.md)
  - [Mathematical Formulas](docs/en/mathematical_formulas.md)

- **Español**: [`docs/es/`](docs/es/)
  - [Resumen Ejecutivo](docs/es/executive_summary.md)
  - [Informe Técnico](docs/es/technical_report.md)
  - [Pipeline Explicado](docs/es/pipeline_explained.md)
  - [Fórmulas Matemáticas](docs/es/mathematical_formulas.md)

---

## Use Cases

This toolkit was developed for Colombian infrastructure corridor projects ("Vías Verdes") and is suitable for:

- **Road/Railway Design**: Linear referencing, chainage markers, alignment analysis
- **Pipeline Routing**: Feature proximity analysis, right-of-way mapping
- **Environmental Studies**: Distance calculations to sensitive areas
- **Geotechnical Surveys**: Borehole location and SPT data management
- **Construction Planning**: Material source and disposal zone mapping

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Author

Developed as part of infrastructure consulting work for Colombian corridor projects.

For questions or contributions, please open an issue or pull request.
