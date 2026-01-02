"""
Generate synthetic demo data for portfolio demonstration.

Creates realistic corridor data without exposing real coordinates.
All data is synthetic but follows realistic patterns for Colombian
infrastructure corridors.

Demo Data Schemas
-----------------

**demo_axis.gpkg**
    | Column      | Type        | Description                      |
    |-------------|-------------|----------------------------------|
    | Name        | str         | Corridor identifier              |
    | tramo       | str         | Section code (e.g., "T01")       |
    | length_km   | float       | Total length in kilometers       |
    | municipio   | str         | Municipality name                |
    | departamento| str         | Department name                  |
    | geometry    | LineString  | Corridor centerline              |

**demo_sources.gpkg** (Material sources: quarries, borrow pits)
    | Column      | Type        | Description                      |
    |-------------|-------------|----------------------------------|
    | Name        | str         | Source name                      |
    | source_id   | str         | Unique identifier (FU-001)       |
    | material    | str         | Material type (grava, arena...)  |
    | capacity_m3 | float       | Estimated capacity in m³         |
    | status      | str         | active/inactive/potential        |
    | owner       | str         | Owner/operator name              |
    | geometry    | Point       | Source location                  |

**demo_disposal.gpkg** (Disposal/ZODME zones)
    | Column      | Type        | Description                      |
    |-------------|-------------|----------------------------------|
    | Name        | str         | Zone name                        |
    | zone_id     | str         | Unique identifier (ZD-001)       |
    | zone_type   | str         | ZODME/temporal/permanente        |
    | area_ha     | float       | Area in hectares                 |
    | capacity_m3 | float       | Disposal capacity in m³          |
    | status      | str         | disponible/en_uso/cerrado        |
    | geometry    | Polygon     | Zone boundary                    |

**demo_boreholes.gpkg/.csv** (Geotechnical boreholes)
    | Column        | Type   | Description                      |
    |---------------|--------|----------------------------------|
    | id            | str    | Borehole ID (S-01, S-02...)      |
    | Name          | str    | Borehole name                    |
    | estratigrafia | str    | Soil description (Spanish)       |
    | profundidad_m | str    | Depth range "from-to"            |
    | prof_ini_m    | float  | Layer start depth (m)            |
    | prof_fin_m    | float  | Layer end depth (m)              |
    | prof_medio_m  | float  | Layer midpoint depth (m)         |
    | N_SPT         | int    | Standard Penetration Test blows  |
    | SUCS          | str    | USCS classification code         |
    | PK            | str    | K+format chainage label          |
    | X             | float  | Easting coordinate               |
    | Y             | float  | Northing coordinate              |
    | geometry      | Point  | Borehole location                |

CRS: All geometries are in EPSG:9377 (MAGNA-SIRGAS Colombia Origin-National)
"""

import random
from pathlib import Path
from typing import List, Tuple

import numpy as np
import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon
import pandas as pd


# =============================================================================
# Schema Definitions (for documentation and validation)
# =============================================================================

AXIS_SCHEMA = {
    "Name": str,
    "tramo": str,
    "length_km": float,
    "municipio": str,
    "departamento": str,
}

SOURCES_SCHEMA = {
    "Name": str,
    "source_id": str,
    "material": str,
    "capacity_m3": float,
    "status": str,
    "owner": str,
}

DISPOSAL_SCHEMA = {
    "Name": str,
    "zone_id": str,
    "zone_type": str,
    "area_ha": float,
    "capacity_m3": float,
    "status": str,
}

BOREHOLES_SCHEMA = {
    "id": str,
    "Name": str,
    "estratigrafia": str,
    "profundidad_m": str,
    "prof_ini_m": float,
    "prof_fin_m": float,
    "prof_medio_m": float,
    "N_SPT": int,
    "SUCS": str,
    "PK": str,
    "X": float,
    "Y": float,
}


# =============================================================================
# Realistic Data Templates (Colombian context)
# =============================================================================

COLOMBIAN_MUNICIPALITIES = [
    ("Puerto López", "Meta"),
    ("Villavicencio", "Meta"),
    ("Acacías", "Meta"),
    ("Yopal", "Casanare"),
    ("Aguazul", "Casanare"),
    ("Tauramena", "Casanare"),
    ("Paz de Ariporo", "Casanare"),
    ("Villanueva", "Casanare"),
]

