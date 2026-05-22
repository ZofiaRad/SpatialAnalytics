trajectories_to_geojson.py
=========================

This small utility converts CSV files that contain X and Y pixel coordinates
into a GeoJSON FeatureCollection. It performs a 1:1 mapping: CSV X,Y become
GeoJSON coordinates [X, Y].

Quick examples
--------------

1) Points output (default):

   python trajectories_to_geojson.py example_trajectory.csv out_points.geojson

2) LineString per track (group by `track_id` column):

   python trajectories_to_geojson.py example_trajectory.csv out_lines.geojson --format lines --id track_id --ts timestamp

Options
-------

- --x / --y: column name (or index when --no-header) for X and Y
- --id: optional column name/index for track id grouping
- --ts: optional timestamp column used to sort points when building LineStrings
- --no-header: treat CSV as having no header (then use numeric indices for columns)
- --props-from-row: copy all CSV columns into properties for each Point feature

Notes
-----

This script does not perform coordinate reprojection. If you need to map
pixel coordinates to map coordinates (e.g., image->CRS transform), perform
the linear transform externally before or after running this script.
