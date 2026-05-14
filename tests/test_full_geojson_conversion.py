import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_JSON = REPO_ROOT / "data" / "NMFA_3floors_plan.json"
TEST_ROOM_POLYGON = [[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]


class FullGeojsonConversionTests(unittest.TestCase):
    def _count_spatial_objects_per_floor(self) -> dict[int, int]:
        plan = json.loads(INPUT_JSON.read_text())
        expected: dict[int, int] = {}
        for floor in plan["floors"]:
            count = 0
            for collection in floor.values():
                if not isinstance(collection, list):
                    continue
                for obj in collection:
                    if not isinstance(obj, dict):
                        continue
                    points = obj.get("position") or obj.get("formToDraw")
                    if (
                        isinstance(points, list)
                        and points
                        and all(isinstance(p, dict) and "x" in p and "y" in p for p in points)
                    ):
                        count += 1
            expected[int(floor["number"])] = count
        return expected

    def test_json_to_geojson_full_exports_all_floor_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            subprocess.run(
                [
                    "python",
                    str(REPO_ROOT / "scripts" / "json_to_geojson_full.py"),
                    "--input-json",
                    str(INPUT_JSON),
                    "--output-dir",
                    str(output_dir),
                ],
                check=True,
                cwd=REPO_ROOT,
            )

            floor0 = json.loads((output_dir / "floor_0_all_objects.geojson").read_text())
            floor1 = json.loads((output_dir / "floor_1_all_objects.geojson").read_text())
            floor2 = json.loads((output_dir / "floor_2_all_objects.geojson").read_text())

            expected_counts = self._count_spatial_objects_per_floor()
            self.assertEqual(len(floor0["features"]), expected_counts[0])
            self.assertEqual(len(floor1["features"]), expected_counts[1])
            self.assertEqual(len(floor2["features"]), expected_counts[2])

            wall_feature = next(
                f
                for f in floor0["features"]
                if f["properties"]["object_type"] == "wall"
                and f["properties"]["id"] == "W0_0"
            )
            self.assertEqual(wall_feature["geometry"]["type"], "LineString")
            self.assertTrue(isinstance(wall_feature["properties"]["paintings"], list))
            self.assertEqual(
                wall_feature["properties"]["paintings"][0]["id"],
                "0_5830",
            )
            self.assertEqual(wall_feature["properties"]["wall_id_reference"], "W0_0")

    def test_geojson_to_json_full_restores_objects_and_adds_rooms(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exported_floor0 = output_dir / "floor_0_all_objects.geojson"
            updated_floor0 = output_dir / "floor_0_all_objects_edited.geojson"
            merged_json = output_dir / "merged.json"

            subprocess.run(
                [
                    "python",
                    str(REPO_ROOT / "scripts" / "json_to_geojson_full.py"),
                    "--input-json",
                    str(INPUT_JSON),
                    "--output-dir",
                    str(output_dir),
                ],
                check=True,
                cwd=REPO_ROOT,
            )

            floor0 = json.loads(exported_floor0.read_text())
            floor0["features"].append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [TEST_ROOM_POLYGON],
                    },
                    "properties": {
                        "id": "F0_R_TEST",
                        "name": "Test Room",
                        "floor": 0,
                        "object_type": "room",
                    },
                }
            )
            updated_floor0.write_text(json.dumps(floor0), encoding="utf-8")

            subprocess.run(
                [
                    "python",
                    str(REPO_ROOT / "scripts" / "geojson_to_json_full.py"),
                    "--input-json",
                    str(INPUT_JSON),
                    "--geojson-files",
                    str(updated_floor0),
                    str(output_dir / "floor_1_all_objects.geojson"),
                    str(output_dir / "floor_2_all_objects.geojson"),
                    "--output-json",
                    str(merged_json),
                ],
                check=True,
                cwd=REPO_ROOT,
            )

            merged = json.loads(merged_json.read_text())
            floor0_merged = next(f for f in merged["floors"] if f["number"] == 0)
            self.assertEqual(len(floor0_merged["walls"]), 235)
            self.assertEqual(len(floor0_merged["background"]), 65)
            self.assertIn("rooms", floor0_merged)
            self.assertEqual(floor0_merged["rooms"][0]["id"], "F0_R_TEST")
            self.assertEqual(
                floor0_merged["walls"][0]["paintings"][0]["id"],
                "0_5830",
            )


if __name__ == "__main__":
    unittest.main()
