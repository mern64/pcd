import glob
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from .glb_snapshot import SnapshotRecord, extract_snapshots

try:
    from pygltflib import GLTF2
except ImportError:  # pragma: no cover
    GLTF2 = None


process_data_bp = Blueprint("process_data", __name__)


@dataclass
class DefectRecord:
    id: str
    description: str
    x: float
    y: float
    z: float
    source_file: str


def _processed_root() -> str:
    return os.path.join(current_app.instance_path, "processed", "module1")


def _upload_root() -> str:
    return os.path.join(current_app.instance_path, "uploads", "upload_data")


def _metadata_path() -> str:
    return os.path.join(_upload_root(), "latest_upload.json")


def _glb_search_directories() -> List[str]:
    return [_processed_root(), _upload_root()]


def _load_glb_defect_file() -> Optional[str]:
    candidates: List[str] = []
    for directory in _glb_search_directories():
        if not os.path.isdir(directory):
            continue
        for pattern in ("*.glb", "*.gltf"):
            candidates.extend(glob.glob(os.path.join(directory, pattern)))

    if not candidates:
        return None

    latest = max(candidates, key=os.path.getmtime)
    current_app.logger.info("Using GLB/GTLF file %s for defect extraction", latest)
    return latest


def _load_metaroom_defect_file() -> Optional[str]:
    defect_file = os.path.join(_processed_root(), "defects.json")
    if not os.path.exists(defect_file):
        current_app.logger.warning("Defect JSON not found at %s", defect_file)
        return None
    return defect_file


