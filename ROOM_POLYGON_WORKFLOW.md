# Room polygon workflow (R + manual digitization)

This repository now includes `/home/runner/work/SpatialAnalytics/SpatialAnalytics/room_polygon_workflow.R` to build room polygons from:

- wall line segments in `data/NMFA_3floors_plan.json`
- a hand-drawn room plan PDF (converted to image for tracing)

## 1) Load wall geometry and visualize a floor

```r
source("/home/runner/work/SpatialAnalytics/SpatialAnalytics/room_polygon_workflow.R")

plan <- load_museum_plan("/home/runner/work/SpatialAnalytics/SpatialAnalytics/data/NMFA_3floors_plan.json")
walls_sf <- extract_walls_sf(plan)
background_sf <- extract_background_sf(plan)

plot_floor_reference(walls_sf, floor_id = 0, background_sf = background_sf)
```

## 2) Convert floor plan PDF to high-resolution image

If you have the original PDF file (example path below), convert it to PNG:

```r
prepare_floorplan_image(
  pdf_path = "/home/runner/work/SpatialAnalytics/SpatialAnalytics/data/museum_walls_plan.pdf",
  output_png = "/home/runner/work/SpatialAnalytics/SpatialAnalytics/data/museum_walls_plan_floor0.png",
  page = 1,
  dpi = 600
)
```

## 3) Interactive room digitization in R (`mapedit`)

```r
rooms_sf <- digitize_rooms_mapedit(walls_sf, floor_id = 0)
```

This opens an interactive editor where you draw room polygons manually.

### QGIS-friendly export of wall reference layer

```r
export_geojson(
  walls_sf %>% dplyr::filter(floor == 0),
  "/home/runner/work/SpatialAnalytics/SpatialAnalytics/data/walls_floor0.geojson"
)
```

## 4) Convert manually supplied coordinates to polygons

For scripted/batch room definitions:

```r
room_coords <- list(
  matrix(c(100, 100,
           400, 100,
           400, 500,
           100, 500), ncol = 2, byrow = TRUE),
  matrix(c(450, 100,
           700, 100,
           700, 500,
           450, 500), ncol = 2, byrow = TRUE)
)

rooms_sf <- room_coords_to_sf(room_coords, floor_id = 0, room_ids = c("A", "B"))
```

## 5) Export reusable room polygons

```r
export_geojson(
  rooms_sf,
  "/home/runner/work/SpatialAnalytics/SpatialAnalytics/data/rooms_floor0.geojson"
)
```

The exported GeoJSON is QGIS-friendly and can be loaded back with `sf::st_read()`.

## Optional convenience pipeline

```r
res <- run_room_workflow(
  json_path = "/home/runner/work/SpatialAnalytics/SpatialAnalytics/data/NMFA_3floors_plan.json",
  floor_id = 0
)

res$floor_plot
```

## Notes

- Fully automatic room extraction is not reliable here because room boundaries are conceptual/arbitrary.
- The provided workflow is intentionally hybrid: automated parsing + manual digitization + reusable GeoJSON output.
