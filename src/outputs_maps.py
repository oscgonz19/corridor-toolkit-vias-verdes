"""Cartographic map generation (PNG output)."""

import datetime as dt
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import MultipleLocator, StrMethodFormatter
import geopandas as gpd
from shapely.geometry import LineString

from .config import DEFAULT_CRS, DEFAULT_OUTPUT


def deg_to_dms(deg: float) -> tuple[int, int, float]:
    """
    Convert decimal degrees to degrees, minutes, seconds.

    Args:
        deg: Decimal degrees

    Returns:
        Tuple of (degrees, minutes, seconds)
    """
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return d, m, sd


def lat_formatter(lat: float, pos=None) -> str:
    """Format latitude for axis labels."""
    d, m, s = deg_to_dms(lat)
    return f"{abs(d)}\u00b0{m}'{int(s)}\"{'N' if lat >= 0 else 'S'}"


def lon_formatter(lon: float, pos=None) -> str:
    """Format longitude for axis labels."""
    d, m, s = deg_to_dms(lon)
    return f"{abs(d)}\u00b0{m}'{int(s)}\"{'E' if lon >= 0 else 'W'}"


def axis_point_on_plot(point, axis_line_plot: LineString):
    """Project a point onto the axis in plot CRS."""
    t = axis_line_plot.project(point)
    return axis_line_plot.interpolate(t)


