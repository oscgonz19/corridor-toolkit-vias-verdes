# Documentation / Documentación

## Vías Verdes: Corridor Cartography Engine

---

## English Documentation

| Document | Description |
|----------|-------------|
| [Executive Summary](en/executive_summary.md) | High-level overview, key benefits, quick start |
| [Case Study](en/case_study.md) | Real-world application, before/after, lessons learned |
| [Pipeline Explained](en/pipeline_explained.md) | Step-by-step processing guide with code examples |
| [Mathematical Formulas](en/mathematical_formulas.md) | Geometric foundations, algorithms, equations |
| [Technical Report](en/technical_report.md) | Full system architecture, data models |
| [**API Reference**](en/api_reference.md) | Complete function/class documentation (SOLID) |

---

## Documentación en Español

| Documento | Descripción |
|-----------|-------------|
| [Resumen Ejecutivo](es/executive_summary.md) | Visión general, beneficios clave, inicio rápido |
| [Caso de Estudio](es/case_study.md) | Aplicación real, antes/después, lecciones aprendidas |
| [Pipeline Explicado](es/pipeline_explained.md) | Guía paso a paso con ejemplos de código |
| [Fórmulas Matemáticas](es/mathematical_formulas.md) | Fundamentos geométricos, algoritmos, ecuaciones |
| [Informe Técnico](es/technical_report.md) | Arquitectura completa, modelos de datos |
| [**Referencia API**](es/api_reference.md) | Documentación completa de funciones/clases (SOLID) |

---

## Quick Links / Enlaces Rápidos

### Getting Started / Inicio Rápido

```bash
# Install / Instalar
pip install -e .

# Generate demo data / Generar datos demo
python examples/generate_demo_data.py

# Run demo / Ejecutar demo
make demo
```

### CLI Commands / Comandos CLI

```bash
vv run --help
vv chainage --help
vv export-dxf --help
vv info --help
```

### Python API / API de Python

```python
from src.io_kmz import load_geodata
from src.crs import ensure_crs
from src.geometry import extract_single_line
from src.chainage import format_chainage, generate_chainage_points
from src.annotate import annotate_to_axis, filter_by_radius, sort_by_chainage
```

---

## Document Structure / Estructura de Documentos

```
docs/
├── README.md           # This file / Este archivo
├── en/                 # English documentation
│   ├── executive_summary.md
│   ├── case_study.md
│   ├── pipeline_explained.md
│   ├── mathematical_formulas.md
│   └── technical_report.md
└── es/                 # Documentación en español
    ├── executive_summary.md
    ├── case_study.md
    ├── pipeline_explained.md
    ├── mathematical_formulas.md
    └── technical_report.md
```

---

## API Reference / Referencia API

### Core Modules / Módulos Principales

| Module | Functions | Description |
|--------|-----------|-------------|
| `src.io_kmz` | `load_geodata()`, `load_kmz()`, `save_geopackage()` | Multi-format geospatial I/O |
| `src.crs` | `ensure_crs()`, `reproject()`, `validate_projected_crs()` | CRS transformation |
| `src.geometry` | `extract_single_line()`, `get_centroids()`, `project_point_to_line()` | Geometry utilities |
| `src.chainage` | `format_chainage()`, `parse_chainage()`, `generate_chainage_points()` | K+format chainage |
| `src.annotate` | `annotate_to_axis()`, `filter_by_radius()`, `sort_by_chainage()` | Feature projection |
| `src.config` | `CorridorConfig`, `CRSConfig`, `ChainageConfig` | Pydantic configuration |

### Output Modules / Módulos de Salida

| Module | Functions | Description |
|--------|-----------|-------------|
| `src.outputs_maps` | `create_corridor_map()`, `save_corridor_map()` | PNG cartographic maps |
| `src.outputs_dxf` | `export_corridor_dxf()` | DXF CAD export |
| `src.outputs_tables` | `export_summary_csv()` | CSV summaries |

---

## CRS Reference / Referencia CRS

| EPSG | Name | Usage |
|------|------|-------|
| 4326 | WGS84 | Input from GPS/KML |
| 9377 | MAGNA-SIRGAS Colombia | Calculations (meters) |
| 3857 | Web Mercator | Map display |
