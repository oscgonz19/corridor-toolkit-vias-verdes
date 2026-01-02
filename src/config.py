"""Configuration management with pydantic models."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class CRSConfig(BaseModel):
    """Coordinate Reference System configuration."""

    calc_epsg: int = Field(default=9377, description="EPSG for calculations (MAGNA-SIRGAS Colombia)")
    plot_epsg: int = Field(default=3857, description="EPSG for display (Web Mercator)")
    input_epsg: int = Field(default=4326, description="EPSG for input data (WGS84/GPS)")


class ChainageConfig(BaseModel):
    """Chainage (abscisas) configuration."""

    interval_m: int = Field(default=500, description="Chainage interval in meters")
    format_template: str = Field(default="K{km}+{rest:03d}", description="Chainage label format")


class FilterConfig(BaseModel):
    """Spatial filtering configuration."""

    radius_m: float = Field(default=70000, description="Search radius in meters")


class OutputConfig(BaseModel):
    """Output configuration."""

    output_dir: Path = Field(default=Path("outputs"), description="Output directory")
    dpi: int = Field(default=300, description="PNG export resolution")
    figure_size: tuple[int, int] = Field(default=(10, 10), description="Figure size in inches")


class CorridorConfig(BaseModel):
    """Complete corridor processing configuration."""

    tramo: str = Field(..., description="Corridor section identifier (e.g., 'tramo6')")
    axis_kmz: Path = Field(..., description="Path to corridor axis KMZ file")

    crs: CRSConfig = Field(default_factory=CRSConfig)
    chainage: ChainageConfig = Field(default_factory=ChainageConfig)
    filter: FilterConfig = Field(default_factory=FilterConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    # Optional feature layers
    sources_kmz: Optional[Path] = Field(default=None, description="Material sources KMZ")
    disposal_kmz: Optional[Path] = Field(default=None, description="Disposal zones KMZ")
    boreholes_csv: Optional[Path] = Field(default=None, description="Borehole data CSV")

    def get_output_dir(self) -> Path:
        """Get output directory for this tramo."""
        out = self.output.output_dir / f"salidas_{self.tramo}"
        out.mkdir(parents=True, exist_ok=True)
        return out


# Default configuration instance
DEFAULT_CRS = CRSConfig()
DEFAULT_CHAINAGE = ChainageConfig()
DEFAULT_FILTER = FilterConfig()
DEFAULT_OUTPUT = OutputConfig()
