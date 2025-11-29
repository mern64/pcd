import json
import os
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

from .pdf_utils import extract_pdf_images

upload_data_bp = Blueprint("upload_data", __name__)

ALLOWED_GLB_EXT = {".glb"}
ALLOWED_PDF_EXT = {".pdf"}
METADATA_FILENAME = "latest_upload.json"

def _allowed_file(filename: str, allowed_exts) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_exts

@upload_data_bp.route("/upload-data", methods=["GET", "POST"])
def upload_scan_data():
    """
    Use Case DM_01: Upload Scan Data
    User: Homeowner / Inspector
    Goal: Upload the 3D GLB model and data file (PDF report) to the system.
    Precondition: None
    Postcondition: Files are stored, and automated data processing is initiated.
    """
    if request.method == "GET":
        return render_template("upload_data/upload.html")

    glb_file = request.files.get("glb_model")
    pdf_file = request.files.get("pdf_report")
    notes = request.form.get("notes", "")

    if not glb_file or glb_file.filename == "":
        flash("Please upload a GLB 3D model file.", "error")
        return redirect(request.url)

    if not pdf_file or pdf_file.filename == "":
        flash("Please upload a PDF report.", "error")
        return redirect(request.url)

    if not _allowed_file(glb_file.filename, ALLOWED_GLB_EXT):
        flash("Invalid 3D model file type. Only .glb is allowed.", "error")
        return redirect(request.url)

    if not _allowed_file(pdf_file.filename, ALLOWED_PDF_EXT):
        flash("Invalid report file type. Only .pdf is allowed.", "error")
        return redirect(request.url)

    upload_root = os.path.join(current_app.instance_path, "uploads", "upload_data")
    os.makedirs(upload_root, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    upload_id = f"upload_{timestamp}"
    image_dir = os.path.join(upload_root, f"{upload_id}_images")

    glb_name = secure_filename(glb_file.filename)
    pdf_name = secure_filename(pdf_file.filename)

    glb_path = os.path.join(upload_root, glb_name)
    pdf_path = os.path.join(upload_root, pdf_name)

    glb_file.save(glb_path)
    pdf_file.save(pdf_path)

    extracted_images = extract_pdf_images(pdf_path, image_dir)
    _persist_latest_upload_metadata(
        upload_root,
        {
            "id": upload_id,
            "created_at": timestamp,
            "glb_path": glb_path,
            "pdf_path": pdf_path,
            "image_dir": image_dir,
            "images": extracted_images,
            "assignments": {"defect_to_image": {}},
            "notes": notes,
        },
    )

    _start_automated_data_processing(glb_path, pdf_path, notes)

    flash("Scan data uploaded successfully. Automated processing has started.", "success")
    # Redirect to Module 2 (now process_data)
    return redirect(url_for("process_data.process_defect_file"))

def _start_automated_data_processing(glb_path: str, pdf_path: str, notes: str) -> None:
    current_app.logger.info("Starting automated processing for:")
    current_app.logger.info("GLB: %s", glb_path)
    current_app.logger.info("PDF: %s", pdf_path)
    if notes:
        current_app.logger.info("Notes: %s", notes)
    # TODO: implement real processing here


def _persist_latest_upload_metadata(upload_root: str, payload: dict) -> None:
    metadata_path = os.path.join(upload_root, METADATA_FILENAME)
    with open(metadata_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)