MATERIAL_TYPES = [
    ("Grava aluvial", 50000, 500000),
    ("Arena de río", 30000, 300000),
    ("Material de cantera", 100000, 1000000),
    ("Recebo", 20000, 200000),
    ("Roca triturada", 80000, 600000),
    ("Agregado fino", 25000, 150000),
]

SOURCE_NAMES = [
    "Cantera La Esperanza",
    "Gravera El Progreso",
    "Arenera San Miguel",
    "Cantera La Victoria",
    "Planta El Carmen",
    "Gravera Santa Rosa",
    "Cantera San José",
    "Arenera La Unión",
    "Cantera El Dorado",
    "Gravera La Florida",
]

DISPOSAL_NAMES = [
    "ZODME Norte",
    "ZODME Sur",
    "Zona de Acopio Central",
    "ZODME Sector Oriental",
    "Área de Disposición Rural",
    "ZODME Kilómetro 5",
    "Zona Temporal T1",
    "ZODME Permanente P1",
]

SUCS_SOILS = [
    ("CH", "ARCILLA DE ALTA PLASTICIDAD CAFÉ OSCURO"),
    ("CL", "ARCILLA DE BAJA PLASTICIDAD CAFÉ CLARO"),
    ("SC", "ARENA ARCILLOSA GRIS VERDOSO"),
    ("SM", "ARENA LIMOSA CAFÉ AMARILLENTO"),
    ("ML", "LIMO DE BAJA PLASTICIDAD GRIS"),
    ("MH", "LIMO DE ALTA PLASTICIDAD CAFÉ ROJIZO"),
    ("OH", "SUELO ORGÁNICO DE ALTA PLASTICIDAD NEGRO"),
    ("OL", "SUELO ORGÁNICO DE BAJA PLASTICIDAD CAFÉ OSCURO"),
    ("GC", "GRAVA ARCILLOSA BIEN GRADADA"),
    ("GM", "GRAVA LIMOSA MAL GRADADA"),
    ("GP", "GRAVA MAL GRADADA GRIS"),
    ("SW", "ARENA BIEN GRADADA CON GRAVA"),
]

OWNER_NAMES = [
    "Agregados del Llano S.A.S.",
    "Materiales del Oriente Ltda.",
    "Concretos y Canteras S.A.",
    "Pétreos de Colombia S.A.S.",
    "Municipal",
    "Consorcio Vías Verdes",
    "Particular",
]


# =============================================================================
# Geometry Generation Functions
# =============================================================================

def generate_corridor_axis(
    start_x: float = 1000000,
    start_y: float = 1000000,
    length_km: float = 12,
    num_vertices: int = 50,
    curvature: float = 0.3,
    seed: int = 42
) -> LineString:
    """
    Generate a realistic-looking corridor axis.

    Creates a sinuous line simulating a road or pipeline corridor
    through varied terrain. The curvature parameter controls how
    much the line deviates from a straight path.

    Args:
        start_x: Starting X coordinate (easting in meters).
        start_y: Starting Y coordinate (northing in meters).
        length_km: Total corridor length in kilometers.
        num_vertices: Number of vertices in the line.
            More vertices = smoother curves.
        curvature: Amount of random curvature (0-1).
            0 = straight line, 1 = highly sinuous.
        seed: Random seed for reproducibility.

    Returns:
        LineString: Corridor axis geometry.
            Length will be approximately `length_km` (may vary due to curves).
    """
    np.random.seed(seed)

    length_m = length_km * 1000
    segment_length = length_m / num_vertices

    coords = [(start_x, start_y)]
    angle = np.pi / 4  # Start heading NE

    for _ in range(num_vertices):
        # Add random curvature
        angle += np.random.uniform(-curvature, curvature)

        dx = segment_length * np.cos(angle)
        dy = segment_length * np.sin(angle)

        new_x = coords[-1][0] + dx
        new_y = coords[-1][1] + dy

        coords.append((new_x, new_y))

    return LineString(coords)


