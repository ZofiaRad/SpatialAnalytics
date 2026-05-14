#!/usr/bin/env python3
import argparse
import copy
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ID_PREFIX_TO_TYPE = {
    "W": "wall",
    "D": "door",
    "F": "furniture",
    "S": "stair",
    "R": "room",
}


def extract_coords_from_points(points: Any) -> Optional[List[List[float]]]:
    if not isinstance(points, list) or not points:
        return None

    coords: List[List[float]] = []
    for point in points:
        if not isinstance(point, dict) or "x" not in point or "y" not in point:
            return None
        coords.append([float(point["x"]), float(point["y"])])
    return coords


def infer_object_type(
    obj: Dict[str, Any], source_collection: str, default_fallback: str = "unknown"
) -> str:
    explicit_type = obj.get("type")
    if isinstance(explicit_type, str) and explicit_type.strip():
        return explicit_type.strip().lower()

    obj_id = obj.get("id")
    if isinstance(obj_id, str):
        match = re.match(r"([A-Za-z]+)", obj_id)
        if match:
            prefix = match.group(1).upper()
            if prefix in ID_PREFIX_TO_TYPE:
                return ID_PREFIX_TO_TYPE[prefix]

    if source_collection.endswith("s") and len(source_collection) > 1:
        return source_collection[:-1].lower()
    if source_collection:
        return source_collection.lower()
    return default_fallback


def build_feature(
    floor_number: int, source_collection: str, source_index: int, obj: Dict[str, Any]
) -> Optional[Tuple[Dict[str, Any], str]]:
    coords = extract_coords_from_points(obj.get("position"))
    spatial_field = "position"
    if coords is None:
        coords = extract_coords_from_points(obj.get("formToDraw"))
        spatial_field = "formToDraw"

    if coords is None:
        return None

    geometry: Dict[str, Any]
    if len(coords) == 1:
        geometry = {"type": "Point", "coordinates": coords[0]}
    else:
        geometry = {"type": "LineString", "coordinates": coords}

    object_type = infer_object_type(obj, source_collection)
    object_id = obj.get("id")
    if not object_id:
        object_id = f"{source_collection}_{floor_number}_{source_index}"

    paintings = obj.get("paintings")
    if not isinstance(paintings, list):
        paintings = []

    wall_id_reference = None
    if paintings or object_type == "wall":
        wall_id_reference = str(object_id)

    feature = {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "id": str(object_id),
            "object_type": object_type,
            "floor": floor_number,
            "source_collection": source_collection,
            "source_index": source_index,
            "spatial_field": spatial_field,
            "original_data": copy.deepcopy(obj),
            "paintings": copy.deepcopy(paintings),
            "wall_id_reference": wall_id_reference,
        },
    }
    return feature, object_type


def convert_floor_to_geojson(
    floor: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, int], Dict[str, int]]:
    floor_number = int(floor["number"])
    features: List[Dict[str, Any]] = []
    object_type_counts: Counter[str] = Counter()
    source_collection_counts: Counter[str] = Counter()

    for source_collection, collection_value in floor.items():
        if not isinstance(collection_value, list):
            continue
        for index, obj in enumerate(collection_value):
            if not isinstance(obj, dict):
                continue
            built = build_feature(floor_number, source_collection, index, obj)
            if built is None:
                continue
            feature, object_type = built
            features.append(feature)
            object_type_counts[object_type] += 1
            source_collection_counts[source_collection] += 1

    geojson = {
        "type": "FeatureCollection",
        "name": f"floor_{floor_number}_all_objects",
        "features": features,
    }
    return geojson, dict(object_type_counts), dict(source_collection_counts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert complete NMFA floor-plan JSON into per-floor GeoJSON files with all spatial objects."
    )
    parser.add_argument(
        "--input-json",
        default="data/NMFA_3floors_plan.json",
        help="Path to input floor-plan JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Directory where floor_*_all_objects.geojson files are written.",
    )
    parser.add_argument(
        "--report-file",
        default="geojson_conversion_report.json",
        help="Report filename (stored inside --output-dir).",
    )
    args = parser.parse_args()

    input_path = Path(args.input_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as f:
        plan = json.load(f)

    report: Dict[str, Any] = {"input_json": str(input_path), "floors": {}}
    total_features = 0
    aggregate_type_counts: Dict[str, int] = defaultdict(int)

    for floor in plan.get("floors", []):
        floor_number = int(floor["number"])
        geojson, type_counts, source_counts = convert_floor_to_geojson(floor)
        output_path = output_dir / f"floor_{floor_number}_all_objects.geojson"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)
            f.write("\n")

        feature_count = len(geojson["features"])
        total_features += feature_count
        for object_type, count in type_counts.items():
            aggregate_type_counts[object_type] += count

        report["floors"][str(floor_number)] = {
            "geojson_file": str(output_path),
            "feature_count": feature_count,
            "object_type_counts": type_counts,
            "source_collection_counts": source_counts,
        }

        print(f"[floor {floor_number}] wrote {output_path} ({feature_count} features)")
        print(f"  object types: {type_counts}")

    report["total_features"] = total_features
    report["aggregate_object_type_counts"] = dict(aggregate_type_counts)
    report_path = output_dir / args.report_file
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote summary report: {report_path}")


if __name__ == "__main__":
    main()
