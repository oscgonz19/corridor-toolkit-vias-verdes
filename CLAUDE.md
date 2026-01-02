# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Green Corridor Cartography Engine - Geospatial analysis and cartographic mapping system for Colombian infrastructure corridors ("Vías Verdes"). Reproducible pipeline for:
- Chainage (abscisas) calculations along linear axes
- Feature projection to corridor axis with perpendicular offsets
- Cartographic output (300dpi PNG maps)
- CAD export (DXF files)
- Tabular summaries (CSV)

## Commands

```bash
# Environment
conda activate geo_env

# Install package
pip install -e .
pip install -e ".[dev]"  # With dev dependencies

# Run tests
make test                                      # All tests
pytest tests/test_core.py -v                   # Single file
pytest tests/test_core.py::TestChainage -v     # Single class
pytest tests/test_core.py::TestChainage::test_format_chainage_basic -v  # Single test
make test-cov                                  # With coverage

# Linting
make lint     # Check with ruff
make format   # Auto-format
make check    # lint + test + typecheck

# Demo
make demo-data  # Generate synthetic data
make demo       # Full demo pipeline

# CLI commands
vv run --tramo demo --axis eje.gpkg --sources fuentes.gpkg --out outputs/
vv chainage --axis eje.gpkg --interval 500
vv export-dxf --tramo demo --axis eje.gpkg
vv info --axis eje.gpkg
```

## Architecture

### Module Structure

```
src/                        # Core library
├── io_kmz.py              # load_kmz(), load_geopackage()
├── crs.py                 # ensure_crs(), reproject()
├── geometry.py            # to_single_line(), get_centroids()
├── chainage.py            # format_chainage(), chainage(), generate_chainage_points()
├── annotate.py            # annotate_to_axis(), filter_by_radius()
├── geology.py             # load_boreholes_csv(), SUCS utilities
├── outputs_maps.py        # create_corridor_map(), save_corridor_map()
├── outputs_dxf.py         # export_corridor_dxf()
├── outputs_tables.py      # export_summary_csv()
└── config.py              # Pydantic models (CorridorConfig, CRSConfig, etc.)

cli/main.py                # Typer CLI (vv command)
```

### Data Flow

```
KMZ/GeoPackage → [io_kmz] → [crs.ensure_crs] → EPSG:9377
                                    ↓
├── [chainage] → K+format markers (K0+000, K0+500...)
├── [annotate_to_axis] → perpendicular distance + chainage per feature
└── Outputs:
    ├── [outputs_maps] → PNG 300dpi (basemap, grid, scale, north arrow)
    ├── [outputs_dxf] → DXF CAD layers
    └── [outputs_tables] → CSV summaries
```

### CRS

| EPSG | Usage |
|------|-------|
| 4326 | Input (WGS84/GPS) |
| 9377 | Calculations (MAGNA-SIRGAS Colombia) |
| 3857 | Display (Web Mercator for basemaps) |

## Key Functions

```python
from src.io_kmz import load_geodata  # Handles both KMZ and GeoPackage
from src.crs import ensure_crs
from src.geometry import to_single_line, extract_single_line, get_centroids
from src.chainage import format_chainage, chainage, generate_chainage_points
from src.annotate import annotate_to_axis, filter_by_radius

# Load and reproject data
gdf = load_geodata("file.kmz")  # or .gpkg
gdf = ensure_crs(gdf, target_epsg=9377)  # Always reproject to 9377 for calculations
axis_line = extract_single_line(gdf)  # Get single LineString from GeoDataFrame

# Chainage: 5250m → "K5+250"
format_chainage(5250)  # "K5+250"

# Generate chainage markers along axis
points = generate_chainage_points(axis_line, interval_m=500)
# Returns: [(Point, distance_m, label), ...]

# Project features to axis
annotated = annotate_to_axis(features_gdf, axis_line)
# Returns GeoDataFrame with: nombre, dist_m, abscisa_m, abscisa_lbl, x, y, x_axis, y_axis
annotated = filter_by_radius(annotated, radius_m=70000)  # Filter by perpendicular distance
```

## Naming Conventions

- Spanish terms: `sondeos` (boreholes), `fuentes` (sources), `dispos` (disposal), `abscisas` (chainage), `tramo` (section)
- Output dirs: `salidas_tramo[N]/`
- DXF layers: `EJE_TRAMO[N]`, `FUENTES`, `ZONAS_DISPOSICION`

## Testing

Test classes: `TestChainage`, `TestAnnotate`, `TestCRS`, `TestGeometry`

```bash
pytest tests/ -v                                   # All tests
pytest tests/test_core.py::TestChainage -v         # Chainage tests
pytest tests/test_core.py::TestAnnotate -v         # Annotation tests
pytest -k "test_format_chainage" -v                # By name pattern
```

## Legacy Notebooks

Research notebooks (kept for reference, not core):
- `mapas_vias_verdes.ipynb` - Original mapping workflow
- `geology.ipynb` - Geological analysis
- `tablas_limpias/transform.ipynb` - CSV transforms
- `vias_verdes_v2/scriptpng.ipynb` - PNG→DXF (CV)
