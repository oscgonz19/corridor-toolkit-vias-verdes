"""Basic geology module for borehole data and SUCS classification."""

from pathlib import Path
from typing import Optional

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from .config import DEFAULT_CRS


# SUCS soil classification codes
SUCS_CODES = {
    "GW": "Grava bien gradada",
    "GP": "Grava mal gradada",
    "GM": "Grava limosa",
    "GC": "Grava arcillosa",
    "SW": "Arena bien gradada",
    "SP": "Arena mal gradada",
    "SM": "Arena limosa",
    "SC": "Arena arcillosa",
    "ML": "Limo de baja plasticidad",
    "CL": "Arcilla de baja plasticidad",
    "OL": "Suelo org\u00e1nico de baja plasticidad",
    "MH": "Limo de alta plasticidad",
    "CH": "Arcilla de alta plasticidad",
    "OH": "Suelo org\u00e1nico de alta plasticidad",
    "PT": "Turba",
}


def load_boreholes_csv(
    csv_path: str | Path,
    x_col: str = "X",
    y_col: str = "Y",
    id_col: str = "id",
    crs_epsg: int = DEFAULT_CRS.calc_epsg
) -> gpd.GeoDataFrame:
    """
    Load borehole data from CSV with coordinates.

    Args:
        csv_path: Path to CSV file
        x_col: Column name for X coordinate
        y_col: Column name for Y coordinate
        id_col: Column name for borehole ID
        crs_epsg: CRS EPSG code

    Returns:
        GeoDataFrame with borehole points
    """
    df = pd.read_csv(csv_path)

    # Create geometry from coordinates
    geometry = [Point(xy) for xy in zip(df[x_col], df[y_col])]

    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=f"EPSG:{crs_epsg}")

    return gdf


def parse_depth_range(depth_str: str) -> tuple[float, float, float]:
    """
    Parse depth range string to numeric values.

    Args:
        depth_str: Depth string like "1,00 - 1,50" or "1.00-1.50"

    Returns:
        Tuple of (min_depth, max_depth, mid_depth)
    """
    # Handle both comma and period decimal separators
    depth_str = str(depth_str).replace(",", ".")

    # Split on various separator patterns
    parts = None
    for sep in [" - ", "-", " a "]:
        if sep in depth_str:
            parts = depth_str.split(sep)
            break

    if parts and len(parts) == 2:
        try:
            min_d = float(parts[0].strip())
            max_d = float(parts[1].strip())
            return min_d, max_d, (min_d + max_d) / 2
        except ValueError:
            pass

    # Try single value
    try:
        val = float(depth_str)
        return val, val, val
    except ValueError:
        return 0.0, 0.0, 0.0


def get_sucs_description(code: str) -> str:
    """
    Get SUCS soil classification description.

    Args:
        code: SUCS code (e.g., "CH", "SC")

    Returns:
        Description string
    """
    return SUCS_CODES.get(code.upper().strip(), f"Unknown ({code})")


def summarize_by_sucs(df: pd.DataFrame, sucs_col: str = "SUCS") -> pd.DataFrame:
    """
    Summarize data by SUCS classification.

    Args:
        df: DataFrame with SUCS column
        sucs_col: Name of SUCS column

    Returns:
        Summary DataFrame with counts and percentages
    """
    if sucs_col not in df.columns:
        raise ValueError(f"Column '{sucs_col}' not found")

    counts = df[sucs_col].value_counts()
    total = counts.sum()

    summary = pd.DataFrame({
        "SUCS": counts.index,
        "Conteo": counts.values,
        "Porcentaje": (counts.values / total * 100).round(1),
        "Descripcion": [get_sucs_description(c) for c in counts.index]
    })

    return summary.sort_values("Conteo", ascending=False).reset_index(drop=True)


def summarize_spt_by_sucs(
    df: pd.DataFrame,
    sucs_col: str = "SUCS",
    spt_col: str = "N_SPT"
) -> pd.DataFrame:
    """
    Summarize SPT N-values by SUCS classification.

    Args:
        df: DataFrame with SUCS and SPT columns
        sucs_col: Name of SUCS column
        spt_col: Name of SPT N-value column

    Returns:
        Summary DataFrame with statistics
    """
    if sucs_col not in df.columns or spt_col not in df.columns:
        raise ValueError(f"Required columns not found")

    # Convert SPT to numeric
    df_clean = df.copy()
    df_clean[spt_col] = pd.to_numeric(df_clean[spt_col], errors="coerce")

    summary = df_clean.groupby(sucs_col)[spt_col].agg([
        "count", "mean", "std", "min", "max"
    ]).round(2)

    summary = summary.reset_index()
    summary.columns = ["SUCS", "n", "N_SPT_medio", "N_SPT_std", "N_SPT_min", "N_SPT_max"]
    summary["Descripcion"] = summary["SUCS"].apply(get_sucs_description)

    return summary.sort_values("n", ascending=False).reset_index(drop=True)


def assign_unique_ids(
    df: pd.DataFrame,
    id_col: str = "id",
    marker: str = "S1"
) -> pd.DataFrame:
    """
    Assign continuous unique IDs detecting group restarts.

    When the ID column shows 'S1' again, it indicates a new group.

    Args:
        df: DataFrame with ID column
        id_col: Name of ID column
        marker: Marker that indicates group restart (e.g., "S1")

    Returns:
        DataFrame with 'grupo' and 'id_unico' columns added
    """
    df = df.copy()

    # Detect group boundaries
    df["group_start"] = (df[id_col] == marker).astype(int)
    df["grupo"] = df["group_start"].cumsum()

    # Create unique ID within conversation
    grupo_counts = {}
    unique_ids = []

    for _, row in df.iterrows():
        grupo = row["grupo"]
        if grupo not in grupo_counts:
            grupo_counts[grupo] = 0
        grupo_counts[grupo] += 1

        # Extract number from ID (e.g., "S5" -> 5)
        try:
            num = int("".join(filter(str.isdigit, str(row[id_col]))))
        except ValueError:
            num = grupo_counts[grupo]

        unique_ids.append(f"S{sum(grupo_counts.values())}")

    df["id_unico"] = unique_ids

    return df
