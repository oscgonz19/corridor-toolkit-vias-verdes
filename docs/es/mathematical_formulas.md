# Fórmulas Matemáticas

## Fundamentos Geométricos para Cartografía de Corredores

---

## 1. Cálculo de Abscisas

### Definición

La **abscisa** (también llamada "estación" o "chainage" en inglés) es la distancia medida a lo largo de una línea de referencia (el eje del corredor) desde un punto de origen definido.

### Distancia a lo Largo de la Línea

Dado un eje de corredor $L$ definido como una secuencia de vértices:

$$L = \{P_0, P_1, P_2, \ldots, P_n\}$$

La longitud total del eje es:

$$|L| = \sum_{i=0}^{n-1} d(P_i, P_{i+1})$$

Donde $d(A, B)$ es la distancia euclidiana:

$$d(A, B) = \sqrt{(x_B - x_A)^2 + (y_B - y_A)^2}$$

### Proyección de Punto a Línea

Para un punto arbitrario $Q$, encontramos su proyección $Q'$ sobre la línea $L$:

$$Q' = \arg\min_{P \in L} d(Q, P)$$

La **abscisa** del punto $Q$ es la distancia a lo largo de $L$ desde el origen $P_0$ hasta la proyección $Q'$:

$$\text{abscisa}(Q) = \sum_{i=0}^{k-1} d(P_i, P_{i+1}) + d(P_k, Q')$$

Donde $Q'$ está en el segmento $\overline{P_k P_{k+1}}$.

### Representación K+Format

El valor de abscisa en metros se formatea como:

$$\text{K}\lfloor m / 1000 \rfloor + (m \mod 1000)$$

**Ejemplo**: 5250 m → K5+250

```python
def format_chainage(distance_m: float) -> str:
    km = int(distance_m // 1000)
    rest = int(distance_m % 1000)
    return f"K{km}+{rest:03d}"
```

---

## 2. Desplazamiento Perpendicular

### Definición

El **desplazamiento perpendicular** (o "distancia offset") es la distancia más corta desde un punto hasta el eje del corredor.

### Cálculo

Para el punto $Q$ con proyección $Q'$ sobre el eje $L$:

$$\text{desplazamiento}(Q) = d(Q, Q') = \sqrt{(x_Q - x_{Q'})^2 + (y_Q - y_{Q'})^2}$$

### Distancia Punto-Segmento

Para un segmento de línea $\overline{AB}$ y punto $Q$:

1. Calcular parámetro $t$:

$$t = \frac{\vec{AQ} \cdot \vec{AB}}{|\vec{AB}|^2} = \frac{(x_Q - x_A)(x_B - x_A) + (y_Q - y_A)(y_B - y_A)}{(x_B - x_A)^2 + (y_B - y_A)^2}$$

2. Limitar $t$ a $[0, 1]$:

$$t' = \max(0, \min(1, t))$$

3. Punto de proyección:

$$Q' = A + t' \cdot \vec{AB} = (x_A + t'(x_B - x_A), \; y_A + t'(y_B - y_A))$$

4. Distancia:

$$d(Q, \overline{AB}) = d(Q, Q')$$

---

## 3. Detección de Lado (Izquierda/Derecha)

### Método del Producto Cruz

Para determinar en qué lado del eje está un punto, usamos el **producto cruz** de vectores.

Dado:
- Vector de dirección del eje en el punto de proyección: $\vec{v} = (v_x, v_y)$
- Vector desde proyección al punto original: $\vec{u} = Q - Q' = (u_x, u_y)$

El **producto cruz 2D** (componente z del producto cruz 3D):

$$\vec{v} \times \vec{u} = v_x \cdot u_y - v_y \cdot u_x$$

### Determinación del Lado

$$\text{lado} = \begin{cases}
\text{Izquierda (I)} & \text{si } \vec{v} \times \vec{u} > 0 \\
\text{Derecha (D)} & \text{si } \vec{v} \times \vec{u} < 0 \\
\text{Sobre el eje} & \text{si } \vec{v} \times \vec{u} = 0
\end{cases}$$

**Convención**: Mirando en la dirección de abscisa creciente:
- **Izquierda (+I)**: Producto cruz positivo
- **Derecha (+D)**: Producto cruz negativo

```python
def determine_side(point, axis, projected) -> str:
    # Obtener dirección del eje en el punto de proyección
    t = axis.project(projected)
    p1 = axis.interpolate(max(0, t - 1))
    p2 = axis.interpolate(min(axis.length, t + 1))

    # Vector de dirección
    vx, vy = p2.x - p1.x, p2.y - p1.y

    # Vector punto-a-proyección
    ux, uy = point.x - projected.x, point.y - projected.y

    # Producto cruz
    cross = vx * uy - vy * ux

    return "I" if cross > 0 else "D"
```

---

## 4. Generación de Puntos de Abscisa

### Marcadores Basados en Intervalo

Generar puntos a lo largo del eje a intervalos regulares:

$$\text{marcadores} = \{L(s) : s \in \{0, \Delta, 2\Delta, \ldots, \lfloor |L| / \Delta \rfloor \cdot \Delta\}\}$$

Donde:
- $\Delta$ = distancia de intervalo (ej., 500 m)
- $L(s)$ = punto en la línea $L$ a distancia $s$ desde el origen

### Interpolación Lineal en Polilínea

Para encontrar punto a distancia $s$ a lo largo de polilínea:

1. Encontrar segmento que contiene la distancia $s$:
   - Longitudes acumuladas: $C_i = \sum_{j=0}^{i-1} d(P_j, P_{j+1})$
   - Encontrar $k$ tal que $C_k \leq s < C_{k+1}$

2. Interpolar dentro del segmento:
   - Parámetro local: $t = (s - C_k) / d(P_k, P_{k+1})$
   - Punto: $L(s) = P_k + t \cdot (P_{k+1} - P_k)$

```python
def interpolate_along_line(line: LineString, distance: float) -> Point:
    return line.interpolate(distance)
```

---

## 5. Sistemas de Referencia de Coordenadas

### Pipeline de Transformación

```
Entrada (WGS84, EPSG:4326)
    ↓ Geográfico → Proyectado
Cálculo (MAGNA-SIRGAS, EPSG:9377)
    ↓ Proyectado → Web Mercator
Visualización (Web Mercator, EPSG:3857)
```

### MAGNA-SIRGAS Colombia (EPSG:9377)

- **Tipo**: Proyección Transversa de Mercator
- **Origen**: Meridiano central en -73° (centro aproximado de Colombia)
- **Unidades**: Metros
- **Falso Este**: 5,000,000 m
- **Falso Norte**: 2,000,000 m

### Precisión de Distancias

Todos los cálculos de distancia deben usar **coordenadas proyectadas** (metros).

**Error en WGS84**: Usar coordenadas geográficas directamente introduciría errores significativos:
- 1° latitud ≈ 111 km (constante)
- 1° longitud ≈ 111 km × cos(latitud) (varía con latitud)

A latitud 4°N (Colombia): 1° longitud ≈ 110.7 km

---

## 6. Fórmulas Geotécnicas

### Corrección de Energía SPT (N60)

El conteo de golpes del Ensayo de Penetración Estándar (SPT) requiere corrección de energía:

$$N_{60} = N_{\text{campo}} \times \frac{E_r}{60}$$

Donde:
- $N_{\text{campo}}$ = conteo de golpes crudo
- $E_r$ = relación de energía del martillo (%)
- 60 = energía de referencia (60% del máximo teórico)

**Valores típicos**:
- Martillo de seguridad: $E_r \approx 60\%$ → $N_{60} = N_{\text{campo}}$
- Martillo donut: $E_r \approx 45\%$ → $N_{60} = 0.75 \times N_{\text{campo}}$
- Martillo automático: $E_r \approx 80\%$ → $N_{60} = 1.33 \times N_{\text{campo}}$

### Corrección SPT Completa

$$N_{60} = N_{\text{campo}} \times C_E \times C_B \times C_R \times C_S$$

| Factor | Símbolo | Descripción | Valores Típicos |
|--------|---------|-------------|-----------------|
| Energía | $C_E$ | $E_r / 60$ | 0.75 - 1.33 |
| Perforación | $C_B$ | Corrección de diámetro | 1.0 (65-115mm) |
| Longitud varillas | $C_R$ | Corrección varillas cortas | 0.75 - 1.0 |
| Muestreador | $C_S$ | Presencia de camisa | 1.0 - 1.2 |

### Clasificación SUCS

El Sistema Unificado de Clasificación de Suelos (SUCS/USCS) usa:

**Suelos de grano grueso** (>50% retenido en malla #200):
- **G** = Grava (>50% de fracción gruesa en malla #4)
- **S** = Arena (≤50% de fracción gruesa en malla #4)

**Segunda letra** (gradación/finos):
- **W** = Bien gradado ($C_u > 4$ para grava, $C_u > 6$ para arena; $1 < C_c < 3$)
- **P** = Mal gradado
- **M** = Finos limosos
- **C** = Finos arcillosos

**Suelos de grano fino** (≥50% pasando malla #200):
- **M** = Limo
- **C** = Arcilla
- **O** = Orgánico

**Plasticidad**:
- **L** = Baja plasticidad ($LL < 50$)
- **H** = Alta plasticidad ($LL \geq 50$)

---

## 7. Resumen de Ecuaciones Clave

| Cálculo | Fórmula |
|---------|---------|
| Distancia euclidiana | $d(A,B) = \sqrt{(x_B-x_A)^2 + (y_B-y_A)^2}$ |
| Abscisa | $\text{abs}(Q) = \text{dist a lo largo de } L \text{ hasta } Q'$ |
| Formato K+ | $\text{K}\lfloor m/1000 \rfloor + (m \mod 1000)$ |
| Desplazamiento | $\text{desp}(Q) = d(Q, Q')$ |
| Lado (producto cruz) | $v_x u_y - v_y u_x > 0 \Rightarrow \text{Izquierda}$ |
| Corrección SPT | $N_{60} = N_f \times (E_r / 60)$ |

---

## Referencias

1. **Manual de Usuario Shapely** - Proyección de puntos e interpolación de líneas
2. **ASTM D2487** - Práctica Estándar para Clasificación de Suelos (SUCS)
3. **ASTM D1586** - Método de Ensayo Estándar para SPT
4. **IGAC** - Instituto Geográfico Agustín Codazzi (documentación MAGNA-SIRGAS)