def create_corridor_map(
    axis_gdf: gpd.GeoDataFrame,
    sources_gdf: Optional[gpd.GeoDataFrame] = None,
    disposal_gdf: Optional[gpd.GeoDataFrame] = None,
    sources_annotated: Optional[gpd.GeoDataFrame] = None,
    disposal_annotated: Optional[gpd.GeoDataFrame] = None,
    title: str = "Corridor Location Map",
    tramo: str = "tramo",
    calc_epsg: int = DEFAULT_CRS.calc_epsg,
    plot_epsg: int = DEFAULT_CRS.plot_epsg,
    figsize: tuple[int, int] = DEFAULT_OUTPUT.figure_size,
    dpi: int = DEFAULT_OUTPUT.dpi,
    add_basemap: bool = True,
    margin_m: float = 500,
    grid_interval_m: float = 5000,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Create a publication-ready corridor map.

    Args:
        axis_gdf: GeoDataFrame with corridor axis
        sources_gdf: Material sources (original geometry)
        disposal_gdf: Disposal zones (original geometry)
        sources_annotated: Annotated sources for labeling
        disposal_annotated: Annotated disposal for labeling
        title: Map title
        tramo: Corridor section identifier
        calc_epsg: Calculation CRS
        plot_epsg: Display CRS
        figsize: Figure size in inches
        dpi: Output resolution
        add_basemap: Add OpenStreetMap basemap
        margin_m: Margin around features in meters
        grid_interval_m: Coordinate grid interval

    Returns:
        Tuple of (figure, axes)
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_aspect("equal")

    # Reproject axis for plotting
    axis_plot = axis_gdf.to_crs(plot_epsg)
    axis_line_plot = axis_plot.geometry.iloc[0]

    # Calculate bounds
    bounds_list = [axis_plot.total_bounds]

    if sources_gdf is not None and len(sources_gdf) > 0:
        sources_plot = sources_gdf.to_crs(plot_epsg)
        bounds_list.append(sources_plot.total_bounds)
    else:
        sources_plot = None

    if disposal_gdf is not None and len(disposal_gdf) > 0:
        disposal_plot = disposal_gdf.to_crs(plot_epsg)
        bounds_list.append(disposal_plot.total_bounds)
    else:
        disposal_plot = None

    # Calculate extent
    import numpy as np
    all_bounds = np.array(bounds_list)
    xmin = all_bounds[:, 0].min() - margin_m
    ymin = all_bounds[:, 1].min() - margin_m
    xmax = all_bounds[:, 2].max() + margin_m
    ymax = all_bounds[:, 3].max() + margin_m

    # Make square
    xrange = xmax - xmin
    yrange = ymax - ymin
    side = max(xrange, yrange)
    xc = (xmin + xmax) / 2
    yc = (ymin + ymax) / 2

    ax.set_xlim(xc - side / 2, xc + side / 2)
    ax.set_ylim(yc - side / 2, yc + side / 2)

    # Plot layers
    axis_plot.plot(ax=ax, linewidth=2, color="C0", label=f"Eje {tramo.capitalize()}")

    if sources_plot is not None:
        sources_plot.plot(ax=ax, markersize=9, color="C1", alpha=0.9, label="Fuentes")

    if disposal_plot is not None:
        disposal_plot.plot(
            ax=ax, facecolor="none", edgecolor="red",
            linewidth=1.2, label="Zonas de disposici\u00f3n"
        )

    # Add basemap
    if add_basemap:
        try:
            import contextily as ctx
            ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, alpha=0.8)
        except Exception:
            pass  # Skip if contextily unavailable

    # Add annotations with reference lines
    if sources_annotated is not None and sources_plot is not None:
        for (_, row), geom in zip(sources_annotated.iterrows(), sources_plot.geometry):
            p_axis = axis_point_on_plot(geom.centroid if hasattr(geom, 'centroid') else geom, axis_line_plot)
            ax.plot([geom.centroid.x if hasattr(geom, 'centroid') else geom.x,
                     p_axis.x],
                    [geom.centroid.y if hasattr(geom, 'centroid') else geom.y,
                     p_axis.y],
                    linewidth=0.6, color="gray")
            pt = geom.centroid if hasattr(geom, 'centroid') else geom
            ax.annotate(
                f"{row['nombre']}\n{row['abscisa_lbl']} / {row['dist_m']/1000:.1f} km",
                xy=(pt.x, pt.y),
                xytext=(6, 6), textcoords="offset points",
                fontsize=7,
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="none")
            )

    if disposal_annotated is not None and disposal_plot is not None:
        for (_, row), geom in zip(disposal_annotated.iterrows(), disposal_plot.geometry):
            p_axis = axis_point_on_plot(geom.centroid, axis_line_plot)
            ax.plot([geom.centroid.x, p_axis.x],
                    [geom.centroid.y, p_axis.y],
                    linewidth=0.6, color="gray")
            ax.annotate(
                f"{row['nombre']}\n{row['abscisa_lbl']} / {row['dist_m']/1000:.1f} km",
                xy=(geom.centroid.x, geom.centroid.y),
                xytext=(6, 6), textcoords="offset points",
                fontsize=7,
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="none")
            )

    # Legend
    handles = [
        Line2D([0], [0], color="C0", lw=2, label=f"Eje {tramo.capitalize()}"),
    ]
    if sources_plot is not None:
        handles.append(Line2D([0], [0], marker="o", linestyle="", color="C1", label="Fuentes"))
    if disposal_plot is not None:
        handles.append(Patch(facecolor="none", edgecolor="red", label="Zonas de disposici\u00f3n"))
    ax.legend(handles=handles, loc="lower left", fontsize=8, frameon=True, framealpha=0.95)

    # North arrow
    ax.annotate(
        "N", xy=(0.965, 0.96), xytext=(0.965, 0.86),
        xycoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", lw=1.5),
        ha="center", va="center",
        bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.2"),
        fontsize=10
    )

    # Scale bar
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    sc = 1000  # 1 km
    x0 = xlim[0] + 0.02 * (xlim[1] - xlim[0])
    y0 = ylim[0] + 0.045 * (ylim[1] - ylim[0])
    ax.plot([x0, x0 + sc], [y0, y0], color="black", lw=2)
    ax.text(x0 + sc / 2, y0 - 0.02 * (ylim[1] - ylim[0]), f"{int(sc/1000)} km",
            ha="center", va="top", fontsize=8)

    # Coordinate grid
    ax.xaxis.set_major_locator(MultipleLocator(grid_interval_m))
    ax.yaxis.set_major_locator(MultipleLocator(grid_interval_m))
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
    ax.grid(which="major", alpha=0.10, lw=0.3)

    # Neatline (border frame)
    ax.add_patch(Rectangle(
        (xlim[0], ylim[0]), xlim[1] - xlim[0], ylim[1] - ylim[0],
        fill=False, lw=0.8, edgecolor="black", zorder=10
    ))

    # Footer
    fig.text(
        0.01, 0.01,
        f"CRS de c\u00e1lculo: EPSG:{calc_epsg} (MAGNA-SIRGAS) | CRS de dibujo: EPSG:{plot_epsg} (Web-Mercator)\n"
        f"Fuente de fondo: OpenStreetMap/Mapnik | Fecha: {dt.date.today():%Y-%m-%d}",
        ha="left", va="bottom", fontsize=7
    )

    # Coordinate bounds box
    ax.text(
        0.99, 0.01,
        f"Xmin={xlim[0]:,.0f}  Xmax={xlim[1]:,.0f}\nYmin={ylim[0]:,.0f}  Ymax={ylim[1]:,.0f}",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=7,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="none")
    )

    # Title
    ax.set_title(title, fontsize=9, ha="center", pad=10)
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")

    return fig, ax


def save_corridor_map(
    fig: plt.Figure,
    output_path: str | Path,
    dpi: int = DEFAULT_OUTPUT.dpi
) -> None:
    """
    Save corridor map to PNG file.

    Args:
        fig: Matplotlib figure
        output_path: Output PNG path
        dpi: Resolution
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
