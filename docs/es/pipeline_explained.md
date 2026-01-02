# Pipeline Explicado

## Guía Paso a Paso del Procesamiento de Cartografía de Corredores

---

## Visión General

El pipeline de Vías Verdes transforma datos geoespaciales crudos en entregables de ingeniería a través de cuatro etapas principales:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ ENTRADA  │ → │ PREPARAR │ → │ PROCESAR │ → │ EXPORTAR │
│          │    │          │    │          │    │          │
│ KMZ/GPKG │    │ CRS/Geom │    │ Abscisas │    │ DXF/PNG  │
│          │    │          │    │ Proyect. │    │ CSV      │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## Etapa 1: Entrada

### Formatos Soportados

| Formato | Extensión | Descripción |
|---------|-----------|-------------|
| KMZ | `.kmz` | KML comprimido de Google Earth |
| GeoPackage | `.gpkg` | Estándar OGC, recomendado |
| GeoJSON | `.geojson` | Formato JSON para web |
| Shapefile | `.shp` | Formato legacy ESRI |
| KML | `.kml` | Markup de Google Earth |

### Cargando Datos

```python
from src.io_kmz import load_geodata

# Detección automática de formato
axis_gdf = load_geodata("corredor.kmz")
features_gdf = load_geodata("elementos.gpkg")
```

### Requisitos de Entrada

**Eje del Corredor**:
- Geometría LineString o MultiLineString única
- Debe representar la línea central del corredor
- La dirección importa: la abscisa aumenta a lo largo de la dirección de la línea

**Elementos**:
- Geometrías Point, LineString o Polygon
- Debe tener campo `Name` (o especificar campo personalizado)
- CRS: WGS84 (EPSG:4326) o proyectado

---

## Etapa 2: Preparar

### Validación y Transformación de CRS

Todos los cálculos requieren **coordenadas proyectadas** en metros. El pipeline:

1. **Detecta** CRS de entrada (o asume WGS84 si falta)
2. **Transforma** a CRS de cálculo (por defecto: EPSG:9377 MAGNA-SIRGAS)
3. **Valida** que las unidades sean metros

```python
from src.crs import ensure_crs

# Transformar a MAGNA-SIRGAS Colombia
axis_gdf = ensure_crs(axis_gdf, target_epsg=9377)
features_gdf = ensure_crs(features_gdf, target_epsg=9377)
```

### Configuración de CRS

| EPSG | Nombre | Uso |
|------|--------|-----|
| 4326 | WGS84 | Entrada (GPS/KML por defecto) |
| 9377 | MAGNA-SIRGAS Origen-Nacional | Cálculos (Colombia) |
| 3857 | Web Mercator | Visualización de mapas con mapa base |

### Preparación de Geometría

**Extraer LineString único del eje**:

```python
from src.geometry import extract_single_line

axis_line = extract_single_line(axis_gdf)
# Maneja MultiLineString fusionando componentes
```

**Obtener centroides para elementos poligonales**:

```python
from src.geometry import get_centroids

# Para proyectar elementos poligonales, usar sus centroides
features_with_centroids = get_centroids(features_gdf)
```

---

## Etapa 3: Procesar

### 3.1 Generación de Abscisas

Generar marcadores K+format a intervalos regulares a lo largo del eje:

```python
from src.chainage import generate_chainage_points

markers = generate_chainage_points(
    line=axis_line,
    interval_m=500,  # Cada 500 metros
    start_m=0        # Abscisa inicial
)

# Retorna: [(Point, distancia_m, etiqueta), ...]
# Ejemplo: [(Point(...), 0, "K0+000"), (Point(...), 500, "K0+500"), ...]
```

**Formateo de abscisas**:

```python
from src.chainage import format_chainage, parse_chainage

format_chainage(5250)      # "K5+250"
format_chainage(11795)     # "K11+795"

parse_chainage("K5+250")   # 5250.0
```

### 3.2 Proyección de Elementos

