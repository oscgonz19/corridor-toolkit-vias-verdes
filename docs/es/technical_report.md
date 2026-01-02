# Informe Técnico

## Vías Verdes: Motor de Cartografía de Corredores

**Versión**: 0.1.0
**Fecha**: 2024
**Clasificación**: Código Abierto / Proyecto de Portafolio

---

## 1. Introducción

### 1.1 Propósito

Este documento proporciona documentación técnica integral para el motor de cartografía de corredores Vías Verdes. Cubre arquitectura del sistema, algoritmos, modelos de datos y detalles de implementación.

### 1.2 Alcance

El sistema procesa corredores de infraestructura lineal para producir:
- Cálculos de abscisas (distancia a lo largo del eje)
- Proyección de elementos al eje del corredor
- Entregables compatibles con CAD (DXF)
- Mapas cartográficos (PNG 300dpi)
- Resúmenes tabulares (CSV)

### 1.3 Antecedentes

Desarrollado para proyectos de corredores de infraestructura colombianos ("Vías Verdes"), el motor aborda la necesidad de procesamiento geoespacial automatizado y reproducible en flujos de trabajo de ingeniería civil.

---

## 2. Arquitectura del Sistema

### 2.1 Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CAPA CLI                                    │
│  cli/main.py - Comandos Typer: run, chainage, export-dxf, info     │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LIBRERÍA NÚCLEO                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │    io    │  │   crs    │  │ geometry │  │  config  │            │
│  │          │  │          │  │          │  │          │            │
│  │ lectura/ │  │ asegurar/│  │ extraer/ │  │ Modelos  │            │
│  │ escritura│  │ reproyect│  │ centroide│  │ Pydantic │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                          │
│  │ chainage │  │projection│  │ geotech  │                          │
│  │          │  │          │  │          │            │
│  │ K+format │  │ proyectar│  │ SUCS/SPT │                          │
│  │ marcador │  │ al eje   │  │ análisis │                          │
│  └──────────┘  └──────────┘  └──────────┘                          │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     export/                                  │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                      │   │
│  │  │   dxf   │  │  maps   │  │ tables  │                      │   │
│  │  │ salida  │  │ salida  │  │ salida  │                      │   │
│  │  │   CAD   │  │   PNG   │  │   CSV   │                      │   │
│  │  └─────────┘  └─────────┘  └─────────┘                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   DEPENDENCIAS EXTERNAS                              │
│  GeoPandas │ Shapely │ Fiona │ Matplotlib │ Contextily │ Typer     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Responsabilidades de Módulos

| Módulo | Responsabilidad |
|--------|-----------------|
| `io` | E/S geoespacial multi-formato (KMZ, GPKG, GeoJSON, SHP) |
| `crs` | Validación de CRS, transformación, metadatos |
| `geometry` | Fusión de líneas, extracción de centroide, proyección |
| `chainage` | Abscisas K+format, generación de marcadores |
| `projection` | Proyección elemento-a-eje, desplazamiento, detección de lado |
| `geotech` | Clasificación SUCS, análisis SPT, integración de sondeos |
| `export.dxf` | Generación de archivos DXF/CAD |
| `export.maps` | Generación de PNG cartográfico |
| `export.tables` | Exportación de resúmenes CSV |
| `config` | Modelos de configuración Pydantic |

### 2.3 Flujo de Datos

```
Archivos Entrada                Procesamiento                   Salidas
────────────────                ─────────────                   ───────

corredor.gpkg ──┐
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
            │ geometry. │──────▶│ chainage.   │──▶ marcadores[]
            │ extract   │       │ generate_   │
            │ _single   │       │ points()    │
            │ _line()   │       └─────────────┘
            └─────┬─────┘
                  │
elementos.gpkg ───┤
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
           archivos *.dxf                   mapas *.png
```

---

## 3. Modelos de Datos

### 3.1 Tipos Principales

