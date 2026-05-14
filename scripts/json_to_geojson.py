#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def wall_to_feature(floor_number: int, wall: Dict[str, Any]) -> Dict[str, Any]:
    p1, p2 = wall["position"]
    return {
        "type": "Feature",
        "properties": {
            "floor": floor_number,
            "wall_id": wall["id"],
        },
        "geometry": {
            "type": "LineString",
            "coordinates": [[p1["x"], p1["y"]], [p2["x"], p2["y"]]],
        },
    }


def convert_floor_to_geojson(floor: Dict[str, Any]) -> Dict[str, Any]:
    floor_number = floor["number"]
    features: List[Dict[str, Any]] = [
        wall_to_feature(floor_number, wall) for wall in floor.get("walls", [])
    ]
    return {
        "type": "FeatureCollection",
        "name": f"floor_{floor_number}_walls",
        "features": features,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert NMFA floor-plan wall JSON into per-floor GeoJSON files."
    )
    parser.add_argument(
        "--input-json",
        default="data/NMFA_3floors_plan.json",
        help="Path to input floor-plan JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Directory where floor_*_walls.geojson files are written.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as f:
        plan = json.load(f)

    for floor in plan.get("floors", []):
        floor_number = floor["number"]
        geojson = convert_floor_to_geojson(floor)
        output_path = output_dir / f"floor_{floor_number}_walls.geojson"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