Proyectar cada elemento al eje del corredor:

```python
from src.annotate import annotate_to_axis

annotated = annotate_to_axis(
    gdf_points=features_gdf,
    axis_line=axis_line,
    name_field="Name"
)
```

**Columnas de salida**:

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `nombre` | str | Identificador del elemento |
| `abscisa_m` | float | Distancia a lo largo del eje (metros) |
| `abscisa_lbl` | str | Etiqueta K+format |
| `dist_m` | float | Distancia perpendicular (metros) |
| `x`, `y` | float | Coordenadas originales |
| `x_axis`, `y_axis` | float | Punto de proyección en el eje |
| `geometry` | Point | Geometría original |
| `geometry_axis` | Point | Punto proyectado en el eje |

### 3.3 Filtrado por Distancia

Filtrar elementos por distancia desde el eje:

```python
from src.annotate import filter_by_radius

# Mantener solo elementos dentro de 10 km del eje
nearby = filter_by_radius(annotated, radius_m=10000)
```

### 3.4 Ordenar por Abscisa

Ordenar elementos por distancia a lo largo del eje:

```python
from src.annotate import sort_by_chainage

sorted_features = sort_by_chainage(annotated)
```

---

## Etapa 4: Exportar

### 4.1 Exportación DXF (CAD)

Exportar a archivos DXF compatibles con AutoCAD:

```python
from src.outputs_dxf import export_corridor_dxf

export_corridor_dxf(
    output_dir="salidas/",
    tramo="DEMO",
    axis_line=axis_line,
    sources_gdf=fuentes_gdf,
    disposal_gdf=disposicion_gdf
)
```

**Convención de nombres de capas**:

| Capa | Contenido |
|------|-----------|
| `EJE_{ID}` | Línea central del corredor |
| `ABSCISAS_{ID}` | Marcadores K+ |
| `FUENTES` | Fuentes de materiales |
| `ZONAS_DISPOSICION` | Zonas de disposición |

### 4.2 Exportación de Mapas (PNG)

Generar mapas cartográficos de calidad publicable:

```python
from src.outputs_maps import create_corridor_map, save_corridor_map

fig, ax = create_corridor_map(
    axis_gdf=axis_gdf,
    features_gdf=features_gdf,
    title="Mapa de Localización del Corredor",
    figsize=(12, 12)
)

save_corridor_map(fig, "salidas/mapa_corredor.png", dpi=300)
```

**Elementos del mapa**:
- Mapa base OpenStreetMap
- Eje del corredor con estilo
- Símbolos de elementos por tipo
- Etiquetas de abscisas en puntos de proyección
- Distancias de desplazamiento en anotaciones
- Barra de escala y flecha norte
- Grilla de coordenadas
- Leyenda y pie de página con metadatos

### 4.3 Exportación de Tablas (CSV)

Exportar tablas resumen:

```python
from src.outputs_tables import export_summary_csv

export_summary_csv(
    gdf=annotated,
    output_path="salidas/resumen_elementos.csv"
)
```

**Columnas CSV**:
- `nombre`: Nombre del elemento
- `abscisa_lbl`: Posición K+format
- `abscisa_m`: Posición en metros
- `dist_m`: Distancia desde el eje
- `x`, `y`: Coordenadas originales

---

## Ejemplo de Pipeline Completo

### Uso CLI

```bash
# Pipeline completo con todas las salidas
vv run \
    --tramo DEMO \
    --axis corredor.gpkg \
    --sources fuentes.gpkg \
    --disposal disposicion.gpkg \
    --radius 20000 \
    --interval 500 \
    --dpi 300 \
    --out salidas/
```

### Script Python

