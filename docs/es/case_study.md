# Caso de Estudio: Automatización de Cartografía de Corredores

## De Flujos de Trabajo Manuales a Pipelines Reproducibles

---

## Contexto

### El Contexto del Proyecto

Un proyecto de infraestructura importante en Colombia requería mapeo y análisis espacial integral de múltiples secciones de corredor ("tramos"). Cada sección abarcaba 10-50 km e involucraba:

- **Fuentes de materiales**: Canteras y préstamos para materiales de construcción
- **Zonas de disposición**: Áreas designadas para material de excavación
- **Sondeos**: Puntos de investigación geotécnica a lo largo del alineamiento
- **Estructuras**: Puentes, alcantarillas y otras estructuras de cruce

### El Desafío Original

El equipo de ingeniería enfrentaba varios puntos de dolor:

1. **Cálculos manuales de abscisas**: Hojas de cálculo Excel con fórmulas propensas a errores
2. **Herramientas desconectadas**: GIS para análisis, CAD para entregables, sin integración
3. **Salidas inconsistentes**: Diferentes estilos de mapa, convenciones de capas por sección
4. **Retrabajo en cambios de alineamiento**: Días de recálculo cuando el corredor cambiaba

---

## La Solución: Motor Vías Verdes

### Filosofía de Diseño

Desarrollamos un pipeline basado en Python con principios claros:

- **Reproducibilidad**: Las mismas entradas siempre producen salidas idénticas
- **Separación de responsabilidades**: E/S, geometría, exportación como módulos distintos
- **Configuración sobre código**: Modelos Pydantic para parámetros del proyecto
- **CLI primero**: Scriptable para procesamiento por lotes, usable desde notebooks

### Visión General de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                      CAPA DE ENTRADA                             │
├─────────────────────────────────────────────────────────────────┤
│  KMZ / GeoPackage / GeoJSON / Shapefile                         │
│  ↓                                                               │
│  io.read_geodata() → GeoDataFrame                               │
│  crs.ensure_crs() → EPSG:9377 (MAGNA-SIRGAS)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PROCESAMIENTO                         │
├─────────────────────────────────────────────────────────────────┤
│  chainage.generate_chainage_points()                            │
│    → Marcadores K+format cada N metros                          │
│                                                                  │
│  projection.project_to_axis()                                   │
│    → Abscisa + desplazamiento + lado para cada elemento         │
│                                                                  │
│  geotech.attach_geotech_to_chainage()                           │
│    → Datos de sondeo vinculados a posición del corredor         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       CAPA DE SALIDA                             │
├─────────────────────────────────────────────────────────────────┤
│  export.dxf.export_corridor_package()                           │
│    → EJE_TRAMO.dxf, FUENTES.dxf, ZONAS_DISPOSICION.dxf         │
│                                                                  │
│  export.maps.export_corridor_map()                              │
│    → PNG 300dpi con mapa base, leyenda, escala                  │
│                                                                  │
│  export.tables.export_summary_csv()                             │
│    → Tabla de elementos con abscisas y desplazamientos          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detalles de Implementación

### Cálculo de Abscisas

El eje del corredor es un LineString en coordenadas proyectadas (EPSG:9377, metros). Para cualquier punto:

1. **Proyectar** el punto sobre el eje (punto más cercano en la línea)
2. **Medir** distancia a lo largo del eje desde el origen hasta el punto proyectado
3. **Formatear** como notación K+: `K{km}+{metros:03d}`

```python
# Ejemplo: 5250 metros desde el origen
format_chainage(5250)  # Retorna "K5+250"
```

### Proyección de Elementos con Detección de Lado

Para cada elemento (sondeo, estructura, etc.):

1. Encontrar el **punto de proyección** en el eje del corredor
2. Calcular **distancia perpendicular** (desplazamiento)
3. Determinar **lado** (izquierdo o derecho) usando producto cruz de vectores

```python
result = project_to_axis(features_gdf, axis_line)
# Retorna: abscisa_m, abscisa_label, desplazamiento_m, lado ("I" o "D")
```

### Estrategia de Exportación CAD

Los archivos DXF están organizados por capa:

| Nombre de Capa | Contenido |
|----------------|-----------|
| `EJE_TRAMO6` | Línea central del corredor |
| `ABSCISAS_TRAMO6` | Marcadores K+ como puntos con texto |
| `FUENTES` | Polígonos de fuentes de material |
| `ZONAS_DISPOSICION` | Polígonos de zonas de disposición |
| `SONDEOS` | Puntos de sondeo |

---

## Resultados

### Mejoras Cuantitativas

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Tiempo cálculo abscisas | 4 horas | 2 minutos | **99%** |
| Generación de mapas | 2 horas | 30 segundos | **99%** |
| Retrabajo por cambio de alineamiento | 2 días | 5 minutos | **99%** |
| Consistencia de salidas | Variable | 100% | Estandarizado |

### Beneficios Cualitativos

- **Fuente única de verdad**: Todas las salidas derivadas de los mismos datos de entrada
- **Control de versiones**: Scripts del pipeline rastreados en Git
- **Documentación**: Código auto-documentado con type hints y docstrings
- **Extensibilidad**: Nuevos tipos de elementos fácilmente agregados al pipeline

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. **Pydantic para configuración**: Configuraciones type-safe y auto-documentadas
2. **GeoPandas en todo**: Estructura de datos consistente desde entrada hasta salida
3. **CLI Typer**: Interfaz de línea de comandos profesional con código mínimo
4. **Contextily para mapas base**: Integración fácil de tiles OpenStreetMap

### Desafíos Superados

1. **Codificación de texto DXF**: Requirió manejo explícito de UTF-8 para caracteres en español
2. **Manejo de MultiLineString**: Algunos archivos KMZ tenían geometrías fragmentadas
3. **Suposiciones de CRS**: Datos de entrada a menudo sin metadatos CRS (se asumió WGS84)

### Mejoras Futuras

- [ ] Visor de mapa web interactivo (Folium/Leaflet)
- [ ] Plugin QGIS para integración directa
- [ ] Generación automatizada de informes (PDF con mapas + tablas)
- [ ] Visualización de perfil 3D

---

## Conclusión

El motor Vías Verdes transformó un flujo de trabajo manual y propenso a errores en un pipeline automatizado y reproducible. La inversión en ingeniería de software apropiada—diseño modular, seguridad de tipos, pruebas integrales—pagó dividendos en confiabilidad y mantenibilidad.

Este proyecto demuestra que la ingeniería geoespacial se beneficia de las mismas mejores prácticas usadas en desarrollo de software: control de versiones, pruebas automatizadas y arquitectura limpia.

---

## Apéndice Técnico

### Configuración del Entorno

```bash
conda create -n vias_verdes python=3.11
conda activate vias_verdes
pip install -e ".[dev]"
```

### Ejecutar la Demo

```bash
make demo-data  # Generar datos sintéticos
make demo       # Ejecutar pipeline completo
```

### Estructura de Salidas

```
salidas/salidas_demo/
├── EJE_DEMO.dxf              # Eje del corredor
├── FUENTES.dxf               # Fuentes de material
├── ZONAS_DISPOSICION.dxf     # Zonas de disposición
├── plano_localizacion_demo.png  # Mapa de localización
├── fuentes_resumen.csv       # Resumen de fuentes
└── dispos_resumen.csv        # Resumen de disposición
```