def generate_sources(
    axis: LineString,
    num_sources: int = 8,
    max_offset_m: float = 15000,
    min_offset_m: float = 2000,
    seed: int = 123
) -> gpd.GeoDataFrame:
    """
    Generate synthetic material source features.

    Creates point features representing quarries, gravel pits, and
    other material sources near the corridor axis.

    Args:
        axis: Corridor axis LineString.
        num_sources: Number of sources to generate.
        max_offset_m: Maximum perpendicular offset from axis.
        min_offset_m: Minimum perpendicular offset from axis.
        seed: Random seed for reproducibility.

    Returns:
        gpd.GeoDataFrame: Sources with schema:
            - Name, source_id, material, capacity_m3, status, owner, geometry
    """
    np.random.seed(seed)

    records = []
    total_length = axis.length

    for i in range(num_sources):
        # Random position along axis
        dist_along = np.random.uniform(0.1, 0.9) * total_length
        point_on_axis = axis.interpolate(dist_along)

        # Get perpendicular direction
        next_point = axis.interpolate(dist_along + 10)
        dx = next_point.x - point_on_axis.x
        dy = next_point.y - point_on_axis.y
        length = np.sqrt(dx**2 + dy**2)

        # Perpendicular unit vector
        perp_x = -dy / length
        perp_y = dx / length

        # Random offset distance and side
        offset = np.random.uniform(min_offset_m, max_offset_m)
        side = np.random.choice([-1, 1])

        # Calculate offset point
        feat_x = point_on_axis.x + side * offset * perp_x
        feat_y = point_on_axis.y + side * offset * perp_y

        # Realistic attributes
        name = SOURCE_NAMES[i % len(SOURCE_NAMES)]
        material_info = MATERIAL_TYPES[np.random.randint(0, len(MATERIAL_TYPES))]
        capacity = np.random.uniform(material_info[1], material_info[2])

        records.append({
            "Name": name,
            "source_id": f"FU-{i+1:03d}",
            "material": material_info[0],
            "capacity_m3": round(capacity, 0),
            "status": np.random.choice(["activo", "inactivo", "potencial"], p=[0.6, 0.2, 0.2]),
            "owner": np.random.choice(OWNER_NAMES),
            "geometry": Point(feat_x, feat_y),
        })

    return gpd.GeoDataFrame(records, crs="EPSG:9377")


def generate_disposal_zones(
    axis: LineString,
    num_zones: int = 5,
    max_offset_m: float = 20000,
    min_offset_m: float = 3000,
    polygon_size_m: float = 500,
    seed: int = 456
) -> gpd.GeoDataFrame:
    """
    Generate synthetic disposal zone features.

    Creates polygon features representing ZODME (Zonas de Disposición
    de Material de Excavación) and temporary storage areas.

    Args:
        axis: Corridor axis LineString.
        num_zones: Number of zones to generate.
        max_offset_m: Maximum perpendicular offset from axis.
        min_offset_m: Minimum perpendicular offset from axis.
        polygon_size_m: Approximate polygon radius in meters.
        seed: Random seed for reproducibility.

    Returns:
        gpd.GeoDataFrame: Disposal zones with schema:
            - Name, zone_id, zone_type, area_ha, capacity_m3, status, geometry
    """
    np.random.seed(seed)

    records = []
    total_length = axis.length

    for i in range(num_zones):
        # Random position along axis
        dist_along = np.random.uniform(0.15, 0.85) * total_length
        point_on_axis = axis.interpolate(dist_along)

        # Get perpendicular direction
        next_point = axis.interpolate(dist_along + 10)
        dx = next_point.x - point_on_axis.x
        dy = next_point.y - point_on_axis.y
        length = np.sqrt(dx**2 + dy**2)

        # Perpendicular unit vector
        perp_x = -dy / length
        perp_y = dx / length

        # Random offset distance and side
        offset = np.random.uniform(min_offset_m, max_offset_m)
        side = np.random.choice([-1, 1])

        # Calculate center point
        center_x = point_on_axis.x + side * offset * perp_x
        center_y = point_on_axis.y + side * offset * perp_y

        # Generate irregular polygon around center
        num_sides = np.random.randint(5, 8)
        angles = np.linspace(0, 2 * np.pi, num_sides + 1)[:-1]
        size_factor = np.random.uniform(0.8, 1.5)
        radii = np.random.uniform(0.7, 1.3, num_sides) * polygon_size_m * size_factor

        poly_coords = [
            (center_x + r * np.cos(a), center_y + r * np.sin(a))
            for a, r in zip(angles, radii)
        ]
        poly_coords.append(poly_coords[0])  # Close polygon

        polygon = Polygon(poly_coords)
        area_ha = polygon.area / 10000  # Convert m² to hectares

        # Realistic attributes
        name = DISPOSAL_NAMES[i % len(DISPOSAL_NAMES)]
        zone_type = np.random.choice(["ZODME", "temporal", "permanente"], p=[0.5, 0.3, 0.2])

        # Capacity based on area (roughly 3m average height)
        capacity = area_ha * 10000 * 3  # m³

        records.append({
            "Name": name,
            "zone_id": f"ZD-{i+1:03d}",
            "zone_type": zone_type,
            "area_ha": round(area_ha, 2),
            "capacity_m3": round(capacity, 0),
            "status": np.random.choice(["disponible", "en_uso", "cerrado"], p=[0.5, 0.3, 0.2]),
            "geometry": polygon,
        })

    return gpd.GeoDataFrame(records, crs="EPSG:9377")