def _parse_defects_from_file(defect_filepath: str) -> List[DefectRecord]:
    with open(defect_filepath, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    source_file = data.get("source_file", os.path.basename(defect_filepath))
    raw_defects = data.get("defects", [])

    defects: List[DefectRecord] = []
    for entry in raw_defects:
        coords = entry.get("coordinates", {})
        try:
            defects.append(
                DefectRecord(
                    id=str(entry.get("id", "")),
                    description=str(entry.get("description", "")),
                    x=float(coords.get("x", 0.0)),
                    y=float(coords.get("y", 0.0)),
                    z=float(coords.get("z", 0.0)),
                    source_file=source_file,
                )
            )
        except (TypeError, ValueError) as exc:
            current_app.logger.warning("Skipping defect with invalid coordinates: %s (%s)", entry, exc)
    return defects


def _prepare_for_postgres(defects: List[DefectRecord]) -> List[dict]:
    prepared: List[dict] = []
    for record in defects:
        prepared.append(
            {
                "defect_id": record.id,
                "description": record.description,
                "x": record.x,
                "y": record.y,
                "z": record.z,
                "source_file": record.source_file,
                "wkt_point": f"POINT Z ({record.x} {record.y} {record.z})",
            }
        )
    return prepared


def _parse_defects_from_glb(defect_filepath: str) -> List[DefectRecord]:
    if GLTF2 is None:
        raise RuntimeError("pygltflib is not installed; cannot parse GLB defects")

    snapshots: List[SnapshotRecord] = extract_snapshots(defect_filepath)
    defects: List[DefectRecord] = []
    for snapshot in snapshots:
        defects.append(
            DefectRecord(
                id=snapshot.snapshot_id,
                description=snapshot.label,
                x=snapshot.coordinates[0],
                y=snapshot.coordinates[1],
                z=snapshot.coordinates[2],
                source_file=os.path.basename(defect_filepath),
            )
        )
    return defects


def _load_defects() -> Tuple[List[DefectRecord], Optional[str], str]:
    glb_file = _load_glb_defect_file()
    if glb_file:
        try:
            defects = _parse_defects_from_glb(glb_file)
            if defects:
                return defects, glb_file, "glb"
            current_app.logger.warning("No snapshot metadata found in %s", glb_file)
        except Exception as exc:  # noqa: BLE001
            current_app.logger.exception("Failed to parse GLB defects from %s: %s", glb_file, exc)

    json_file = _load_metaroom_defect_file()
    if json_file:
        try:
            defects = _parse_defects_from_file(json_file)
            return defects, json_file, "json"
        except Exception as exc:  # noqa: BLE001
            current_app.logger.exception("Failed to parse JSON defects from %s: %s", json_file, exc)

    return [], None, "none"


def _load_latest_metadata() -> Optional[dict]:
    metadata_file = _metadata_path()
    if not os.path.exists(metadata_file):
        return None
    try:
        with open(metadata_file, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        current_app.logger.error("Unable to load upload metadata: %s", exc)
        return None


def _save_latest_metadata(metadata: dict) -> None:
    metadata_file = _metadata_path()
    os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
    with open(metadata_file, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)


def _defect_assignments_map(metadata: Optional[dict]) -> Dict[str, str]:
    if not metadata:
        return {}
    assignments = metadata.get("assignments") or {}
    mapping = assignments.get("defect_to_image") or {}
    return {str(defect_id): str(image_id) for defect_id, image_id in mapping.items() if image_id}


def _image_entries(metadata: Optional[dict]) -> List[dict]:
    if not metadata:
        return []
    defect_map = _defect_assignments_map(metadata)
    image_to_defect = {image_id: defect_id for defect_id, image_id in defect_map.items()}
    entries: List[dict] = []
    for image in metadata.get("images", []):
        image_id = str(image.get("id"))
        entries.append(
            {
                "id": image_id,
                "file": image.get("file"),
                "page": image.get("page"),
                "width": image.get("width"),
                "height": image.get("height"),
                "assigned_defect": image_to_defect.get(image_id),
            }
        )
    return entries


def _resolve_image(metadata: dict, image_id: str) -> Optional[Tuple[str, str]]:
    image_dir = metadata.get("image_dir")
    if not image_dir:
        return None
    for image in metadata.get("images", []):
        if str(image.get("id")) == image_id:
            filename = image.get("file")
            if filename:
                return image_dir, filename
    return None


def _render_error(message: str):
    return render_template(
        "process_data/process_result.html",
        error=message,
        defects=[],
        prepared_records=[],
        image_entries=[],
        defect_assignments={},
    )


@process_data_bp.route("/process-data", methods=["GET"])
def process_defect_file():
    defects, source_path, source_kind = _load_defects()
    metadata = _load_latest_metadata()
    image_entries = _image_entries(metadata)
    defect_assignments = _defect_assignments_map(metadata)

    if not source_path:
        return _render_error(
            "No GLB/JSON defect file found. Ensure the processed folder contains either a Snapshot-enabled GLB or defects.json."
        )

    for entry in image_entries:
        entry["url"] = url_for("process_data.serve_extracted_image", image_id=entry["id"])

    prepared_records = _prepare_for_postgres(defects)
    current_app.logger.info(
        "Prepared %d defect records for PostgreSQL from %s (%s).",
        len(prepared_records),
        source_path,
        source_kind,
    )

    error = None
    if not defects and source_kind == "glb":
        error = "No Snapshot metadata found inside the GLB file."

    return render_template(
        "process_data/process_result.html",
        error=error,
        defects=defects,
        prepared_records=prepared_records,
        image_entries=image_entries,
        defect_assignments=defect_assignments,
    )


@process_data_bp.route("/process-data.json", methods=["GET"])
def process_defect_file_json():
    defects, source_path, source_kind = _load_defects()
    metadata = _load_latest_metadata()
    image_entries = _image_entries(metadata)
    defect_assignments = _defect_assignments_map(metadata)

    if not source_path:
        return jsonify({"ok": False, "error": "No GLB/JSON defect file found.", "records": []}), 404

    for entry in image_entries:
        entry["url"] = url_for("process_data.serve_extracted_image", image_id=entry["id"])

    prepared_records = _prepare_for_postgres(defects)
    return jsonify(
        {
            "ok": True,
            "count": len(prepared_records),
            "source": source_kind,
            "records": prepared_records,
            "images": image_entries,
            "assignments": defect_assignments,
        }
    )


@process_data_bp.route("/process-data/image/<image_id>", methods=["GET"])
def serve_extracted_image(image_id: str):
    metadata = _load_latest_metadata()
    if not metadata:
        abort(404)

    resolved = _resolve_image(metadata, image_id)
    if not resolved:
        abort(404)

    image_dir, filename = resolved
    image_dir = os.path.abspath(image_dir)
    image_path = os.path.abspath(os.path.join(image_dir, filename))
    if os.path.commonpath([image_dir, image_path]) != image_dir:
        abort(404)
    if not os.path.exists(image_path):
        abort(404)

    return send_from_directory(image_dir, filename)


@process_data_bp.route("/process-data/assign-image", methods=["POST"])
def assign_image_to_defect():
    metadata = _load_latest_metadata()
    if not metadata:
        flash("No upload metadata available. Upload a GLB/PDF first.", "error")
        return redirect(url_for("process_data.process_defect_file"))

    action = request.form.get("action", "assign")
    image_id = request.form.get("image_id")
    defect_id = request.form.get("defect_id")

    if not image_id:
        flash("Missing image selection.", "error")
        return redirect(url_for("process_data.process_defect_file"))

    assignments = metadata.setdefault("assignments", {}).setdefault("defect_to_image", {})

    if not _resolve_image(metadata, image_id):
        flash("Selected image is no longer available.", "error")
        return redirect(url_for("process_data.process_defect_file"))

    if action == "unassign":
        removed = False
        for defect_key, assigned_image in list(assignments.items()):
            if assigned_image == image_id:
                assignments.pop(defect_key)
                removed = True
        if removed:
            flash("Image unassigned from defect.", "success")
        else:
            flash("Image was not assigned.", "info")
    else:
        if not defect_id:
            flash("Select a defect before assigning an image.", "error")
            return redirect(url_for("process_data.process_defect_file"))

        for defect_key, assigned_image in list(assignments.items()):
            if defect_key == defect_id or assigned_image == image_id:
                assignments.pop(defect_key)
        assignments[defect_id] = image_id
        flash(f"Linked image to defect {defect_id}.", "success")

    _save_latest_metadata(metadata)
    return redirect(url_for("process_data.process_defect_file"))
