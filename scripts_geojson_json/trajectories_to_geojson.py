#!/usr/bin/env python3
"""
trajectories_to_geojson.py

Read a CSV of trajectory points containing X and Y pixel coordinates and
write a GeoJSON FeatureCollection. This does a 1:1 coordinate conversion
— it treats the CSV X,Y as the GeoJSON coordinates directly.

Usage examples:
  python trajectories_to_geojson.py input.csv output.geojson --x X --y Y --id track_id

The script supports optional columns for timestamp and track id, and
can output either Points or LineString per track.
"""
import argparse
import csv
import json
from collections import defaultdict
import os
from typing import Dict, List, Any

project_dir = os.path.join(os.path.dirname(__file__))
out_dir = os.path.join(project_dir, '../data/geojson_converted_objects/')
data_dir = os.path.join(project_dir, '../data/all_trajectories_normalised.csv')

def read_csv_points(path: str, x_col: str, y_col: str, id_col: str = None, ts_col: str = None, floor_col: str = None, floor_filter: str = None, has_header: bool = True) -> List[Dict[str, Any]]:
    points = []
    with open(path, newline='') as fh:
        if has_header:
            reader = csv.DictReader(fh)
        else:
            reader = csv.reader(fh)
        for i, row in enumerate(reader):
            if not has_header:
                # when no header, x_col/y_col/id_col/ts_col are treated as indices
                def get(col):
                    try:
                        idx = int(col)
                        return row[idx]
                    except Exception:
                        return None
                x = get(x_col)
                y = get(y_col)
                tid = get(id_col) if id_col is not None else None
                ts = get(ts_col) if ts_col is not None else None
                floor = get(floor_col) if floor_col is not None else None
            else:
                x = row.get(x_col)
                y = row.get(y_col)
                tid = row.get(id_col) if id_col is not None else None
                ts = row.get(ts_col) if ts_col is not None else None
                floor = row.get(floor_col) if floor_col is not None else None

            # Apply floor filter if specified
            if floor_filter is not None and floor != floor_filter:
                continue

            if x is None or y is None:
                # skip malformed rows
                continue

            try:
                x_f = float(x)
                y_f = float(y)
            except ValueError:
                # skip rows where coordinates are not numeric
                continue

            points.append({
                'x': x_f,
                'y': y_f,
                'id': tid,
                'ts': ts,
                'floor': floor,
                'raw': row if has_header else None,
            })
    return points


def points_to_geojson_points(points: List[Dict[str, Any]], props_from_row: bool = False) -> Dict[str, Any]:
    features = []
    for p in points:
        properties = {}
        if p.get('id') is not None:
            properties['id'] = p['id']
        if p.get('ts') is not None:
            properties['timestamp'] = p['ts']
        if p.get('floor') is not None:
            properties['floorNumber'] = p['floor']
        if props_from_row and p.get('raw'):
            properties.update(p['raw'])

        feat = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [p['x'], p['y']]},
            'properties': properties,
        }
        features.append(feat)
    return {'type': 'FeatureCollection', 'features': features}


def points_to_geojson_lines(points: List[Dict[str, Any]], id_col: str = None) -> Dict[str, Any]:
    # Group by id_col
    groups = defaultdict(list)
    for p in points:
        key = p.get('id') if id_col is not None else '__all__'
        groups[key].append((p.get('ts'), (p['x'], p['y']), p))

    features = []
    for key, items in groups.items():
        # sort by timestamp if available
        items_sorted = sorted(items, key=lambda t: (t[0] is None, t[0]))
        coords = [pt for _, pt, _ in items_sorted]
        properties = {'id': key} if key != '__all__' else {}
        # Add floor from first point if available
        if items_sorted and items_sorted[0][2].get('floor') is not None:
            properties['floorNumber'] = items_sorted[0][2].get('floor')
        feat = {
            'type': 'Feature',
            'geometry': {'type': 'LineString', 'coordinates': coords},
            'properties': properties,
        }
        features.append(feat)

    return {'type': 'FeatureCollection', 'features': features}


def write_geojson(obj: Dict[str, Any], path: str) -> None:
    with open(path, 'w') as fh:
        json.dump(obj, fh, indent=2)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Convert CSV of pixel XY trajectories to GeoJSON (1:1 conversion)')
    p.add_argument('csv', help='Input CSV file path')
    p.add_argument('out', help='Output GeoJSON path')
    p.add_argument('--x', default='x', help='Column name or index for X coordinate (default: "x")')
    p.add_argument('--y', default='y', help='Column name or index for Y coordinate (default: "y")')
    p.add_argument('--id', default=None, help='Column name or index for track id (optional)')
    p.add_argument('--ts', default=None, help='Column name or index for timestamp (optional)')
    p.add_argument('--floor-col', default=None, help='Column name or index for floor number (optional)')
    p.add_argument('--floor', default=None, help='Filter trajectories by floor number (optional)')
    p.add_argument('--format', choices=['points', 'lines'], default='points', help='Output geometry type')
    p.add_argument('--no-header', dest='has_header', action='store_false', help='Treat CSV as having no header (then --x/--y/--id/--ts are indices)')
    p.add_argument('--props-from-row', action='store_true', help='Copy all row columns into properties for point features')
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    points = read_csv_points(args.csv, x_col=args.x, y_col=args.y, id_col=args.id, ts_col=args.ts, floor_col=args.floor_col, floor_filter=args.floor, has_header=args.has_header)
    if args.format == 'points':
        geo = points_to_geojson_points(points, props_from_row=args.props_from_row)
    else:
        geo = points_to_geojson_lines(points, id_col=args.id)

    write_geojson(geo, args.out)
    print(f'Wrote {len(geo.get("features", []))} features to {args.out}')


if __name__ == '__main__':
    main()