```python
# Eje del corredor
axis: shapely.LineString  # En EPSG:9377 (metros)

# Colección de elementos
features: geopandas.GeoDataFrame
# Columnas requeridas: geometry, Name (o configurable)
# CRS: Cualquiera (transformado a CRS de cálculo)

# Marcador de abscisa
Marker = tuple[shapely.Point, float, str]
# (punto_en_eje, distancia_m, etiqueta)
# Ejemplo: (Point(1005000, 1003000), 5000, "K5+000")
```

### 3.2 Resultado de Proyección

```python
@dataclass
class ProjectionResult:
    nombre: str              # Identificador del elemento
    abscisa_m: float         # Distancia a lo largo del eje (metros)
    abscisa_lbl: str         # Etiqueta K+format
    desplazamiento_m: float  # Distancia perpendicular (metros)
    lado: Literal["I", "D"]  # Izquierda o derecha del eje

    # Coordenadas
    x: float                 # X original
    y: float                 # Y original
    x_eje: float             # X de proyección en el eje
    y_eje: float             # Y de proyección en el eje
```

### 3.3 Modelos de Configuración

```python
class CRSConfig(BaseModel):
    calc_epsg: int = 9377   # CRS de cálculo
    plot_epsg: int = 3857   # CRS de visualización
    input_epsg: int = 4326  # CRS de entrada por defecto

class ChainageConfig(BaseModel):
    interval_m: int = 500   # Espaciado de marcadores
    format_template: str = "K{km}+{rest:03d}"

class CorridorConfig(BaseModel):
    tramo: str              # Identificador del corredor
    axis_kmz: Path          # Ruta archivo del eje
    sources_kmz: Path = None
    disposal_kmz: Path = None
    crs: CRSConfig = CRSConfig()
    chainage: ChainageConfig = ChainageConfig()
```

---

## 4. Algoritmos

### 4.1 Cálculo de Abscisas

**Entrada**: LineString `L`, Point `Q`
**Salida**: (distancia_m, etiqueta)

```
1. Proyectar Q sobre L:
   Q' = punto_más_cercano_en_línea(L, Q)

2. Calcular distancia a lo largo de L desde origen hasta Q':
   d = distancia_línea_hasta_punto(L, Q')

3. Formatear como K+:
   km = piso(d / 1000)
   resto = d mod 1000
   etiqueta = f"K{km}+{resto:03d}"

4. Retornar (d, etiqueta)
```

**Complejidad**: O(n) donde n = número de segmentos de línea

### 4.2 Proyección de Elementos con Detección de Lado

**Entrada**: Point `Q`, LineString `L`
**Salida**: ProjectionResult

```
1. Encontrar punto de proyección:
   Q' = L.interpolate(L.project(Q))

2. Calcular desplazamiento:
   desplazamiento = distancia(Q, Q')

3. Determinar lado:
   a. Obtener dirección del eje en Q':
      t = L.project(Q')
      P1 = L.interpolate(max(0, t - 1))
      P2 = L.interpolate(min(L.length, t + 1))
      v = (P2.x - P1.x, P2.y - P1.y)

   b. Obtener vector de Q' a Q:
      u = (Q.x - Q'.x, Q.y - Q'.y)

   c. Producto cruz:
      cruz = v.x * u.y - v.y * u.x

   d. Lado:
      if cruz > 0: lado = "I"
      else: lado = "D"

4. Calcular abscisa:
   abscisa_m, abscisa_lbl = chainage(L, Q')

5. Retornar ProjectionResult(...)
```

### 4.3 Generación de Puntos de Abscisa

**Entrada**: LineString `L`, intervalo `Δ`
**Salida**: List[Marker]

```
marcadores = []
d = 0
while d <= L.length:
    P = L.interpolate(d)
    etiqueta = format_chainage(d)
    marcadores.append((P, d, etiqueta))
    d += Δ
return marcadores
```

---

## 5. Formatos de Archivo

### 5.1 Formatos de Entrada

| Formato | Driver | Notas |
|---------|--------|-------|
| KMZ | KML (extraído) | Archivo KML comprimido |
| GeoPackage | GPKG | Recomendado, soporta capas |
| GeoJSON | GeoJSON | UTF-8, amigable para web |
| Shapefile | ESRI Shapefile | Legacy, evitar para nuevos proyectos |
| KML | KML | Basado en XML |

