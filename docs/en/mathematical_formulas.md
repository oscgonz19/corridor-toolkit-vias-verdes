# Mathematical Formulas

## Geometric Foundations for Corridor Cartography

---

## 1. Chainage Calculation

### Definition

**Chainage** (also called "stationing" or "abscisas" in Spanish) is the distance measured along a reference line (the corridor axis) from a defined origin point.

### Distance Along Line

Given a corridor axis $L$ defined as a sequence of vertices:

$$L = \{P_0, P_1, P_2, \ldots, P_n\}$$

The total length of the axis is:

$$|L| = \sum_{i=0}^{n-1} d(P_i, P_{i+1})$$

Where $d(A, B)$ is the Euclidean distance:

$$d(A, B) = \sqrt{(x_B - x_A)^2 + (y_B - y_A)^2}$$

### Point Projection to Line

For an arbitrary point $Q$, we find its projection $Q'$ on the line $L$:

$$Q' = \arg\min_{P \in L} d(Q, P)$$

The **chainage** of point $Q$ is the distance along $L$ from origin $P_0$ to projection $Q'$:

$$\text{chainage}(Q) = \sum_{i=0}^{k-1} d(P_i, P_{i+1}) + d(P_k, Q')$$

Where $Q'$ lies on segment $\overline{P_k P_{k+1}}$.

### K+Format Representation

The chainage value in meters is formatted as:

$$\text{K}\lfloor m / 1000 \rfloor + (m \mod 1000)$$

**Example**: 5250 m → K5+250

```python
def format_chainage(distance_m: float) -> str:
    km = int(distance_m // 1000)
    rest = int(distance_m % 1000)
    return f"K{km}+{rest:03d}"
```

---

## 2. Perpendicular Offset

### Definition

The **perpendicular offset** (or "offset distance") is the shortest distance from a point to the corridor axis.

### Calculation

For point $Q$ with projection $Q'$ on axis $L$:

$$\text{offset}(Q) = d(Q, Q') = \sqrt{(x_Q - x_{Q'})^2 + (y_Q - y_{Q'})^2}$$

### Point-to-Segment Distance

For a line segment $\overline{AB}$ and point $Q$:

1. Compute parameter $t$:

$$t = \frac{\vec{AQ} \cdot \vec{AB}}{|\vec{AB}|^2} = \frac{(x_Q - x_A)(x_B - x_A) + (y_Q - y_A)(y_B - y_A)}{(x_B - x_A)^2 + (y_B - y_A)^2}$$

2. Clamp $t$ to $[0, 1]$:

$$t' = \max(0, \min(1, t))$$

3. Projection point:

$$Q' = A + t' \cdot \vec{AB} = (x_A + t'(x_B - x_A), \; y_A + t'(y_B - y_A))$$

4. Distance:

$$d(Q, \overline{AB}) = d(Q, Q')$$

---

## 3. Side Detection (Left/Right)

### Cross Product Method

To determine which side of the axis a point lies on, we use the **cross product** of vectors.

Given:
- Axis direction vector at projection point: $\vec{v} = (v_x, v_y)$
- Vector from projection to original point: $\vec{u} = Q - Q' = (u_x, u_y)$

The **2D cross product** (z-component of 3D cross product):

$$\vec{v} \times \vec{u} = v_x \cdot u_y - v_y \cdot u_x$$

### Side Determination

$$\text{side} = \begin{cases}
\text{Left (L)} & \text{if } \vec{v} \times \vec{u} > 0 \\
\text{Right (R)} & \text{if } \vec{v} \times \vec{u} < 0 \\
\text{On axis} & \text{if } \vec{v} \times \vec{u} = 0
\end{cases}$$

**Convention**: Looking in the direction of increasing chainage:
- **Left (+L)**: Positive cross product
- **Right (+R)**: Negative cross product

```python
def determine_side(point, axis, projected) -> str:
    # Get axis direction at projection point
    t = axis.project(projected)
    p1 = axis.interpolate(max(0, t - 1))
    p2 = axis.interpolate(min(axis.length, t + 1))

    # Direction vector
    vx, vy = p2.x - p1.x, p2.y - p1.y

    # Point-to-projection vector
    ux, uy = point.x - projected.x, point.y - projected.y

    # Cross product
    cross = vx * uy - vy * ux

    return "L" if cross > 0 else "R"
```

---

## 4. Chainage Point Generation

### Interval-Based Markers

Generate points along the axis at regular intervals:

$$\text{markers} = \{L(s) : s \in \{0, \Delta, 2\Delta, \ldots, \lfloor |L| / \Delta \rfloor \cdot \Delta\}\}$$

Where:
- $\Delta$ = interval distance (e.g., 500 m)
- $L(s)$ = point on line $L$ at distance $s$ from origin

### Linear Interpolation on Polyline

To find point at distance $s$ along polyline:

1. Find segment containing distance $s$:
   - Cumulative lengths: $C_i = \sum_{j=0}^{i-1} d(P_j, P_{j+1})$
   - Find $k$ such that $C_k \leq s < C_{k+1}$

2. Interpolate within segment:
   - Local parameter: $t = (s - C_k) / d(P_k, P_{k+1})$
   - Point: $L(s) = P_k + t \cdot (P_{k+1} - P_k)$

```python
def interpolate_along_line(line: LineString, distance: float) -> Point:
    return line.interpolate(distance)
```

---

## 5. Coordinate Reference Systems

### Transformation Pipeline

```
Input (WGS84, EPSG:4326)
    ↓ Geographic → Projected
Calculation (MAGNA-SIRGAS, EPSG:9377)
    ↓ Projected → Web Mercator
Display (Web Mercator, EPSG:3857)
```

### MAGNA-SIRGAS Colombia (EPSG:9377)

- **Type**: Transverse Mercator projection
- **Origin**: Central meridian at -73° (approximate center of Colombia)
- **Units**: Meters
- **False Easting**: 5,000,000 m
- **False Northing**: 2,000,000 m

### Distance Accuracy

All distance calculations must use **projected coordinates** (meters).

**Error in WGS84**: Using geographic coordinates directly would introduce significant errors:
- 1° latitude ≈ 111 km (constant)
- 1° longitude ≈ 111 km × cos(latitude) (varies with latitude)

At latitude 4°N (Colombia): 1° longitude ≈ 110.7 km

---

## 6. Geotechnical Formulas

### SPT Energy Correction (N60)

The Standard Penetration Test (SPT) blow count requires energy correction:

$$N_{60} = N_{\text{field}} \times \frac{E_r}{60}$$

Where:
- $N_{\text{field}}$ = raw blow count
- $E_r$ = hammer energy ratio (%)
- 60 = reference energy (60% of theoretical maximum)

**Typical values**:
- Safety hammer: $E_r \approx 60\%$ → $N_{60} = N_{\text{field}}$
- Donut hammer: $E_r \approx 45\%$ → $N_{60} = 0.75 \times N_{\text{field}}$
- Automatic hammer: $E_r \approx 80\%$ → $N_{60} = 1.33 \times N_{\text{field}}$

### Full SPT Correction

$$N_{60} = N_{\text{field}} \times C_E \times C_B \times C_R \times C_S$$

| Factor | Symbol | Description | Typical Values |
|--------|--------|-------------|----------------|
| Energy | $C_E$ | $E_r / 60$ | 0.75 - 1.33 |
| Borehole | $C_B$ | Diameter correction | 1.0 (65-115mm) |
| Rod length | $C_R$ | Short rod correction | 0.75 - 1.0 |
| Sampler | $C_S$ | Liner presence | 1.0 - 1.2 |

### SUCS Classification

The Unified Soil Classification System (SUCS/USCS) uses:

**Coarse-grained soils** (>50% retained on #200 sieve):
- **G** = Gravel (>50% of coarse fraction on #4 sieve)
- **S** = Sand (≤50% of coarse fraction on #4 sieve)

**Second letter** (gradation/fines):
- **W** = Well-graded ($C_u > 4$ for gravel, $C_u > 6$ for sand; $1 < C_c < 3$)
- **P** = Poorly-graded
- **M** = Silty fines
- **C** = Clayey fines

**Fine-grained soils** (≥50% passing #200 sieve):
- **M** = Silt
- **C** = Clay
- **O** = Organic

**Plasticity**:
- **L** = Low plasticity ($LL < 50$)
- **H** = High plasticity ($LL \geq 50$)

---

## 7. Summary of Key Equations

| Calculation | Formula |
|-------------|---------|
| Euclidean distance | $d(A,B) = \sqrt{(x_B-x_A)^2 + (y_B-y_A)^2}$ |
| Chainage | $\text{ch}(Q) = \text{dist along } L \text{ to } Q'$ |
| K+format | $\text{K}\lfloor m/1000 \rfloor + (m \mod 1000)$ |
| Offset | $\text{offset}(Q) = d(Q, Q')$ |
| Side (cross product) | $v_x u_y - v_y u_x > 0 \Rightarrow \text{Left}$ |
| SPT correction | $N_{60} = N_f \times (E_r / 60)$ |

---

## References

1. **Shapely User Manual** - Point projection and line interpolation
2. **ASTM D2487** - Standard Practice for Classification of Soils (SUCS)
3. **ASTM D1586** - Standard Test Method for SPT
4. **IGAC** - Instituto Geográfico Agustín Codazzi (MAGNA-SIRGAS documentation)