```python
#!/usr/bin/env python3
"""Pipeline completo de procesamiento de corredor."""

from pathlib import Path
from src.io_kmz import load_geodata
from src.crs import ensure_crs
from src.geometry import extract_single_line, get_centroids
from src.chainage import generate_chainage_points
from src.annotate import annotate_to_axis, filter_by_radius, sort_by_chainage

# Configuración
CORRIDOR_ID = "DEMO"
OUTPUT_DIR = Path("salidas")
CHAINAGE_INTERVAL = 500
MAX_OFFSET = 20000

# 1. Cargar datos
print("Cargando datos...")
axis_gdf = load_geodata("corredor.gpkg")
sources_gdf = load_geodata("fuentes.gpkg")
disposal_gdf = load_geodata("disposicion.gpkg")

# 2. Preparar: Transformación CRS
print("Transformando CRS...")
axis_gdf = ensure_crs(axis_gdf, target_epsg=9377)
sources_gdf = ensure_crs(sources_gdf, target_epsg=9377)
disposal_gdf = ensure_crs(disposal_gdf, target_epsg=9377)

# 3. Extraer línea del eje
axis_line = extract_single_line(axis_gdf)
print(f"Longitud del corredor: {axis_line.length/1000:.1f} km")

# 4. Generar marcadores de abscisa
markers = generate_chainage_points(axis_line, CHAINAGE_INTERVAL)
print(f"Generados {len(markers)} marcadores de abscisa")

# 5. Proyectar elementos al eje
sources_centroids = get_centroids(sources_gdf)
disposal_centroids = get_centroids(disposal_gdf)

sources_annotated = annotate_to_axis(sources_centroids, axis_line, name_field="Name")
disposal_annotated = annotate_to_axis(disposal_centroids, axis_line, name_field="Name")

# 6. Filtrar por distancia
sources_annotated = filter_by_radius(sources_annotated, radius_m=MAX_OFFSET)
disposal_annotated = filter_by_radius(disposal_annotated, radius_m=MAX_OFFSET)

# 7. Ordenar por abscisa
sources_annotated = sort_by_chainage(sources_annotated)
disposal_annotated = sort_by_chainage(disposal_annotated)

print(f"Fuentes dentro del rango: {len(sources_annotated)}")
print(f"Zonas de disposición dentro del rango: {len(disposal_annotated)}")

# 8. Exportar resultados
print("Exportando...")
output_path = OUTPUT_DIR / f"salidas_{CORRIDOR_ID}"
output_path.mkdir(parents=True, exist_ok=True)

sources_annotated.to_csv(output_path / "fuentes_resumen.csv", index=False)
disposal_annotated.to_csv(output_path / "dispos_resumen.csv", index=False)

print(f"\n¡Completo! Salidas en: {output_path}")
```

---

## Configuración del Pipeline

### Usando Modelos Pydantic

```python
from src.config import CorridorConfig, CRSConfig, ChainageConfig

config = CorridorConfig(
    tramo="DEMO",
    axis_kmz=Path("corredor.gpkg"),
    sources_kmz=Path("fuentes.gpkg"),
    disposal_kmz=Path("disposicion.gpkg"),
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

## Solución de Problemas

### Problemas Comunes

| Problema | Causa | Solución |
|----------|-------|----------|
| Salida vacía | Sin elementos dentro del radio | Aumentar parámetro `--radius` |
| Advertencia CRS | CRS faltante en entrada | Especificar `assume_input_epsg=4326` |
| Error codificación DXF | Caracteres en español | Asegurar codificación UTF-8 |
| Mapa base faltante | Sin internet / contextily | Establecer `add_basemap=False` |

### Depuración

```python
from src.crs import validate_projected_crs

# Verificar CRS
print(f"CRS del eje: {axis_gdf.crs}")
print(f"CRS de elementos: {features_gdf.crs}")

# Validar CRS proyectado
assert validate_projected_crs(axis_gdf), "El eje debe estar en CRS proyectado"

# Verificar tipos de geometría
print(f"Geometría del eje: {axis_gdf.geometry.iloc[0].geom_type}")

# Validar eje
print(f"Longitud del eje: {axis_line.length} metros")
print(f"Eje es válido: {axis_line.is_valid}")
```
