"""
Green Corridor Cartography Engine CLI

Usage:
    vv run --tramo tramo6 --axis eje.kmz --out outputs/
    vv chainage --axis eje.kmz --interval 500
    vv export-dxf --tramo tramo6 --layers axis sources disposal
    vv map --tramo tramo6 --dpi 300
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="vv",
    help="Green Corridor Cartography Engine - Colombian infrastructure corridor mapping"
)
console = Console()


@app.command()
def run(
    tramo: str = typer.Option(..., "--tramo", "-t", help="Corridor section identifier"),
    axis: Path = typer.Option(..., "--axis", "-a", help="Corridor axis KMZ file"),
    sources: Optional[Path] = typer.Option(None, "--sources", "-s", help="Material sources KMZ"),
    disposal: Optional[Path] = typer.Option(None, "--disposal", "-d", help="Disposal zones KMZ"),
    output: Path = typer.Option(Path("outputs"), "--out", "-o", help="Output directory"),
    radius: float = typer.Option(70000, "--radius", "-r", help="Search radius in meters"),
    interval: int = typer.Option(500, "--interval", "-i", help="Chainage interval in meters"),
    dpi: int = typer.Option(300, "--dpi", help="PNG export resolution"),
):
    """
    Run complete corridor processing pipeline.

    Generates: PNG map, DXF CAD files, CSV summaries.
    """
    from src.io_kmz import load_geodata
    from src.crs import ensure_crs
    from src.geometry import extract_single_line, get_centroids
    from src.annotate import annotate_to_axis, filter_by_radius
    from src.outputs_dxf import export_corridor_dxf
    from src.outputs_tables import export_summary_csv
    from src.outputs_maps import create_corridor_map, save_corridor_map
    from src.config import DEFAULT_CRS

    console.print(f"[bold blue]Processing corridor: {tramo}[/bold blue]")

    # Create output directory
    out_dir = output / f"salidas_{tramo}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load and process axis
    console.print("Loading axis...", style="dim")
    eje_gdf = load_geodata(axis)
    eje_gdf = ensure_crs(eje_gdf)
    eje_line = extract_single_line(eje_gdf)

    console.print(f"  Axis length: {eje_line.length/1000:.2f} km", style="green")

    # Process sources if provided
    sources_gdf = None
    sources_annotated = None
    if sources and sources.exists():
        console.print("Processing sources...", style="dim")
        sources_gdf = load_geodata(sources)
        sources_gdf = ensure_crs(sources_gdf)
        sources_cent = get_centroids(sources_gdf)
        sources_annotated = annotate_to_axis(sources_cent, eje_line)
        sources_annotated = filter_by_radius(sources_annotated, radius)
        console.print(f"  Sources within radius: {len(sources_annotated)}", style="green")

        # Export CSV
        export_summary_csv(sources_annotated, out_dir / "fuentes_resumen.csv")

    # Process disposal if provided
    disposal_gdf = None
    disposal_annotated = None
    if disposal and disposal.exists():
        console.print("Processing disposal zones...", style="dim")
        disposal_gdf = load_geodata(disposal)
        disposal_gdf = ensure_crs(disposal_gdf)
        disposal_cent = get_centroids(disposal_gdf)
        disposal_annotated = annotate_to_axis(disposal_cent, eje_line)
        disposal_annotated = filter_by_radius(disposal_annotated, radius)
        console.print(f"  Disposal zones within radius: {len(disposal_annotated)}", style="green")

        # Export CSV
        export_summary_csv(disposal_annotated, out_dir / "dispos_resumen.csv")

    # Export DXF files
    console.print("Exporting DXF files...", style="dim")
    dxf_outputs = export_corridor_dxf(
        out_dir, tramo, eje_line,
        sources_gdf, disposal_gdf,
        DEFAULT_CRS.calc_epsg
    )
    for layer, path in dxf_outputs.items():
        console.print(f"  {layer}: {path.name}", style="green")

    # Generate map
    console.print("Generating map...", style="dim")
    import geopandas as gpd
    axis_gdf_for_map = gpd.GeoDataFrame(
        {"name": [tramo]},
        geometry=[eje_line],
        crs=f"EPSG:{DEFAULT_CRS.calc_epsg}"
    )

    fig, ax = create_corridor_map(
        axis_gdf=axis_gdf_for_map,
        sources_gdf=sources_gdf,
        disposal_gdf=disposal_gdf,
        sources_annotated=sources_annotated,
        disposal_annotated=disposal_annotated,
        title=f"Localizaci\u00f3n de fuentes y zonas de disposici\u00f3n\nReferencia {tramo.capitalize()}",
        tramo=tramo,
        dpi=dpi
    )

    map_path = out_dir / f"plano_localizacion_{tramo}.png"
    save_corridor_map(fig, map_path, dpi=dpi)
    console.print(f"  Map saved: {map_path.name}", style="green")

    console.print(f"\n[bold green]Complete! Outputs in: {out_dir}[/bold green]")


@app.command()
def chainage(
    axis: Path = typer.Option(..., "--axis", "-a", help="Corridor axis KMZ file"),
    interval: int = typer.Option(500, "--interval", "-i", help="Interval in meters"),
    output: Optional[Path] = typer.Option(None, "--out", "-o", help="Output CSV file"),
):
    """
    Generate chainage points along corridor axis.
    """
    from src.io_kmz import load_geodata
    from src.crs import ensure_crs
    from src.geometry import extract_single_line
    from src.chainage import generate_chainage_points, format_chainage
    from src.config import DEFAULT_CRS

    console.print(f"[bold blue]Generating chainage points[/bold blue]")

    # Load axis
    eje_gdf = load_geodata(axis)
    eje_gdf = ensure_crs(eje_gdf)
    eje_line = extract_single_line(eje_gdf)

    total_length = eje_line.length
    console.print(f"Axis length: {total_length/1000:.2f} km")

    # Generate points
    points = generate_chainage_points(eje_line, interval)

    # Display table
    table = Table(title="Chainage Points")
    table.add_column("Abscisa", style="cyan")
    table.add_column("Distance (m)", justify="right")
    table.add_column("X", justify="right")
    table.add_column("Y", justify="right")

    for point, dist, label in points:
        table.add_row(label, f"{dist:.0f}", f"{point.x:.2f}", f"{point.y:.2f}")

    console.print(table)

    # Save if output specified
    if output:
        import pandas as pd
        df = pd.DataFrame([
            {"abscisa": label, "distancia_m": dist, "x": point.x, "y": point.y}
            for point, dist, label in points
        ])
        df.to_csv(output, index=False)
        console.print(f"\nSaved to: {output}", style="green")


@app.command("export-dxf")
def export_dxf(
    tramo: str = typer.Option(..., "--tramo", "-t", help="Corridor section identifier"),
    axis: Path = typer.Option(..., "--axis", "-a", help="Corridor axis KMZ file"),
    sources: Optional[Path] = typer.Option(None, "--sources", "-s", help="Material sources KMZ"),
    disposal: Optional[Path] = typer.Option(None, "--disposal", "-d", help="Disposal zones KMZ"),
    output: Path = typer.Option(Path("outputs"), "--out", "-o", help="Output directory"),
):
    """
    Export corridor layers to DXF CAD files.
    """
    from src.io_kmz import load_geodata
    from src.crs import ensure_crs
    from src.geometry import extract_single_line
    from src.outputs_dxf import export_corridor_dxf
    from src.config import DEFAULT_CRS

    console.print(f"[bold blue]Exporting DXF files for: {tramo}[/bold blue]")

    out_dir = output / f"salidas_{tramo}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load axis
    eje_gdf = load_geodata(axis)
    eje_gdf = ensure_crs(eje_gdf)
    eje_line = extract_single_line(eje_gdf)

    # Load optional layers
    sources_gdf = None
    if sources and sources.exists():
        sources_gdf = ensure_crs(load_geodata(sources))

    disposal_gdf = None
    if disposal and disposal.exists():
        disposal_gdf = ensure_crs(load_geodata(disposal))

    # Export
    outputs = export_corridor_dxf(
        out_dir, tramo, eje_line,
        sources_gdf, disposal_gdf,
        DEFAULT_CRS.calc_epsg
    )

    for layer, path in outputs.items():
        console.print(f"  [green]{layer}[/green]: {path}")

    console.print(f"\n[bold green]DXF export complete![/bold green]")


@app.command()
def info(
    axis: Path = typer.Option(..., "--axis", "-a", help="Corridor axis KMZ file"),
):
    """
    Display corridor information.
    """
    from src.io_kmz import load_geodata
    from src.crs import ensure_crs
    from src.geometry import extract_single_line
    from src.chainage import format_chainage

    eje_gdf = load_geodata(axis)
    eje_gdf = ensure_crs(eje_gdf)
    eje_line = extract_single_line(eje_gdf)

    bounds = eje_line.bounds

    console.print("[bold]Corridor Information[/bold]\n")
    console.print(f"Length: {eje_line.length/1000:.2f} km ({format_chainage(eje_line.length)})")
    console.print(f"CRS: EPSG:9377 (MAGNA-SIRGAS Colombia)")
    console.print(f"\nBounds:")
    console.print(f"  X: {bounds[0]:.2f} - {bounds[2]:.2f}")
    console.print(f"  Y: {bounds[1]:.2f} - {bounds[3]:.2f}")


@app.command()
def version():
    """Show version information."""
    from src import __version__
    console.print(f"Green Corridor Cartography Engine v{__version__}")


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
