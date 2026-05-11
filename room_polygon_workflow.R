# Room polygon workflow for NMFA floor plans
# This script provides a hybrid (semi-automated) workflow:
# 1) parse wall segments from JSON, 2) prepare PDF image reference,
# 3) interactively digitize rooms, 4) export room polygons as sf/GeoJSON.

suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
  library(purrr)
  library(sf)
  library(ggplot2)
})

load_museum_plan <- function(json_path) {
  stopifnot(file.exists(json_path))
  fromJSON(json_path, simplifyVector = FALSE)
}

extract_walls_sf <- function(plan, floors = NULL, crs = NA_crs_) {
  wall_tbl <- map_dfr(plan$floors, function(floor_item) {
    map_dfr(floor_item$walls, function(wall) {
      p1 <- wall$position[[1]]
      p2 <- wall$position[[2]]
      tibble(
        floor = floor_item$number,
        wall_id = wall$id,
        x1 = p1$x,
        y1 = p1$y,
        x2 = p2$x,
        y2 = p2$y,
        painting_ids = list(map_chr(wall$paintings, function(p) if (is.null(p$id)) NA_character_ else as.character(p$id)))
      )
    })
  })

  if (!is.null(floors)) {
    wall_tbl <- wall_tbl %>% filter(floor %in% floors)
  }

  wall_tbl$geometry <- pmap(
    wall_tbl[, c("x1", "y1", "x2", "y2")],
    function(x1, y1, x2, y2) st_linestring(matrix(c(x1, y1, x2, y2), ncol = 2, byrow = TRUE))
  )

  sf::st_as_sf(wall_tbl, sf_column_name = "geometry", crs = crs)
}

extract_background_sf <- function(plan, floors = NULL, crs = NA_crs_) {
  bg_tbl <- map_dfr(plan$floors, function(floor_item) {
    map_dfr(floor_item$background, function(bg) {
      p1 <- bg$formToDraw[[1]]
      p2 <- bg$formToDraw[[2]]
      tibble(
        floor = floor_item$number,
        background_type = bg$type,
        x1 = p1$x,
        y1 = p1$y,
        x2 = p2$x,
        y2 = p2$y
      )
    })
  })

  if (!is.null(floors)) {
    bg_tbl <- bg_tbl %>% filter(floor %in% floors)
  }

  bg_tbl$geometry <- pmap(
    bg_tbl[, c("x1", "y1", "x2", "y2")],
    function(x1, y1, x2, y2) st_linestring(matrix(c(x1, y1, x2, y2), ncol = 2, byrow = TRUE))
  )

  sf::st_as_sf(bg_tbl, sf_column_name = "geometry", crs = crs)
}

prepare_floorplan_image <- function(pdf_path, output_png, page = 1, dpi = 600) {
  if (!requireNamespace("pdftools", quietly = TRUE)) {
    stop("Package 'pdftools' is required for PDF conversion. Install with install.packages('pdftools').")
  }
  stopifnot(file.exists(pdf_path))
  pdftools::pdf_convert(
    pdf = pdf_path,
    pages = page,
    dpi = dpi,
    filenames = output_png
  )
}

plot_floor_reference <- function(walls_sf, floor_id, background_sf = NULL, reverse_axes = TRUE) {
  p <- ggplot() +
    geom_sf(data = walls_sf %>% filter(floor == floor_id), linewidth = 0.35, color = "black")

  if (!is.null(background_sf)) {
    p <- p +
      geom_sf(data = background_sf %>% filter(floor == floor_id), linewidth = 0.25, color = "grey55")
  }

  if (isTRUE(reverse_axes)) {
    p <- p + scale_x_reverse() + scale_y_reverse()
  }

  p + coord_sf(expand = FALSE) + theme_void()
}

digitize_rooms_mapedit <- function(walls_sf, floor_id) {
  if (!requireNamespace("mapview", quietly = TRUE) || !requireNamespace("mapedit", quietly = TRUE)) {
    stop("Packages 'mapview' and 'mapedit' are required for interactive digitization.")
  }

  layer <- walls_sf %>% filter(floor == floor_id)
  edit_result <- mapedit::editMap(mapview::mapview(layer, color = "black", lwd = 1))

  rooms <- edit_result$finished
  if (is.null(rooms) || nrow(rooms) == 0) {
    stop("No room polygons were digitized.")
  }

  rooms %>%
    mutate(
      floor = floor_id,
      room_id = ifelse("feature_id" %in% names(.), as.character(feature_id), paste0("f", floor_id, "_room_", row_number()))
    )
}

room_coords_to_sf <- function(room_coords, floor_id, room_ids = NULL, crs = NA_crs_) {
  stopifnot(is.list(room_coords), length(room_coords) > 0)

  if (is.null(room_ids)) {
    room_ids <- paste0("f", floor_id, "_room_", seq_along(room_coords))
  }
  stopifnot(length(room_ids) == length(room_coords))

  geoms <- map(room_coords, function(coords) {
    m <- as.matrix(coords)
    stopifnot(ncol(m) == 2, nrow(m) >= 3)
    if (!all(m[1, ] == m[nrow(m), ])) {
      m <- rbind(m, m[1, ])
    }
    st_polygon(list(m))
  })

  st_sf(
    floor = floor_id,
    room_id = room_ids,
    geometry = st_sfc(geoms, crs = crs)
  )
}

export_geojson <- function(sf_obj, output_geojson, overwrite = TRUE) {
  sf::st_write(sf_obj, output_geojson, delete_dsn = overwrite, quiet = TRUE)
  invisible(output_geojson)
}

# Optional convenience pipeline
run_room_workflow <- function(
  json_path = "data/NMFA_3floors_plan.json",
  floor_id = 0,
  pdf_path = NULL,
  png_path = NULL
) {
  plan <- load_museum_plan(json_path)
  walls_sf <- extract_walls_sf(plan)
  bg_sf <- extract_background_sf(plan)

  if (!is.null(pdf_path) && !is.null(png_path)) {
    prepare_floorplan_image(pdf_path, png_path, page = floor_id + 1)
  }

  list(
    plan = plan,
    walls_sf = walls_sf,
    background_sf = bg_sf,
    floor_plot = plot_floor_reference(walls_sf, floor_id, bg_sf)
  )
}
