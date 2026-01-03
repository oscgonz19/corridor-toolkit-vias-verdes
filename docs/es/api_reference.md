# Referencia API

## Documentación Completa de Módulos, Clases y Funciones

---

## Arquitectura de Módulos (Principios SOLID)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CORRIDOR TOOLKIT                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │   io_kmz    │   │    crs      │   │  geometry   │   │   config    │     │
│  │ [S] E/S     │   │ [S] CRS     │   │ [S] Geom    │   │ [S] Config  │     │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └─────────────┘     │
│         └────────────────┬┴─────────────────┘                               │
│  ┌─────────────┐         ▼              ┌─────────────┐                     │
│  │  chainage   │◄── [O] Extensible ───►│  annotate   │                     │
│  │ K+format    │                        │ Proyección  │                     │
│  └─────────────┘                        └─────────────┘                     │
│         ┌────────────────┼────────────────┐                                 │
│         ▼                ▼                ▼                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  [I] Interfaces         │
│  │outputs_maps │  │ outputs_dxf │  │outputs_table│  Segregadas             │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
│  ┌─────────────┐                                                            │
│  │  geology    │  [D] Inversión de Dependencias                             │
│  └─────────────┘                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Principios SOLID

| Principio | Aplicación |
|-----------|------------|
| **S**ingle Responsibility | Cada módulo: una responsabilidad |
| **O**pen/Closed | Extensible sin modificar código base |
| **L**iskov Substitution | GeoDataFrames intercambiables |
| **I**nterface Segregation | Exportadores con interfaces enfocadas |
| **D**ependency Inversion | Depende de abstracciones GeoPandas/Shapely |

---

## Módulo: `src.config`

### Clases de Configuración

#### `CRSConfig`
```python
class CRSConfig(BaseModel):
    calc_epsg: int = 9377      # MAGNA-SIRGAS (metros)
    plot_epsg: int = 3857      # Web Mercator (visualización)
    input_epsg: int = 4326     # WGS84 (entrada GPS/KML)
```

#### `ChainageConfig`
```python
class ChainageConfig(BaseModel):
    interval_m: int = 500                    # Intervalo entre marcadores
    format_template: str = "K{km}+{rest:03d}" # Formato K+
```

#### `FilterConfig`
```python
class FilterConfig(BaseModel):
    radius_m: float = 70000    # Radio máximo de búsqueda
```

#### `OutputConfig`
```python
class OutputConfig(BaseModel):
    output_dir: Path = Path("outputs")
    dpi: int = 300
    figure_size: tuple[int, int] = (10, 10)
```

#### `CorridorConfig`
```python
class CorridorConfig(BaseModel):
    tramo: str                 # Identificador de sección
    axis_kmz: Path             # Archivo del eje
    crs: CRSConfig = CRSConfig()
    chainage: ChainageConfig = ChainageConfig()
    filter: FilterConfig = FilterConfig()
    output: OutputConfig = OutputConfig()
    sources_kmz: Optional[Path] = None
    disposal_kmz: Optional[Path] = None
    boreholes_csv: Optional[Path] = None

    def get_output_dir(self) -> Path
```

---

## Módulo: `src.io_kmz`

### Funciones

| Función | Firma | Descripción |
|---------|-------|-------------|
| `load_geodata` | `(path, layer=None) -> GeoDataFrame` | Carga multi-formato con detección automática |
| `load_kmz` | `(kmz_path, temp_dir=None) -> GeoDataFrame` | Extrae y carga KML desde KMZ |
| `load_geopackage` | `(gpkg_path, layer=None) -> GeoDataFrame` | Carga desde GeoPackage |
| `save_geopackage` | `(gdf, gpkg_path, layer="features") -> Path` | Guarda a GeoPackage |

**Formatos soportados:** `.kmz`, `.gpkg`, `.geojson`, `.shp`, `.kml`

---

## Módulo: `src.crs`

### Funciones

| Función | Firma | Descripción |
|---------|-------|-------------|
| `ensure_crs` | `(gdf, target_epsg=9377, assume_input_epsg=4326) -> GeoDataFrame` | Valida y transforma CRS |
| `reproject` | `(gdf, target_epsg) -> GeoDataFrame` | Reproyecta a CRS especificado |
| `validate_projected_crs` | `(gdf) -> bool` | Verifica si CRS es proyectado |
| `get_crs_info` | `(epsg) -> dict` | Info legible del CRS |

---

## Módulo: `src.geometry`

