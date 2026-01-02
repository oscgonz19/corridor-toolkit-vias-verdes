# Executive Summary

## Vías Verdes: Corridor Cartography Engine

**Engineering-grade deliverables for linear infrastructure projects**

---

## The Challenge

Linear infrastructure projects (highways, railways, pipelines) require precise spatial referencing along the corridor axis. Engineers and geologists need to:

- Reference features by **chainage** (distance along the corridor: K5+250 = 5.25 km from origin)
- Calculate **perpendicular offsets** from the corridor centerline
- Produce **CAD-compatible deliverables** (DXF) for design teams
- Generate **publication-ready maps** for reports and stakeholders
- Integrate **geotechnical data** (boreholes, soil classification) with spatial positions

Traditional workflows involve manual calculations in spreadsheets, disconnected GIS/CAD tools, and significant rework when alignments change.

---

## The Solution

**Vías Verdes** is a reproducible geospatial pipeline that automates corridor cartography:

```
Raw Data (KMZ/GPKG) → Chainage → Projection → Engineering Deliverables
```

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Chainage Automation** | K+format markers at configurable intervals (K0+000, K0+500...) |
| **Feature Projection** | Project any geometry to corridor axis with offset calculation |
| **Side Detection** | Automatic left/right (+L/+R) classification relative to axis direction |
| **CAD Export** | DXF files with proper layering for AutoCAD/Civil 3D |
| **Cartographic Maps** | 300dpi PNG with basemap, legend, scale bar, coordinate grid |
| **Geotechnical Module** | SUCS classification, SPT N-value analysis, borehole integration |

---

## Key Benefits

### For Engineering Teams
- **80% reduction** in manual chainage calculations
- **Consistent deliverables** across project phases
- **CAD-ready outputs** that integrate directly into design workflows

### For Project Managers
- **Reproducible pipeline** — regenerate all outputs when alignment changes
- **Audit trail** — version-controlled processing scripts
- **Standardized outputs** — uniform map styling and DXF layer conventions

### For Geoscientists
- **Integrated geotechnical data** — boreholes referenced by chainage
- **Soil classification summaries** — SUCS distribution along corridor
- **SPT analysis** — N-value statistics by soil type and depth

---

## Technical Highlights

- **CRS-aware**: Handles WGS84 input, projects to MAGNA-SIRGAS (EPSG:9377) for calculations
- **Multi-format I/O**: Reads KMZ, GeoPackage, GeoJSON, Shapefile
- **CLI + API**: Command-line interface for automation, Python API for notebooks
- **Extensible**: Pydantic configuration, modular architecture

---

## Target Applications

- Highway and railway corridor studies
- Pipeline route selection and engineering
- Transmission line surveys
- Environmental impact assessments along linear features
- Geotechnical site characterization for linear infrastructure

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Core | Python 3.10+, GeoPandas, Shapely |
| Mapping | Matplotlib, Contextily |
| CAD Export | Fiona (DXF driver) |
| CLI | Typer, Rich |
| Configuration | Pydantic |

---

## Quick Start

```bash
# Install
pip install -e .

# Generate demo data
make demo-data

# Run full pipeline
vv run --tramo DEMO --axis corridor.gpkg --sources features.gpkg --out outputs/
```

---

## About

Developed from real Colombian infrastructure corridor projects ("Vías Verdes"). The codebase has been anonymized and generalized for public use, demonstrating best practices in geospatial engineering automation.

**Author**: Geologist with expertise in geospatial AI and infrastructure risk assessment.
