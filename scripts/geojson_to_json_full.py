#!/usr/bin/env python3
import argparse
import copy
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def extract_floor_from_filename(path: Path) -> Optional[int]:
    match = re.search(r"floor_(\d+)", path.stem)
    return int(match.group(1)) if match else None


def parse_floor_number(
    properties: Dict[str, Any], fallback_floor: Optional[int], path_hint: Path
) -> int:
    value = properties.get("floor", properties.get("floor_number"))
    if value is not None:
        return int(value)

    from_name = extract_floor_from_filename(path_hint)
    if from_name is not None:
        return from_name

    if fallback_floor is None:
        raise ValueError(
            f"Feature missing floor/floor_number property in {path_hint}. "
            "Provide --floor-number N when running the script."
        )
    return fallback_floor


def coords_to_xy_dicts(coords: List[List[float]]) -> List[Dict[str, float]]:
    return [{"x": float(x), "y": float(y)} for x, y in coords]


def extract_polygon_points(geometry: Dict[str, Any]) -> List[Dict[str, float]]:
    rings = geometry.get("coordinates", [])
    if not rings or not rings[0]:
        raise ValueError("Polygon geometry has no coordinates.")

    outer_ring = rings[0]
    if len(outer_ring) >= 2 and outer_ring[0] == outer_ring[-1]:
        outer_ring = outer_ring[:-1]
    return coords_to_xy_dicts(outer_ring)


def apply_geometry_to_object(
    obj: Dict[str, Any], geometry: Dict[str, Any], source_collection: str
) -> Dict[str, Any]:
    geometry_type = geometry.get("type")
    if geometry_type == "Point":
        coordinates = geometry.get("coordinates", [])
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            raise ValueError(
                "Point geometry coordinates must be [x, y] "
                f"(got {type(coordinates).__name__}: {coordinates!r})."
            )
        xy = [{"x": float(coordinates[0]), "y": float(coordinates[1])}]
    elif geometry_type == "LineString":
        coordinates = geometry.get("coordinates", [])
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise ValueError(
                "LineString geometry must have at least 2 coordinate points "
                f"(got {type(coordinates).__name__}: {coordinates!r})."
            )
        xy = coords_to_xy_dicts(coordinates)
    elif geometry_type == "Polygon":
        obj["polygon"] = extract_polygon_points(geometry)
        return obj
    else:
        raise ValueError(f"Unsupported geometry type: {geometry_type}")

    if "position" in obj or source_collection == "walls":
        obj["position"] = xy
    elif "formToDraw" in obj or source_collection == "background":
        obj["formToDraw"] = xy
    else:
        obj["position"] = xy
    return obj


def infer_source_collection(properties: Dict[str, Any], geometry_type: str) -> str:
    source_collection = properties.get("source_collection")
    if isinstance(source_collection, str) and source_collection:
        return source_collection

    object_type = str(properties.get("object_type", "")).lower()
    if object_type == "wall":
        return "walls"
    if object_type == "room" or geometry_type == "Polygon":
        return "rooms"
    return "background"


def build_room_from_feature(feature: Dict[str, Any], properties: Dict[str, Any]) -> Dict[str, Any]:
    geometry = feature.get("geometry", {}) or {}
    if geometry.get("type") != "Polygon":
        raise ValueError("Room features must use Polygon geometry.")

    room_id = str(properties.get("id") or properties.get("room_id") or "room")
    room_name = str(properties.get("name") or properties.get("room_name") or room_id)
    polygon = extract_polygon_points(geometry)
    original_data = properties.get("original_data")
    if isinstance(original_data, dict):
        room = copy.deepcopy(original_data)
    else:
        room = {}

    # Keep extra room metadata from original_data, but use edited GeoJSON ID/name/polygon.
    room["id"] = room_id
    room["name"] = room_name
    room["polygon"] = polygon
    return room


def parse_objects_from_geojson(
    geojson_path: Path, fallback_floor: Optional[int] = None
) -> Dict[int, Dict[str, List[Dict[str, Any]]]]:
    with geojson_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("type") != "FeatureCollection":
        raise ValueError(f"{geojson_path} is not a GeoJSON FeatureCollection.")

    by_floor: Dict[int, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))

    for feature in data.get("features", []):
        properties = feature.get("properties", {}) or {}
        geometry = feature.get("geometry", {}) or {}
        geometry_type = geometry.get("type")
        if geometry_type is None:
            continue

        floor_number = parse_floor_number(properties, fallback_floor, geojson_path)
        source_collection = infer_source_collection(properties, geometry_type)

        if source_collection == "rooms":
            room = build_room_from_feature(feature, properties)
            by_floor[floor_number]["rooms"].append(room)
            continue

        original_data = properties.get("original_data")
        obj: Dict[str, Any]
        if isinstance(original_data, dict):
            obj = copy.deepcopy(original_data)
        else:
            obj = {}

        feature_id = properties.get("id")
        if feature_id is not None:
            obj["id"] = str(feature_id)

        obj = apply_geometry_to_object(obj, geometry, source_collection)

        paintings = properties.get("paintings")
        if source_collection == "walls":
            if isinstance(paintings, list):
                obj["paintings"] = copy.deepcopy(paintings)
            elif "paintings" not in obj:
                obj["paintings"] = []

        object_type = properties.get("object_type")
        if source_collection == "background" and "type" not in obj and object_type:
            obj["type"] = str(object_type)

        by_floor[floor_number][source_collection].append(obj)

    return by_floor


def merge_objects(
    plan: Dict[str, Any],
    imported_objects: Dict[int, Dict[str, List[Dict[str, Any]]]],
    replace_existing_rooms: bool,
) -> Dict[str, Any]:
    for floor in plan.get("floors", []):
        floor_number = int(floor.get("number"))
        floor_data = imported_objects.get(floor_number)
        if not floor_data:
            continue

        for collection_name, items in floor_data.items():
            if collection_name == "rooms":
                existing_rooms = floor.get("rooms", [])
                if not isinstance(existing_rooms, list):
                    existing_rooms = []
                if replace_existing_rooms:
                    floor["rooms"] = items
                else:
                    floor["rooms"] = existing_rooms + items
            else:
                floor[collection_name] = items

    return plan


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert all-object floor GeoJSON files back into complete NMFA floor-plan JSON."
    )
    parser.add_argument(
        "--input-json",
        default="data/NMFA_3floors_plan.json",
        help="Path to the original museum JSON file.",
    )
    parser.add_argument(
        "--geojson-files",
        nargs="+",
        required=True,
        help="One or more GeoJSON files exported from QGIS.",
    )
    parser.add_argument(
        "--output-json",
        default="data/NMFA_3floors_plan_updated.json",
        help="Path for output JSON containing merged objects and rooms.",
    )
    parser.add_argument(
        "--floor-number",
        type=int,
        default=None,
        help="Fallback floor number used when GeoJSON features do not include floor properties.",
    )
    parser.add_argument(
        "--replace-existing-rooms",
        action="store_true",
        help="Replace existing rooms per floor instead of appending.",
    )
    args = parser.parse_args()

    with Path(args.input_json).open("r", encoding="utf-8") as f:
        plan = json.load(f)

    combined: Dict[int, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for geojson_file in args.geojson_files:
        parsed = parse_objects_from_geojson(Path(geojson_file), fallback_floor=args.floor_number)
        for floor_number, collections in parsed.items():
            for collection_name, items in collections.items():
                combined[floor_number][collection_name].extend(items)

    updated_plan = merge_objects(
        plan, combined, replace_existing_rooms=args.replace_existing_rooms
    )

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(updated_plan, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