### 5.2 Formatos de Salida

**DXF (CAD)**:
- Formato AutoCAD DXF R12/R2000
- Codificación UTF-8 para caracteres en español
- Organizado por capas (EJE_, ABSCISAS_, tipos de elemento)

**PNG (Mapas)**:
- Resolución 300 DPI (configurable)
- Espacio de color RGB
- Incluye: mapa base, elementos, anotaciones, leyenda, escala

**CSV (Tablas)**:
- Codificación UTF-8
- Separado por comas
- Encabezados: nombre, abscisa_lbl, abscisa_m, desplazamiento_m, lado, x, y

---

## 6. Sistemas de Referencia de Coordenadas

### 6.1 Estrategia de CRS

```
Entrada (WGS84)        Cálculo              Visualización
EPSG:4326       →      EPSG:9377       →    EPSG:3857
Geográfico            MAGNA-SIRGAS          Web Mercator
                      (metros)
```

### 6.2 MAGNA-SIRGAS Colombia (EPSG:9377)

**Parámetros**:
- Proyección: Transversa de Mercator
- Latitud de origen: 4°N
- Meridiano central: -73°
- Factor de escala: 0.9992
- Falso este: 5,000,000 m
- Falso norte: 2,000,000 m

**Precisión**: Sub-métrica para aplicaciones de ingeniería

### 6.3 Manejo de Transformación

```python
def ensure_crs(gdf, target_epsg=9377, assume_input_epsg=4326):
    if gdf.crs is None:
        gdf = gdf.set_crs(assume_input_epsg)
    if gdf.crs.to_epsg() != target_epsg:
        return gdf.to_crs(epsg=target_epsg)
    return gdf
```

---

## 7. Módulo Geotécnico

### 7.1 Clasificación SUCS

Códigos de clasificación de suelos estándar según ASTM D2487:

| Código | Descripción |
|--------|-------------|
| GW | Grava bien gradada |
| GP | Grava mal gradada |
| GM | Grava limosa |
| GC | Grava arcillosa |
| SW | Arena bien gradada |
| SP | Arena mal gradada |
| SM | Arena limosa |
| SC | Arena arcillosa |
| ML | Limo de baja plasticidad |
| CL | Arcilla de baja plasticidad |
| MH | Limo de alta plasticidad |
| CH | Arcilla de alta plasticidad |
| OL | Orgánico (baja plasticidad) |
| OH | Orgánico (alta plasticidad) |
| PT | Turba |

### 7.2 Correcciones SPT

**Corrección de energía (N60)**:

$$N_{60} = N_{campo} \times \frac{E_r}{60}$$

**Corrección completa**:

$$N_{60} = N_{campo} \times C_E \times C_B \times C_R \times C_S$$

| Factor | Descripción | Rango Típico |
|--------|-------------|--------------|
| $C_E$ | Relación de energía | 0.75 - 1.33 |
| $C_B$ | Diámetro de perforación | 1.0 |
| $C_R$ | Longitud de varillas | 0.75 - 1.0 |
| $C_S$ | Tipo de muestreador | 1.0 - 1.2 |

---

## 8. Consideraciones de Rendimiento

### 8.1 Benchmarks

| Operación | Tiempo Típico | Notas |
|-----------|---------------|-------|
| Cargar GPKG 10 MB | < 1 s | |
| Abscisas (1000 puntos) | < 0.5 s | |
| Proyección (1000 elementos) | < 2 s | |
| Exportación DXF | < 1 s | Por capa |
| Generación de mapa | 5-10 s | Con mapa base |

### 8.2 Uso de Memoria

- GeoDataFrame: ~1 MB por 10,000 elementos
- Figura Matplotlib: ~50 MB a 300 DPI
- Uso pico: < 500 MB para corredores típicos

### 8.3 Estrategias de Optimización

