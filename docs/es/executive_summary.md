# Resumen Ejecutivo

## Vías Verdes: Motor de Cartografía de Corredores

**Entregables de grado ingenieril para proyectos de infraestructura lineal**

---

## El Desafío

Los proyectos de infraestructura lineal (carreteras, ferrocarriles, ductos) requieren referenciación espacial precisa a lo largo del eje del corredor. Ingenieros y geólogos necesitan:

- Referenciar elementos por **abscisas** (distancia a lo largo del corredor: K5+250 = 5.25 km desde el origen)
- Calcular **desplazamientos perpendiculares** desde la línea central del corredor
- Producir **entregables compatibles con CAD** (DXF) para equipos de diseño
- Generar **mapas de calidad publicable** para informes y stakeholders
- Integrar **datos geotécnicos** (sondeos, clasificación de suelos) con posiciones espaciales

Los flujos de trabajo tradicionales involucran cálculos manuales en hojas de cálculo, herramientas GIS/CAD desconectadas, y retrabajo significativo cuando cambian los alineamientos.

---

## La Solución

**Vías Verdes** es un pipeline geoespacial reproducible que automatiza la cartografía de corredores:

```
Datos Crudos (KMZ/GPKG) → Abscisas → Proyección → Entregables de Ingeniería
```

### Capacidades Principales

| Capacidad | Descripción |
|-----------|-------------|
| **Automatización de Abscisas** | Marcadores K+format a intervalos configurables (K0+000, K0+500...) |
| **Proyección de Elementos** | Proyectar cualquier geometría al eje con cálculo de desplazamiento |
| **Detección de Lado** | Clasificación automática izquierda/derecha (+I/+D) relativa a dirección del eje |
| **Exportación CAD** | Archivos DXF con capas apropiadas para AutoCAD/Civil 3D |
| **Mapas Cartográficos** | PNG 300dpi con mapa base, leyenda, escala, grilla de coordenadas |
| **Módulo Geotécnico** | Clasificación SUCS, análisis de N-SPT, integración de sondeos |

---

## Beneficios Clave

### Para Equipos de Ingeniería
- **Reducción del 80%** en cálculos manuales de abscisas
- **Entregables consistentes** a través de fases del proyecto
- **Salidas listas para CAD** que integran directamente en flujos de diseño

### Para Gerentes de Proyecto
- **Pipeline reproducible** — regenerar todas las salidas cuando cambia el alineamiento
- **Trazabilidad** — scripts de procesamiento bajo control de versiones
- **Salidas estandarizadas** — estilos de mapa y convenciones de capas DXF uniformes

### Para Geocientíficos
- **Datos geotécnicos integrados** — sondeos referenciados por abscisa
- **Resúmenes de clasificación de suelos** — distribución SUCS a lo largo del corredor
- **Análisis SPT** — estadísticas de valor N por tipo de suelo y profundidad

---

## Aspectos Técnicos Destacados

- **Consciente del CRS**: Maneja entrada WGS84, proyecta a MAGNA-SIRGAS (EPSG:9377) para cálculos
- **E/S multi-formato**: Lee KMZ, GeoPackage, GeoJSON, Shapefile
- **CLI + API**: Interfaz de línea de comandos para automatización, API Python para notebooks
- **Extensible**: Configuración Pydantic, arquitectura modular

---

## Aplicaciones Objetivo

- Estudios de corredores viales y ferroviarios
- Selección de rutas e ingeniería de ductos
- Levantamientos de líneas de transmisión
- Evaluaciones de impacto ambiental a lo largo de elementos lineales
- Caracterización geotécnica de sitios para infraestructura lineal

---

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Núcleo | Python 3.10+, GeoPandas, Shapely |
| Mapeo | Matplotlib, Contextily |
| Exportación CAD | Fiona (driver DXF) |
| CLI | Typer, Rich |
| Configuración | Pydantic |

---

## Inicio Rápido

```bash
# Instalar
pip install -e .

# Generar datos demo
make demo-data

# Ejecutar pipeline completo
vv run --tramo DEMO --axis corredor.gpkg --sources elementos.gpkg --out salidas/
```

---

## Acerca de

Desarrollado a partir de proyectos reales de corredores de infraestructura colombianos ("Vías Verdes"). El código ha sido anonimizado y generalizado para uso público, demostrando mejores prácticas en automatización de ingeniería geoespacial.

**Autor**: Geólogo con experiencia en IA geoespacial y evaluación de riesgos de infraestructura.
