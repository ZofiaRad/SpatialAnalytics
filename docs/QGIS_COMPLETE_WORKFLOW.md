# QGIS complete workflow (all objects + rooms)

This workflow uses the full conversion scripts to include **all spatial objects** (walls, doors, stairs, windows, circles, etc.) and preserve painting associations.

Scripts:

- `scripts/json_to_geojson_full.py`
- `scripts/geojson_to_json_full.py`

Repository root:

`<repository-root>`

## 1) Export full multi-object GeoJSON per floor

```bash
python scripts/json_to_geojson_full.py \
  --input-json data/NMFA_3floors_plan.json \
  --output-dir data
```

Generated files:

- `data/floor_0_all_objects.geojson`
- `data/floor_1_all_objects.geojson`
- `data/floor_2_all_objects.geojson`
- `data/geojson_conversion_report.json`

Each feature stores:

- `properties.id`
- `properties.object_type`
- `properties.floor`
- `properties.original_data` (full original object payload)
- `properties.paintings` (walls keep painting arrays, including partial entries)
- `properties.wall_id_reference` (for wall-linked paintings)

## 2) Import all-object GeoJSON into QGIS

1. Open QGIS and create a new project.
2. **Layer → Add Layer → Add Vector Layer**.
3. Load one or more `floor_*_all_objects.geojson` files.
4. Verify objects appear as line/point features.

## 3) Style by object type

1. Right-click layer → **Properties → Symbology**.
2. Set renderer to **Categorized**.
3. Categorize by `object_type`.
4. Assign distinct colors/symbols (example):
   - wall: dark gray line
   - door: orange line
   - window: blue line
   - stair: purple line
   - circle: green symbol/line

This makes walls and background objects easy to use as tracing guides.

## 4) Digitize room polygons using existing objects as guides

1. Create a new polygon layer:
   - **Layer → Create Layer → New GeoPackage Layer** (or GeoJSON)
   - Geometry: **Polygon**
   - Fields: `id` (text), `name` (text), `floor` (integer), `object_type` (text)
2. Enable snapping:
   - **Project → Snapping Options**
   - Enable snapping to the all-object layer (vertex + segment)
3. Toggle editing on the room layer.
4. Draw each room polygon using walls/doors/other objects as references.
5. Set attributes for each room:
   - `id`: e.g. `F0_R01`
   - `name`: e.g. `Gallery A`
   - `floor`: `0`, `1`, or `2`
   - `object_type`: `room`
6. Save edits.

## 5) Export edited features from QGIS

Export all edited layers (including new rooms) as GeoJSON files, for example:

- `data/floor_0_all_objects_edited.geojson`
- `data/floor_1_all_objects_edited.geojson`
- `data/floor_2_all_objects_edited.geojson`

If rooms are in separate files, that is also supported.

## 6) Convert GeoJSON back to full JSON

```bash
python scripts/geojson_to_json_full.py \
  --input-json data/NMFA_3floors_plan.json \
  --geojson-files \
    data/floor_0_all_objects_edited.geojson \
    data/floor_1_all_objects_edited.geojson \
    data/floor_2_all_objects_edited.geojson \
  --output-json data/NMFA_3floors_plan_updated.json
```

Behavior:

- Rebuilds floor object collections from exported features.
- Preserves full `original_data` and applies updated geometry from GeoJSON.
- Preserves wall painting associations (`paintings` arrays).
- Merges room polygons into each floor as `rooms` entries.

Optional:

- `--replace-existing-rooms` to replace `rooms` instead of appending.
- `--floor-number N` if exported features do not contain a floor property.