1. **Indexación espacial**: Usar `sindex` para filtrado
2. **Procesamiento por chunks**: Para corredores muy largos
3. **Caché de mapa base**: Contextily cachea tiles localmente

---

## 9. Estrategia de Pruebas

### 9.1 Categorías de Pruebas

| Categoría | Cobertura | Ubicación |
|-----------|-----------|-----------|
| Pruebas unitarias | Funciones núcleo | `tests/test_*.py` |
| Pruebas integración | Pipeline completo | `tests/test_integration.py` |
| Fixtures | Datos sintéticos | `tests/conftest.py` |

### 9.2 Casos de Prueba Clave

**Abscisas**:
- Ida y vuelta de formato: `parse(format(x)) == x`
- Casos límite: 0 m, 999 m, 1000 m
- Valores grandes: > 100 km

**Proyección**:
- Punto en el eje: desplazamiento = 0
- Punto a izquierda del eje: lado = "I"
- Punto a derecha del eje: lado = "D"

**CRS**:
- Manejo de CRS faltante
- Precisión de transformación (< 1 m error)
- Ida y vuelta: entrada → cálculo → entrada

### 9.3 Ejecutar Pruebas

```bash
# Todas las pruebas
make test

# Con cobertura
make test-cov

# Módulo específico
pytest tests/test_chainage.py -v

# Prueba individual
pytest tests/test_chainage.py::TestChainage::test_format_basic -v
```

---

## 10. Despliegue

### 10.1 Instalación

```bash
# Desde código fuente
git clone https://github.com/user/vias-verdes.git
cd vias-verdes
pip install -e ".[dev]"

# Desde PyPI (futuro)
pip install vias-verdes
```

### 10.2 Dependencias

**Requeridas**:
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

**Desarrollo**:
```
pytest>=7.0.0
pytest-cov>=4.0.0
ruff>=0.1.0
mypy>=1.0.0
```

### 10.3 Entorno

```bash
# Conda (recomendado)
conda create -n vias_verdes python=3.11
conda activate vias_verdes
pip install -e ".[dev]"
```

---

## 11. Hoja de Ruta Futura

### 11.1 Características Planificadas

| Prioridad | Característica | Estado |
|-----------|----------------|--------|
| Alta | Mapa web interactivo (Folium) | Planificado |
| Alta | Generación de informes PDF | Planificado |
| Media | Plugin QGIS | Conceptual |
| Media | Visualización de perfil 3D | Conceptual |
| Baja | Colaboración en tiempo real | Futuro |

### 11.2 Estabilidad de API

- **Estable**: módulos `chainage`, `projection`, `io`
- **En evolución**: opciones de estilo en `export.maps`
- **Experimental**: correlaciones SPT en `geotech`

---

## 12. Referencias

1. Manual de Usuario Shapely (https://shapely.readthedocs.io/)
2. Documentación GeoPandas (https://geopandas.org/)
3. ASTM D2487 - Práctica Estándar para Clasificación de Suelos (SUCS)
4. ASTM D1586 - Método de Ensayo Estándar para SPT
5. IGAC - Documentación MAGNA-SIRGAS

---

## Apéndice A: Referencia CLI

```bash
# Ejecutar pipeline completo
vv run --tramo ID --axis ARCHIVO --sources ARCHIVO --disposal ARCHIVO --out DIR

# Generar tabla de abscisas
vv chainage --axis ARCHIVO --interval 500 --out ARCHIVO.csv

# Exportar solo DXF
vv export-dxf --tramo ID --axis ARCHIVO --sources ARCHIVO --out DIR

# Mostrar info del corredor
vv info --axis ARCHIVO

# Mostrar versión
vv version
```

## Apéndice B: Variables de Entorno

| Variable | Por Defecto | Descripción |
|----------|-------------|-------------|
| `VIAS_VERDES_CRS` | 9377 | CRS de cálculo por defecto |
| `VIAS_VERDES_INTERVAL` | 500 | Intervalo de abscisa por defecto |
| `VIAS_VERDES_DPI` | 300 | Resolución de mapa por defecto |
