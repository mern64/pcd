#!/usr/bin/env python3
"""Utility to extract Snapshot IDs and coordinates from a GLB/GTLF file."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from pygltflib import GLTF2  # type: ignore
except ImportError as exc:  # pragma: no cover - runtime dependency
    raise SystemExit("pygltflib must be installed to run this script") from exc


def _snapshot_from_extras(extras: Any) -> Optional[Dict[str, Any]]:
    if extras is None:
        return None

    data = extras
    if hasattr(data, "to_dict"):
        data = data.to_dict()

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return None

    if not isinstance(data, dict):
        return None

    snapshot = data.get("Snapshot") or data.get("snapshot")
    if isinstance(snapshot, str):
        try:
            snapshot = json.loads(snapshot)
        except json.JSONDecodeError:
            return None

    return snapshot if isinstance(snapshot, dict) else None


def _snapshot_from_name(name: Optional[str]) -> Optional[Dict[str, Any]]:
    if not name or "Snapshot" not in name:
        return None
    identifier = name.split("/")[-1]
    return {"id": identifier, "label": name}


def _coerce_coordinates(snapshot: Dict[str, Any], translation: Optional[Sequence[float]]) -> Optional[Tuple[float, float, float]]:
    coords = snapshot.get("coordinates") or snapshot.get("Coordinates")
    if isinstance(coords, dict):
        try:
            return (
                float(coords.get("x") or coords.get("X")),
                float(coords.get("y") or coords.get("Y")),
                float(coords.get("z") or coords.get("Z")),
            )
        except (TypeError, ValueError):
            return None

    if isinstance(coords, (list, tuple)) and len(coords) >= 3:
        try:
            return (float(coords[0]), float(coords[1]), float(coords[2]))
        except (TypeError, ValueError):
            return None

    if translation and len(translation) == 3:
        try:
            return (float(translation[0]), float(translation[1]), float(translation[2]))
        except (TypeError, ValueError):
            return None

    return None


def extract_snapshots(glb_path: Path) -> List[Dict[str, Any]]:
    gltf = GLTF2().load(glb_path)
    nodes = gltf.nodes or []
    snapshots: List[Dict[str, Any]] = []

    for idx, node in enumerate(nodes):
        snapshot = _snapshot_from_extras(getattr(node, "extras", None)) or _snapshot_from_name(getattr(node, "name", None))
        if not snapshot:
            continue

        coords = _coerce_coordinates(snapshot, getattr(node, "translation", None))
        if coords is None:
            continue

        snapshots.append(
            {
                "id": str(
                    snapshot.get("id")
                    or snapshot.get("Id")
                    or snapshot.get("ID")
                    or getattr(node, "name", None)
                    or f"snapshot_{idx}"
                ),
                "label": snapshot.get("label") or snapshot.get("description") or getattr(node, "name", "Snapshot"),
                "coordinates": {
                    "x": coords[0],
                    "y": coords[1],
                    "z": coords[2],
                },
            }
        )

    return snapshots


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Snapshot IDs and coordinates from a GLB/GTLF file")
    parser.add_argument("glb_file", type=Path, help="Path to the GLB/GTLF file")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable lines")
    args = parser.parse_args()

    if not args.glb_file.exists():
        raise SystemExit(f"File not found: {args.glb_file}")

    data = extract_snapshots(args.glb_file)

    if args.json:
        print(json.dumps(data, indent=2))
        return

    if not data:
        print("No Snapshot metadata found.")
        return

    for entry in data:
        coords = entry["coordinates"]
        print(
            f"{entry['id']}: X={coords['x']:.3f}, Y={coords['y']:.3f}, Z={coords['z']:.3f}"
            f" (label={entry['label']})"
        )


if __name__ == "__main__":
    main()