def generate_boreholes(
    axis: LineString,
    num_boreholes: int = 15,
    max_offset_m: float = 500,
    seed: int = 789
) -> Tuple[pd.DataFrame, gpd.GeoDataFrame]:
    """
    Generate synthetic borehole data along corridor.

    Creates realistic geotechnical borehole data with multiple
    soil layers per borehole, SPT values, and SUCS classifications.

    Args:
        axis: Corridor axis LineString.
        num_boreholes: Number of boreholes to generate.
        max_offset_m: Maximum offset from axis (boreholes are near axis).
        seed: Random seed for reproducibility.

    Returns:
        Tuple[pd.DataFrame, gpd.GeoDataFrame]:
            - DataFrame: All soil layers (multiple rows per borehole)
            - GeoDataFrame: Borehole locations (one point per borehole)
    """
    np.random.seed(seed)

    layer_records = []
    location_records = []
    total_length = axis.length

    for i in range(num_boreholes):
        borehole_id = f"S-{i+1:02d}"

        # Position along axis (evenly distributed)
        dist_along = (i + 1) / (num_boreholes + 1) * total_length
        point_on_axis = axis.interpolate(dist_along)

        # Small random offset (boreholes are near the axis)
        offset_x = np.random.uniform(-max_offset_m, max_offset_m)
        offset_y = np.random.uniform(-max_offset_m, max_offset_m)

        x = point_on_axis.x + offset_x
        y = point_on_axis.y + offset_y

        # K+format chainage
        km = int(dist_along / 1000)
        rest = int(dist_along % 1000)
        pk_label = f"K{km}+{rest:03d}"

        # Store location
        location_records.append({
            "id": borehole_id,
            "Name": f"Sondeo {borehole_id}",
            "PK": pk_label,
            "X": x,
            "Y": y,
            "geometry": Point(x, y),
        })

        # Generate soil layers with realistic depth progression
        depth = 0
        total_depth = np.random.uniform(8, 15)
        layer_num = 0

        while depth < total_depth:
            layer_num += 1
            thickness = np.random.uniform(0.5, 2.5)
            depth_end = min(depth + thickness, total_depth)

            # Select soil type (weighted towards common types)
            soil_idx = np.random.choice(
                len(SUCS_SOILS),
                p=[0.15, 0.15, 0.12, 0.12, 0.10, 0.08, 0.05, 0.05, 0.06, 0.06, 0.03, 0.03]
            )
            sucs_code, description = SUCS_SOILS[soil_idx]

            # SPT N-value (varies with depth and soil type)
            base_n = np.random.randint(3, 15)
            depth_factor = 1 + (depth / 10) * 0.5  # Increases with depth
            n_spt = int(base_n * depth_factor)

            layer_records.append({
                "id": borehole_id,
                "Name": f"Sondeo {borehole_id}",
                "estratigrafia": description,
                "profundidad_m": f"{depth:.2f}-{depth_end:.2f}",
                "prof_ini_m": round(depth, 2),
                "prof_fin_m": round(depth_end, 2),
                "prof_medio_m": round((depth + depth_end) / 2, 2),
                "N_SPT": n_spt,
                "SUCS": sucs_code,
                "PK": pk_label,
                "X": x,
                "Y": y,
            })

            depth = depth_end

    # Create DataFrames
    layers_df = pd.DataFrame(layer_records)
    locations_gdf = gpd.GeoDataFrame(location_records, crs="EPSG:9377")

    return layers_df, locations_gdf


