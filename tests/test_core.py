"""
Comprehensive tests for Vías Verdes core modules.

Test Coverage:
    - chainage: format_chainage, parse_chainage, chainage, generate_chainage_points
    - annotate: annotate_to_axis, filter_by_radius, sort_by_chainage
    - crs: ensure_crs, reproject, validate_projected_crs, get_crs_info
    - geometry: to_single_line, extract_single_line, get_centroids, project_point_to_line

Run with: pytest tests/test_core.py -v
"""

import pytest
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import LineString, Point, Polygon, MultiLineString

from src.chainage import (
    format_chainage,
    parse_chainage,
    chainage,
    generate_chainage_points,
    chainage_points_to_gdf,
)
from src.annotate import annotate_to_axis, filter_by_radius, sort_by_chainage
from src.crs import ensure_crs, reproject, validate_projected_crs, get_crs_info
from src.geometry import (
    to_single_line,
    extract_single_line,
    get_centroids,
    project_point_to_line,
    perpendicular_distance,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def simple_axis():
    """10km horizontal line for testing."""
    return LineString([(0, 0), (10000, 0)])


@pytest.fixture
def curved_axis():
    """Curved line simulating real corridor."""
    coords = [
        (0, 0),
        (2000, 500),
        (4000, 200),
        (6000, 800),
        (8000, 400),
        (10000, 600),
    ]
    return LineString(coords)


@pytest.fixture
def sample_points_gdf():
    """Sample point GeoDataFrame for testing."""
    return gpd.GeoDataFrame(
        {
            "Name": ["Point A", "Point B", "Point C"],
            "type": ["source", "disposal", "borehole"],
        },
        geometry=[
            Point(5000, 100),
            Point(7500, -200),
            Point(2500, 50),
        ],
        crs="EPSG:9377",
    )


@pytest.fixture
def sample_polygons_gdf():
    """Sample polygon GeoDataFrame for testing."""
    poly1 = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    poly2 = Polygon([(500, 500), (600, 500), (600, 600), (500, 600)])
    return gpd.GeoDataFrame(
        {"Name": ["Zone A", "Zone B"]},
        geometry=[poly1, poly2],
        crs="EPSG:9377",
    )


# =============================================================================
# TestChainage: Tests for chainage.py
# =============================================================================

class TestChainage:
    """Tests for chainage calculations and formatting."""

    # -------------------------------------------------------------------------
    # format_chainage tests
    # -------------------------------------------------------------------------

    def test_format_chainage_zero(self):
        """Test formatting of zero distance."""
        assert format_chainage(0) == "K0+000"

    def test_format_chainage_under_one_km(self):
        """Test formatting of sub-kilometer distances."""
        assert format_chainage(500) == "K0+500"
        assert format_chainage(999) == "K0+999"
        assert format_chainage(1) == "K0+001"

    def test_format_chainage_exact_km(self):
        """Test formatting of exact kilometer values."""
        assert format_chainage(1000) == "K1+000"
        assert format_chainage(5000) == "K5+000"
        assert format_chainage(10000) == "K10+000"

    def test_format_chainage_mixed(self):
        """Test formatting of mixed km+m values."""
        assert format_chainage(5250) == "K5+250"
        assert format_chainage(11795) == "K11+795"
        assert format_chainage(1001) == "K1+001"

    def test_format_chainage_rounding_down(self):
        """Test rounding down for values < 0.5."""
        assert format_chainage(5250.4) == "K5+250"
        assert format_chainage(5250.49) == "K5+250"

    def test_format_chainage_rounding_up(self):
        """Test rounding up for values >= 0.5."""
        assert format_chainage(5250.5) == "K5+251"
        assert format_chainage(5250.9) == "K5+251"

    def test_format_chainage_large_values(self):
        """Test formatting of large corridor lengths."""
        assert format_chainage(99999) == "K99+999"
        assert format_chainage(150000) == "K150+000"

    # -------------------------------------------------------------------------
    # parse_chainage tests
    # -------------------------------------------------------------------------

    def test_parse_chainage_basic(self):
        """Test basic chainage parsing."""
        assert parse_chainage("K0+000") == 0.0
        assert parse_chainage("K5+250") == 5250.0
        assert parse_chainage("K11+795") == 11795.0

    def test_parse_chainage_case_insensitive(self):
        """Test that parsing is case-insensitive."""
        assert parse_chainage("k5+250") == 5250.0
        assert parse_chainage("K5+250") == 5250.0

    def test_parse_chainage_roundtrip(self):
        """Test format -> parse -> format roundtrip."""
        for meters in [0, 500, 1000, 5250, 11795, 99999]:
            label = format_chainage(meters)
            parsed = parse_chainage(label)
            assert parsed == float(meters)

    def test_parse_chainage_invalid_format(self):
        """Test that invalid formats raise ValueError."""
        with pytest.raises(ValueError):
            parse_chainage("invalid")
        with pytest.raises(ValueError):
            parse_chainage("5+250")  # Missing K
        with pytest.raises(ValueError):
            parse_chainage("K5")  # Missing +meters

    # -------------------------------------------------------------------------
    # chainage function tests
    # -------------------------------------------------------------------------

    def test_chainage_point_on_line(self, simple_axis):
        """Test chainage for point exactly on line."""
        point = Point(5000, 0)
        dist, label = chainage(simple_axis, point)

        assert dist == 5000.0
        assert label == "K5+000"

    def test_chainage_point_off_line(self, simple_axis):
        """Test chainage for point perpendicular to line."""
        point = Point(5000, 100)  # 100m north of axis
        dist, label = chainage(simple_axis, point)

        assert dist == 5000.0  # Projects to K5+000
        assert label == "K5+000"

    def test_chainage_at_start(self, simple_axis):
        """Test chainage at line start."""
        point = Point(0, 0)
        dist, label = chainage(simple_axis, point)

        assert dist == 0.0
        assert label == "K0+000"

    def test_chainage_at_end(self, simple_axis):
        """Test chainage at line end."""
        point = Point(10000, 0)
        dist, label = chainage(simple_axis, point)

        assert dist == 10000.0
        assert label == "K10+000"

    def test_chainage_beyond_start(self, simple_axis):
        """Test chainage for point before line start."""
        point = Point(-100, 0)
        dist, label = chainage(simple_axis, point)

        assert dist == 0.0  # Clamps to start
        assert label == "K0+000"

    def test_chainage_beyond_end(self, simple_axis):
        """Test chainage for point after line end."""
        point = Point(10100, 0)
        dist, label = chainage(simple_axis, point)

        assert dist == 10000.0  # Clamps to end
        assert label == "K10+000"

    # -------------------------------------------------------------------------
    # generate_chainage_points tests
    # -------------------------------------------------------------------------

    def test_generate_chainage_points_basic(self, simple_axis):
        """Test basic chainage point generation."""
        points = generate_chainage_points(simple_axis, interval_m=500)

        # 10km / 500m = 20 intervals + start point = 21 points
        assert len(points) == 21
        assert points[0][2] == "K0+000"
        assert points[-1][2] == "K10+000"

    def test_generate_chainage_points_interval(self):
        """Test different interval sizes."""
        line = LineString([(0, 0), (2500, 0)])

        points_500 = generate_chainage_points(line, interval_m=500)
        points_1000 = generate_chainage_points(line, interval_m=1000)

        assert len(points_500) == 6  # K0+000 to K2+500
        assert len(points_1000) == 3  # K0+000, K1+000, K2+000

    def test_generate_chainage_points_with_start_offset(self):
        """Test chainage generation with start offset."""
        line = LineString([(0, 0), (2000, 0)])
        points = generate_chainage_points(line, interval_m=500, start_m=1000)

        assert points[0][2] == "K1+000"
        assert points[-1][2] == "K2+000"

    def test_generate_chainage_points_geometry(self, simple_axis):
        """Test that generated points are on the line."""
        points = generate_chainage_points(simple_axis, interval_m=1000)

        for point, dist_m, label in points:
            assert isinstance(point, Point)
            # Point should be on or very close to line
            assert simple_axis.distance(point) < 0.001

    # -------------------------------------------------------------------------
    # chainage_points_to_gdf tests
    # -------------------------------------------------------------------------

    def test_chainage_points_to_gdf(self, simple_axis):
        """Test conversion of chainage points to GeoDataFrame."""
        points = generate_chainage_points(simple_axis, interval_m=1000)
        gdf = chainage_points_to_gdf(points, crs=9377)

        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == len(points)
        assert "abscisa_m" in gdf.columns
        assert "abscisa_lbl" in gdf.columns
        assert gdf.crs.to_epsg() == 9377

    def test_chainage_points_to_gdf_string_crs(self, simple_axis):
        """Test with string CRS specification."""
        points = generate_chainage_points(simple_axis, interval_m=1000)
        gdf = chainage_points_to_gdf(points, crs="EPSG:9377")

        assert gdf.crs is not None


# =============================================================================
# TestAnnotate: Tests for annotate.py
# =============================================================================

class TestAnnotate:
    """Tests for annotation functions."""

    # -------------------------------------------------------------------------
    # annotate_to_axis tests
    # -------------------------------------------------------------------------

    def test_annotate_to_axis_basic(self, simple_axis, sample_points_gdf):
        """Test basic point annotation."""
        result = annotate_to_axis(sample_points_gdf, simple_axis, name_field="Name")

        assert len(result) == 3
        assert "dist_m" in result.columns
        assert "abscisa_m" in result.columns
        assert "abscisa_lbl" in result.columns
        assert "nombre" in result.columns
        assert "x" in result.columns
        assert "y" in result.columns
        assert "x_axis" in result.columns
        assert "y_axis" in result.columns

    def test_annotate_to_axis_chainage_values(self, simple_axis):
        """Test that chainage values are correct."""
        points = gpd.GeoDataFrame(
            {"Name": ["Test"]},
            geometry=[Point(5000, 100)],
            crs="EPSG:9377",
        )

        result = annotate_to_axis(points, simple_axis, name_field="Name")

        assert result.iloc[0]["abscisa_lbl"] == "K5+000"
        assert result.iloc[0]["abscisa_m"] == 5000.0

    def test_annotate_to_axis_offset_values(self, simple_axis):
        """Test that offset distances are correct."""
        points = gpd.GeoDataFrame(
            {"Name": ["Near", "Far"]},
            geometry=[Point(5000, 100), Point(5000, 500)],
            crs="EPSG:9377",
        )

        result = annotate_to_axis(points, simple_axis, name_field="Name")

        assert abs(result.iloc[0]["dist_m"] - 100) < 1
        assert abs(result.iloc[1]["dist_m"] - 500) < 1

    def test_annotate_to_axis_preserves_coordinates(self, simple_axis):
        """Test that original coordinates are preserved."""
        point = Point(5000, 100)
        points = gpd.GeoDataFrame(
            {"Name": ["Test"]},
            geometry=[point],
            crs="EPSG:9377",
        )

        result = annotate_to_axis(points, simple_axis)

        assert result.iloc[0]["x"] == 5000
        assert result.iloc[0]["y"] == 100

    def test_annotate_to_axis_missing_name_field(self, simple_axis):
        """Test handling of missing name field."""
        points = gpd.GeoDataFrame(
            {"other_field": ["value"]},
            geometry=[Point(5000, 100)],
            crs="EPSG:9377",
        )

        result = annotate_to_axis(points, simple_axis, name_field="Name")

        assert result.iloc[0]["nombre"] == "sin_nombre"

    def test_annotate_to_axis_null_names(self, simple_axis):
        """Test handling of null/NaN names."""
        points = gpd.GeoDataFrame(
            {"Name": [None, np.nan, "Valid"]},
            geometry=[Point(2000, 0), Point(5000, 0), Point(8000, 0)],
            crs="EPSG:9377",
        )

        result = annotate_to_axis(points, simple_axis, name_field="Name")

        assert result.iloc[0]["nombre"] == "sin_nombre"
        assert result.iloc[1]["nombre"] == "sin_nombre"
        assert result.iloc[2]["nombre"] == "Valid"

    def test_annotate_to_axis_geometry_axis(self, simple_axis):
        """Test that geometry_axis column is created."""
        points = gpd.GeoDataFrame(
            {"Name": ["Test"]},
            geometry=[Point(5000, 100)],
            crs="EPSG:9377",
        )

        result = annotate_to_axis(points, simple_axis)

        assert "geometry_axis" in result.columns
        projected = result.iloc[0]["geometry_axis"]
        assert isinstance(projected, Point)
        assert projected.y == 0  # Should be on the horizontal axis

    # -------------------------------------------------------------------------
    # filter_by_radius tests
    # -------------------------------------------------------------------------

    def test_filter_by_radius_basic(self, simple_axis):
        """Test basic radius filtering."""
        points = gpd.GeoDataFrame(
            {"Name": ["Close", "Far"]},
            geometry=[Point(5000, 100), Point(5000, 5000)],
            crs="EPSG:9377",
        )

        annotated = annotate_to_axis(points, simple_axis)
        filtered = filter_by_radius(annotated, radius_m=1000)

        assert len(filtered) == 1
        assert filtered.iloc[0]["nombre"] == "Close"

    def test_filter_by_radius_boundary(self, simple_axis):
        """Test filtering at exact boundary."""
        points = gpd.GeoDataFrame(
            {"Name": ["AtBoundary", "JustOver"]},
            geometry=[Point(5000, 1000), Point(5000, 1001)],
            crs="EPSG:9377",
        )

        annotated = annotate_to_axis(points, simple_axis)
        filtered = filter_by_radius(annotated, radius_m=1000)

        assert len(filtered) == 1

    def test_filter_by_radius_all_pass(self, simple_axis):
        """Test when all points pass filter."""
        points = gpd.GeoDataFrame(
            {"Name": ["A", "B", "C"]},
            geometry=[Point(2000, 50), Point(5000, 100), Point(8000, 200)],
            crs="EPSG:9377",
        )

        annotated = annotate_to_axis(points, simple_axis)
        filtered = filter_by_radius(annotated, radius_m=10000)

        assert len(filtered) == 3

    def test_filter_by_radius_none_pass(self, simple_axis):
        """Test when no points pass filter."""
        points = gpd.GeoDataFrame(
            {"Name": ["Far1", "Far2"]},
            geometry=[Point(5000, 5000), Point(5000, 6000)],
            crs="EPSG:9377",
        )

        annotated = annotate_to_axis(points, simple_axis)
        filtered = filter_by_radius(annotated, radius_m=100)

        assert len(filtered) == 0

    def test_filter_by_radius_returns_copy(self, simple_axis):
        """Test that filter returns a copy, not a view."""
        points = gpd.GeoDataFrame(
            {"Name": ["Test"]},
            geometry=[Point(5000, 100)],
            crs="EPSG:9377",
        )

        annotated = annotate_to_axis(points, simple_axis)
        filtered = filter_by_radius(annotated, radius_m=1000)

        # Modifying filtered should not affect original
        filtered.loc[filtered.index[0], "nombre"] = "Modified"
        assert annotated.iloc[0]["nombre"] != "Modified"

    # -------------------------------------------------------------------------
    # sort_by_chainage tests
    # -------------------------------------------------------------------------

    def test_sort_by_chainage_basic(self, simple_axis):
        """Test basic chainage sorting."""
        points = gpd.GeoDataFrame(
            {"Name": ["Last", "First", "Middle"]},
            geometry=[Point(8000, 0), Point(2000, 0), Point(5000, 0)],
            crs="EPSG:9377",
        )

        annotated = annotate_to_axis(points, simple_axis)
        sorted_gdf = sort_by_chainage(annotated)

        assert sorted_gdf.iloc[0]["nombre"] == "First"
        assert sorted_gdf.iloc[1]["nombre"] == "Middle"
        assert sorted_gdf.iloc[2]["nombre"] == "Last"

    def test_sort_by_chainage_resets_index(self, simple_axis):
        """Test that index is reset after sorting."""
        points = gpd.GeoDataFrame(
            {"Name": ["B", "A"]},
            geometry=[Point(8000, 0), Point(2000, 0)],
            crs="EPSG:9377",
        )

        annotated = annotate_to_axis(points, simple_axis)
        sorted_gdf = sort_by_chainage(annotated)

        assert list(sorted_gdf.index) == [0, 1]


# =============================================================================
# TestCRS: Tests for crs.py
# =============================================================================

class TestCRS:
    """Tests for CRS functions."""

    # -------------------------------------------------------------------------
    # ensure_crs tests
    # -------------------------------------------------------------------------

    def test_ensure_crs_none_input(self):
        """Test CRS assignment when input has no CRS."""
        gdf = gpd.GeoDataFrame(
            {"name": ["test"]},
            geometry=[Point(0, 0)],
        )
        gdf.crs = None

        result = ensure_crs(gdf, target_epsg=9377, assume_input_epsg=4326)

        assert result.crs is not None
        assert result.crs.to_epsg() == 9377

    def test_ensure_crs_transform(self):
        """Test CRS transformation from 4326 to 9377."""
        gdf = gpd.GeoDataFrame(
            {"name": ["test"]},
            geometry=[Point(-75.5, 4.5)],  # Lon/lat in Colombia
            crs="EPSG:4326",
        )

        result = ensure_crs(gdf, target_epsg=9377)

        assert result.crs.to_epsg() == 9377
        # Coordinates should be transformed (projected)
        assert result.geometry.iloc[0].x != -75.5

    def test_ensure_crs_no_transform_needed(self):
        """Test when already in target CRS."""
        gdf = gpd.GeoDataFrame(
            {"name": ["test"]},
            geometry=[Point(1000000, 1000000)],
            crs="EPSG:9377",
        )

        result = ensure_crs(gdf, target_epsg=9377)

        assert result.crs.to_epsg() == 9377
        assert result.geometry.iloc[0].x == 1000000

    def test_ensure_crs_default_assumption(self):
        """Test default WGS84 assumption for missing CRS."""
        gdf = gpd.GeoDataFrame(
            {"name": ["test"]},
            geometry=[Point(-75.5, 4.5)],
        )
        gdf.crs = None

        # Default assume_input_epsg is 4326
        result = ensure_crs(gdf, target_epsg=9377)

        assert result.crs.to_epsg() == 9377

    # -------------------------------------------------------------------------
    # reproject tests
    # -------------------------------------------------------------------------

    def test_reproject_basic(self):
        """Test basic reprojection."""
        gdf = gpd.GeoDataFrame(
            {"name": ["test"]},
            geometry=[Point(1000000, 1000000)],
            crs="EPSG:9377",
        )

        result = reproject(gdf, target_epsg=3857)

        assert result.crs.to_epsg() == 3857

    def test_reproject_no_crs_raises(self):
        """Test that reprojection without CRS raises ValueError."""
        gdf = gpd.GeoDataFrame(
            {"name": ["test"]},
            geometry=[Point(0, 0)],
        )
        gdf.crs = None

        with pytest.raises(ValueError):
            reproject(gdf, target_epsg=9377)

    # -------------------------------------------------------------------------
    # validate_projected_crs tests
    # -------------------------------------------------------------------------

    def test_validate_projected_crs_true(self):
        """Test validation of projected CRS."""
        gdf = gpd.GeoDataFrame(
            {"name": ["test"]},
            geometry=[Point(1000000, 1000000)],
            crs="EPSG:9377",
        )

        assert validate_projected_crs(gdf) is True

    def test_validate_projected_crs_false_geographic(self):
        """Test validation of geographic CRS returns False."""
        gdf = gpd.GeoDataFrame(
            {"name": ["test"]},
            geometry=[Point(-75.5, 4.5)],
            crs="EPSG:4326",
        )

        assert validate_projected_crs(gdf) is False

    def test_validate_projected_crs_false_no_crs(self):
        """Test validation with no CRS returns False."""
        gdf = gpd.GeoDataFrame(
            {"name": ["test"]},
            geometry=[Point(0, 0)],
        )
        gdf.crs = None

        assert validate_projected_crs(gdf) is False

    # -------------------------------------------------------------------------
    # get_crs_info tests
    # -------------------------------------------------------------------------

    def test_get_crs_info_known(self):
        """Test CRS info for known EPSG codes."""
        info_9377 = get_crs_info(9377)
        assert info_9377["epsg"] == 9377
        assert "MAGNA" in info_9377["name"]
        assert info_9377["units"] == "meters"

        info_4326 = get_crs_info(4326)
        assert info_4326["units"] == "degrees"

    def test_get_crs_info_unknown(self):
        """Test CRS info for unknown EPSG code."""
        info = get_crs_info(99999)
        assert info["epsg"] == 99999
        assert info["units"] == "unknown"


# =============================================================================
# TestGeometry: Tests for geometry.py
# =============================================================================

class TestGeometry:
    """Tests for geometry functions."""

    # -------------------------------------------------------------------------
    # to_single_line tests
    # -------------------------------------------------------------------------

    def test_to_single_line_linestring(self):
        """Test that LineString passes through unchanged."""
        line = LineString([(0, 0), (1, 1), (2, 0)])
        result = to_single_line(line)

        assert result.geom_type == "LineString"
        assert len(list(result.coords)) == 3

    def test_to_single_line_multilinestring_connected(self):
        """Test MultiLineString conversion when segments are connected."""
        multi = MultiLineString([
            [(0, 0), (1, 1)],
            [(1, 1), (2, 0)],
        ])

        result = to_single_line(multi)

        assert result.geom_type == "LineString"
        # Should merge to 3 coordinates (endpoints shared)
        assert len(list(result.coords)) == 3

    def test_to_single_line_multilinestring_disconnected(self):
        """Test MultiLineString conversion when segments are disconnected."""
        multi = MultiLineString([
            [(0, 0), (1, 1)],
            [(2, 2), (3, 3)],  # Gap between segments
        ])

        result = to_single_line(multi)

        assert result.geom_type == "LineString"
        # Fallback concatenates all coordinates
        assert len(list(result.coords)) == 4

    def test_to_single_line_invalid_type(self):
        """Test that invalid geometry type raises TypeError."""
        with pytest.raises(TypeError):
            to_single_line(Point(0, 0))

        with pytest.raises(TypeError):
            to_single_line(Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]))

    # -------------------------------------------------------------------------
    # extract_single_line tests
    # -------------------------------------------------------------------------

    def test_extract_single_line_basic(self):
        """Test extraction from single-row GeoDataFrame."""
        line = LineString([(0, 0), (100, 100)])
        gdf = gpd.GeoDataFrame(
            {"name": ["axis"]},
            geometry=[line],
            crs="EPSG:9377",
        )

        result = extract_single_line(gdf)

        assert isinstance(result, LineString)
        assert result.length == line.length

    def test_extract_single_line_multilinestring(self):
        """Test extraction from GeoDataFrame with MultiLineString."""
        multi = MultiLineString([
            [(0, 0), (1, 1)],
            [(1, 1), (2, 0)],
        ])
        gdf = gpd.GeoDataFrame(
            {"name": ["axis"]},
            geometry=[multi],
            crs="EPSG:9377",
        )

        result = extract_single_line(gdf)

        assert result.geom_type == "LineString"

    def test_extract_single_line_empty_gdf(self):
        """Test that empty GeoDataFrame raises IndexError."""
        gdf = gpd.GeoDataFrame(columns=["name", "geometry"])

        with pytest.raises(IndexError):
            extract_single_line(gdf)

    def test_extract_single_line_uses_first_row(self):
        """Test that first row is used when multiple rows exist."""
        gdf = gpd.GeoDataFrame(
            {"name": ["first", "second"]},
            geometry=[
                LineString([(0, 0), (100, 0)]),
                LineString([(0, 0), (200, 0)]),
            ],
            crs="EPSG:9377",
        )

        result = extract_single_line(gdf)

        assert result.length == 100  # First line, not second

    # -------------------------------------------------------------------------
    # get_centroids tests
    # -------------------------------------------------------------------------

    def test_get_centroids_points(self):
        """Test centroids of points (should be unchanged)."""
        gdf = gpd.GeoDataFrame(
            {"name": ["A", "B"]},
            geometry=[Point(100, 100), Point(200, 200)],
            crs="EPSG:9377",
        )

        result = get_centroids(gdf)

        assert result.geometry.iloc[0].equals(Point(100, 100))
        assert result.geometry.iloc[1].equals(Point(200, 200))

    def test_get_centroids_polygons(self, sample_polygons_gdf):
        """Test centroids of polygons."""
        result = get_centroids(sample_polygons_gdf)

        # Centroids should be Point geometries
        assert all(result.geometry.geom_type == "Point")
        # Original geometries should be preserved
        assert "geom_ori" in result.columns
        assert result["geom_ori"].iloc[0].geom_type == "Polygon"

    def test_get_centroids_preserves_data(self, sample_polygons_gdf):
        """Test that original data columns are preserved."""
        result = get_centroids(sample_polygons_gdf)

        assert "Name" in result.columns
        assert result["Name"].iloc[0] == "Zone A"

    def test_get_centroids_returns_copy(self, sample_polygons_gdf):
        """Test that get_centroids returns a copy."""
        result = get_centroids(sample_polygons_gdf)

        result["Name"] = ["Modified A", "Modified B"]
        assert sample_polygons_gdf["Name"].iloc[0] == "Zone A"

    # -------------------------------------------------------------------------
    # project_point_to_line tests
    # -------------------------------------------------------------------------

    def test_project_point_to_line_on_line(self, simple_axis):
        """Test projection of point on line."""
        point = Point(5000, 0)
        projected, dist_along = project_point_to_line(point, simple_axis)

        assert projected.x == 5000.0
        assert projected.y == 0.0
        assert dist_along == 5000.0

    def test_project_point_to_line_perpendicular(self, simple_axis):
        """Test projection of point perpendicular to line."""
        point = Point(5000, 300)
        projected, dist_along = project_point_to_line(point, simple_axis)

        assert projected.x == 5000.0
        assert projected.y == 0.0
        assert dist_along == 5000.0

    def test_project_point_to_line_diagonal(self):
        """Test projection onto diagonal line."""
        line = LineString([(0, 0), (10, 10)])
        point = Point(5, 0)  # Below the diagonal

        projected, dist_along = project_point_to_line(point, line)

        # Should project to midpoint of diagonal
        assert abs(projected.x - 2.5) < 0.001
        assert abs(projected.y - 2.5) < 0.001

    # -------------------------------------------------------------------------
    # perpendicular_distance tests
    # -------------------------------------------------------------------------

    def test_perpendicular_distance_on_line(self, simple_axis):
        """Test distance for point on line is zero."""
        point = Point(5000, 0)
        dist = perpendicular_distance(point, simple_axis)

        assert dist == 0.0

    def test_perpendicular_distance_perpendicular(self, simple_axis):
        """Test perpendicular distance."""
        point = Point(5000, 100)
        dist = perpendicular_distance(point, simple_axis)

        assert dist == 100.0

    def test_perpendicular_distance_negative_y(self, simple_axis):
        """Test distance is absolute (always positive)."""
        point = Point(5000, -100)
        dist = perpendicular_distance(point, simple_axis)

        assert dist == 100.0  # Positive, not -100


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple modules."""

    def test_full_annotation_workflow(self, simple_axis, sample_points_gdf):
        """Test complete annotation workflow."""
        # Annotate
        annotated = annotate_to_axis(sample_points_gdf, simple_axis, name_field="Name")

        # Filter
        filtered = filter_by_radius(annotated, radius_m=500)

        # Sort
        sorted_gdf = sort_by_chainage(filtered)

        # Validate
        assert len(sorted_gdf) <= len(sample_points_gdf)
        if len(sorted_gdf) > 1:
            # Should be sorted by chainage
            assert sorted_gdf["abscisa_m"].is_monotonic_increasing

    def test_chainage_markers_workflow(self, simple_axis):
        """Test complete chainage marker generation."""
        # Generate markers
        markers = generate_chainage_points(simple_axis, interval_m=1000)

        # Convert to GDF
        markers_gdf = chainage_points_to_gdf(markers, crs=9377)

        # Validate
        assert len(markers_gdf) == 11  # K0+000 to K10+000
        assert markers_gdf.crs.to_epsg() == 9377
        assert markers_gdf["abscisa_lbl"].iloc[0] == "K0+000"
        assert markers_gdf["abscisa_lbl"].iloc[-1] == "K10+000"

    def test_polygon_centroid_annotation(self, simple_axis, sample_polygons_gdf):
        """Test annotation of polygon features via centroids."""
        # Get centroids
        centroids = get_centroids(sample_polygons_gdf)

        # Annotate
        annotated = annotate_to_axis(centroids, simple_axis, name_field="Name")

        # Validate
        assert len(annotated) == 2
        assert "abscisa_lbl" in annotated.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
