#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_floor_number(properties: Dict[str, Any], fallback_floor: Optional[int]) -> int:
    value = properties.get("floor", properties.get("floor_number"))
    if value is None:
        if fallback_floor is None:
            raise ValueError(
                "Feature missing floor/floor_number property and no --floor-number was provided."
            )
        return fallback_floor
    return int(value)


def extract_polygon_points(geometry: Dict[str, Any]) -> List[Dict[str, float]]:
    if geometry.get("type") != "Polygon":
        raise ValueError(f"Unsupported geometry type: {geometry.get('type')}. Only Polygon is supported.")

    rings = geometry.get("coordinates", [])
    if not rings or not rings[0]:
        raise ValueError("Polygon geometry has no coordinates.")

    outer_ring = rings[0]
    if len(outer_ring) >= 2 and outer_ring[0] == outer_ring[-1]:
        outer_ring = outer_ring[:-1]

    return [{"x": float(x), "y": float(y)} for x, y in outer_ring]


def parse_rooms_from_geojson(
    geojson_path: Path, fallback_floor: Optional[int] = None
) -> Dict[int, List[Dict[str, Any]]]:
    with geojson_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("type") != "FeatureCollection":
        raise ValueError(f"{geojson_path} is not a GeoJSON FeatureCollection.")

    rooms_by_floor: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    generated_index = defaultdict(int)

    for feature in data.get("features", []):
        properties = feature.get("properties", {}) or {}
        geometry = feature.get("geometry", {}) or {}
        floor_number = parse_floor_number(properties, fallback_floor)
        polygon = extract_polygon_points(geometry)

        generated_index[floor_number] += 1
        room_id = str(
            properties.get("id")
            or properties.get("room_id")
            or f"floor_{floor_number}_room_{generated_index[floor_number]}"
        )
        room_name = str(properties.get("name") or properties.get("room_name") or room_id)

        rooms_by_floor[floor_number].append(
            {
                "id": room_id,
                "name": room_name,
                "polygon": polygon,
            }
        )

    return rooms_by_floor


def merge_rooms(
    plan: Dict[str, Any], imported_rooms: Dict[int, List[Dict[str, Any]]], replace: bool
) -> Dict[str, Any]:
    for floor in plan.get("floors", []):
        floor_number = int(floor.get("number"))
        existing = floor.get("rooms", [])
        if not isinstance(existing, list):
            existing = []

        new_rooms = imported_rooms.get(floor_number, [])
        floor["rooms"] = new_rooms if replace else existing + new_rooms

    return plan


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert GeoJSON room polygons from QGIS back into NMFA floor-plan JSON."
    )
    parser.add_argument(
        "--input-json",
        default="data/NMFA_3floors_plan.json",
        help="Path to the original museum JSON file.",
    )
    parser.add_argument(
        "--rooms-geojson",
        nargs="+",
        required=True,
        help="One or more GeoJSON files containing room Polygon features.",
    )
    parser.add_argument(
        "--output-json",
        default="data/NMFA_3floors_plan_with_rooms.json",
        help="Path for output JSON containing merged rooms.",
    )
    parser.add_argument(
        "--floor-number",
        type=int,
        default=None,
        help="Fallback floor number used when GeoJSON features do not include floor properties.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace existing rooms per floor instead of appending.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_json)
    output_path = Path(args.output_json)

    with input_path.open("r", encoding="utf-8") as f:
        plan = json.load(f)

    combined_rooms: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for room_geojson in args.rooms_geojson:
        parsed = parse_rooms_from_geojson(Path(room_geojson), fallback_floor=args.floor_number)
        for floor_number, rooms in parsed.items():
            combined_rooms[floor_number].extend(rooms)

    updated_plan = merge_rooms(plan, combined_rooms, replace=args.replace_existing)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(updated_plan, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