# =============================================================================
# Main Generation Function
# =============================================================================

def main():
    """
    Generate all demo data files.

    Creates a complete set of synthetic demo data in examples/demo_data/:
        - demo_axis.gpkg: Corridor centerline
        - demo_sources.gpkg: Material source points
        - demo_disposal.gpkg: Disposal zone polygons
        - demo_boreholes.csv: Borehole layers (tabular)
        - demo_boreholes.gpkg: Borehole locations (spatial)

    All data is synthetic and safe for public repository.
    """
    output_dir = Path(__file__).parent / "demo_data"
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("Vías Verdes - Demo Data Generator")
    print("=" * 60)
    print(f"\nOutput directory: {output_dir}\n")

    # Generate axis
    print("[1/4] Generating corridor axis...")
    axis = generate_corridor_axis(length_km=12)

    municipio, departamento = COLOMBIAN_MUNICIPALITIES[0]
    axis_gdf = gpd.GeoDataFrame(
        [{
            "Name": "Corredor Demo",
            "tramo": "T01",
            "length_km": round(axis.length / 1000, 2),
            "municipio": municipio,
            "departamento": departamento,
        }],
        geometry=[axis],
        crs="EPSG:9377"
    )
    axis_gdf.to_file(output_dir / "demo_axis.gpkg", driver="GPKG")
    print(f"       Created: demo_axis.gpkg ({axis_gdf['length_km'].iloc[0]} km)")

    # Generate sources
    print("[2/4] Generating material sources...")
    sources_gdf = generate_sources(axis, num_sources=8, seed=123)
    sources_gdf.to_file(output_dir / "demo_sources.gpkg", driver="GPKG")
    print(f"       Created: demo_sources.gpkg ({len(sources_gdf)} sources)")

    # Generate disposal zones
    print("[3/4] Generating disposal zones...")
    disposal_gdf = generate_disposal_zones(axis, num_zones=5, seed=456)
    disposal_gdf.to_file(output_dir / "demo_disposal.gpkg", driver="GPKG")
    print(f"       Created: demo_disposal.gpkg ({len(disposal_gdf)} zones)")

    # Generate borehole data
    print("[4/4] Generating borehole data...")
    layers_df, locations_gdf = generate_boreholes(axis, num_boreholes=15, seed=789)

    # Save CSV (all layers)
    layers_df.to_csv(output_dir / "demo_boreholes.csv", index=False)
    print(f"       Created: demo_boreholes.csv ({len(layers_df)} soil layers)")

    # Save GeoPackage (locations only)
    locations_gdf.to_file(output_dir / "demo_boreholes.gpkg", driver="GPKG")
    print(f"       Created: demo_boreholes.gpkg ({len(locations_gdf)} boreholes)")

    # Summary
    print("\n" + "=" * 60)
    print("Demo data generation complete!")
    print("=" * 60)
    print("\nFiles created:")
    for f in sorted(output_dir.glob("*")):
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name:25} ({size_kb:.1f} KB)")

    print("\nSchemas:")
    print("  - demo_axis.gpkg:      LineString with tramo, length_km, municipio")
    print("  - demo_sources.gpkg:   Point with source_id, material, capacity_m3")
    print("  - demo_disposal.gpkg:  Polygon with zone_id, zone_type, area_ha")
    print("  - demo_boreholes.*:    Layers with SUCS, N_SPT, depths")


if __name__ == "__main__":
    main()