### Funciones

| Función | Firma | Descripción |
|---------|-------|-------------|
| `to_single_line` | `(geom) -> LineString` | Convierte a LineString único |
| `extract_single_line` | `(gdf) -> LineString` | Extrae eje desde GeoDataFrame |
| `get_centroids` | `(gdf) -> GeoDataFrame` | Reemplaza con centroides, preserva originales |
| `project_point_to_line` | `(point, line) -> (Point, float)` | Proyecta punto a línea |
| `perpendicular_distance` | `(point, line) -> float` | Distancia perpendicular |

---

## Módulo: `src.chainage`

### Funciones

| Función | Firma | Descripción |
|---------|-------|-------------|
| `format_chainage` | `(distance_m) -> str` | Metros → "K5+250" |
| `parse_chainage` | `(label) -> float` | "K5+250" → 5250.0 |
| `chainage` | `(line, point) -> (float, str)` | Calcula abscisa de punto |
| `generate_chainage_points` | `(line, interval_m=500) -> List[Tuple]` | Genera marcadores |
| `chainage_points_to_gdf` | `(points, crs) -> GeoDataFrame` | Convierte a GeoDataFrame |

---

## Módulo: `src.annotate`

### Funciones

| Función | Firma | Descripción |
|---------|-------|-------------|
| `annotate_to_axis` | `(gdf_points, axis_line, name_field="Name") -> GeoDataFrame` | Proyecta y anota features |
| `filter_by_radius` | `(gdf, radius_m) -> GeoDataFrame` | Filtra por distancia |
| `sort_by_chainage` | `(gdf) -> GeoDataFrame` | Ordena por abscisa |

**Columnas de salida de `annotate_to_axis`:**
- `nombre`, `dist_m`, `abscisa_m`, `abscisa_lbl`
- `x`, `y`, `x_axis`, `y_axis`
- `geometry`, `geometry_axis`

---

## Módulo: `src.geology`

### Constantes
```python
SUCS_CODES = {"GW": "Grava bien gradada", "CH": "Arcilla de alta plasticidad", ...}
```

### Funciones

| Función | Firma | Descripción |
|---------|-------|-------------|
| `load_boreholes_csv` | `(csv_path, x_col, y_col) -> GeoDataFrame` | Carga sondeos desde CSV |
| `parse_depth_range` | `(depth_str) -> (min, max, mid)` | Parsea rango de profundidad |
| `get_sucs_description` | `(code) -> str` | Descripción SUCS |
| `summarize_by_sucs` | `(df) -> DataFrame` | Resumen por clasificación |
| `summarize_spt_by_sucs` | `(df) -> DataFrame` | Estadísticas SPT por SUCS |
| `assign_unique_ids` | `(df, marker="S1") -> DataFrame` | IDs únicos continuos |

---

## Módulo: `src.outputs_dxf`

### Funciones

| Función | Firma | Descripción |
|---------|-------|-------------|
| `export_axis_dxf` | `(axis_line, output_path, layer_name="EJE")` | Exporta eje a DXF |
| `export_points_dxf` | `(gdf, output_path, layer_name)` | Exporta puntos a DXF |
| `export_polygons_dxf` | `(gdf, output_path, layer_name)` | Exporta polígonos a DXF |
| `export_corridor_dxf` | `(output_dir, tramo, axis_line, ...) -> dict` | Exporta corredor completo |

---

## Módulo: `src.outputs_maps`

### Funciones

| Función | Firma | Descripción |
|---------|-------|-------------|
| `create_corridor_map` | `(axis_gdf, sources_gdf, ...) -> (Figure, Axes)` | Crea mapa cartográfico |
| `save_corridor_map` | `(fig, output_path, dpi=300)` | Guarda mapa a PNG |

---

## Módulo: `src.outputs_tables`

### Funciones

| Función | Firma | Descripción |
|---------|-------|-------------|
| `export_summary_csv` | `(gdf, output_path)` | Exporta resumen CSV |
| `export_geopackage` | `(gdf, output_path, layer_name)` | Exporta a GeoPackage |
| `create_chainage_table` | `(chainage_points, crs_epsg) -> DataFrame` | Tabla de abscisas |

---

## CLI: Comandos

```bash
vv run --tramo ID --axis FILE --sources FILE --out DIR
vv chainage --axis FILE --interval 500 --out FILE.csv
vv export-dxf --tramo ID --axis FILE --out DIR
vv info --axis FILE
vv version
```
