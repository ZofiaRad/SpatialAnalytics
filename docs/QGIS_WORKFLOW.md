# QGIS workflow for room digitization

This guide explains how to use the project conversion scripts with QGIS:

- `scripts/json_to_geojson.py` (walls JSON ➜ per-floor GeoJSON lines)
- `scripts/geojson_to_json.py` (digitized room polygons GeoJSON ➜ updated project JSON)

## 1) Generate per-floor wall reference layers

From the repository root (`/home/runner/work/SpatialAnalytics/SpatialAnalytics`):

```bash
python scripts/json_to_geojson.py \
  --input-json data/NMFA_3floors_plan.json \
  --output-dir data
```

This creates:

- `data/floor_0_walls.geojson`
- `data/floor_1_walls.geojson`
- `data/floor_2_walls.geojson`

Load one of these in QGIS as a reference layer while digitizing rooms.

## 2) Import wall GeoJSON into QGIS

1. Open QGIS and create a new project.
2. Go to **Layer → Add Layer → Add Vector Layer**.
3. Choose one of the generated files, e.g. `data/floor_0_walls.geojson`.
4. Click **Add**.
5. (Optional) Style walls with a thin dark line for easier tracing.

Repeat for other floors if you want multiple floor references in one project.

## 3) Digitize room polygons in QGIS

1. Create a new polygon layer:
   - **Layer → Create Layer → New GeoPackage Layer** (or Shapefile/GeoJSON)
   - Geometry type: **Polygon**
   - Add fields:
     - `id` (text)
     - `name` (text)
     - `floor` (integer)
2. Enable snapping:
   - **Project → Snapping Options**
   - Enable snapping for the walls layer (vertex/segment).
3. Toggle editing on the room layer.
4. Use **Add Polygon Feature** to draw each room boundary.
5. For each polygon feature, fill attributes:
   - `id` (e.g., `F0_R01`)
   - `name` (e.g., `Gallery A`)
   - `floor` (`0`, `1`, or `2`)
6. Save edits and stop editing.

## 4) Export rooms from QGIS as GeoJSON

1. Right-click your room polygon layer.
2. Choose **Export → Save Features As...**
3. Format: **GeoJSON**
4. Save as e.g. `data/rooms_from_qgis.geojson`.

## 5) Convert room GeoJSON back to project JSON

```bash
python scripts/geojson_to_json.py \
  --input-json data/NMFA_3floors_plan.json \
  --rooms-geojson data/rooms_from_qgis.geojson \
  --output-json data/NMFA_3floors_plan_with_rooms.json
```

If your exported features do not include a `floor`/`floor_number` attribute, use:

```bash
python scripts/geojson_to_json.py \
  --input-json data/NMFA_3floors_plan.json \
  --rooms-geojson data/rooms_floor0.geojson \
  --floor-number 0 \
  --output-json data/NMFA_3floors_plan_with_rooms.json
```

The output room format per floor is:

```json
{
  "id": "room_id",
  "name": "room_name",
  "polygon": [
    {"x": 100.0, "y": 200.0},
    {"x": 150.0, "y": 200.0},
    {"x": 150.0, "y": 250.0}
  ]
}
```
