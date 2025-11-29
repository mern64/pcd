import os
import json
from dataclasses import dataclass
from typing import List, Optional
from flask import Blueprint, current_app, jsonify, render_template

process_data_bp = Blueprint("process_data", __name__)

@dataclass
class DefectRecord:
    id: str
    description: str
    x: float
    y: float
    z: float
    source_file: str

def _load_metaroom_defect_file() -> Optional[str]:
    processed_root = os.path.join(current_app.instance_path, "processed", "module1")
    defect_file = os.path.join(processed_root, "defects.json")
    if not os.path.exists(defect_file):
        current_app.logger.warning("Defect file not found at %s", defect_file)
        return None
    return defect_file

def _parse_defects_from_file(defect_filepath: str) -> List[DefectRecord]:
    with open(defect_filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_file = data.get("source_file", os.path.basename(defect_filepath))
    raw_defects = data.get("defects", [])

    defects: List[DefectRecord] = []
    for d in raw_defects:
        coords = d.get("coordinates", {})
        try:
            defects.append(
                DefectRecord(
                    id=str(d.get("id", "")),
                    description=str(d.get("description", "")),
                    x=float(coords.get("x", 0.0)),
                    y=float(coords.get("y", 0.0)),
                    z=float(coords.get("z", 0.0)),
                    source_file=source_file,
                )
            )
        except (TypeError, ValueError) as exc:
            current_app.logger.warning("Skipping defect with invalid coordinates: %s (%s)", d, exc)
    return defects

def _prepare_for_postgres(defects: List[DefectRecord]) -> List[dict]:
    prepared = []
    for d in defects:
        prepared.append(
            {
                "defect_id": d.id,
                "description": d.description,
                "x": d.x,
                "y": d.y,
                "z": d.z,
                "source_file": d.source_file,
                "wkt_point": f"POINT Z ({d.x} {d.y} {d.z})",
            }
        )
    return prepared

@process_data_bp.route("/process-data", methods=["GET"])
def process_defect_file():
    defect_filepath = _load_metaroom_defect_file()
    if defect_filepath is None:
        return render_template(
            "process_data/process_result.html",
            error="No defect file found. Ensure DM_01 has completed and produced a Metaroom data file.",
            defects=[],
            prepared_records=[],
        )

    defects = _parse_defects_from_file(defect_filepath)
    prepared_records = _prepare_for_postgres(defects)
    current_app.logger.info("Prepared %d defect records for PostgreSQL.", len(prepared_records))

    return render_template(
        "process_data/process_result.html",
        error=None,
        defects=defects,
        prepared_records=prepared_records,
    )

@process_data_bp.route("/process-data.json", methods=["GET"])
def process_defect_file_json():
    defect_filepath = _load_metaroom_defect_file()
    if defect_filepath is None:
        return jsonify(
            {"ok": False, "error": "No defect file found.", "records": []}
        ), 404

    defects = _parse_defects_from_file(defect_filepath)
    prepared_records = _prepare_for_postgres(defects)
    return jsonify({"ok": True, "count": len(prepared_records), "records": prepared_records})