#!/usr/bin/env python3
"""
Update existing defects with element data from GLB snapshot names
"""
import sqlite3
import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, '/usr/src/app')

try:
    from pygltflib import GLTF2
    from app.process_data.glb_snapshot import extract_snapshots
except ImportError:
    print("Error: pygltflib not installed")
    sys.exit(1)

# Get the database path
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'instance', 'ldms.db')
metadata_path = os.path.join(script_dir, 'instance', 'uploads', 'upload_data', 'latest_upload.json')

def update_defects_from_glb():
    # Load upload metadata
    if not os.path.exists(metadata_path):
        print(f"Metadata not found at {metadata_path}")
        return
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    glb_path = metadata.get('glb_path')
    if not glb_path or not os.path.exists(glb_path):
        print(f"GLB file not found: {glb_path}")
        return
    
    # Extract snapshots with element data
    print(f"Extracting snapshots from {glb_path}...")
    snapshots = extract_snapshots(glb_path)
    
    # Create mapping from snapshot ID to element
    snapshot_map = {}
    for snap in snapshots:
        snapshot_map[snap.snapshot_id] = snap.element
    
    print(f"Found {len(snapshots)} snapshots with element data")
    
    # Update database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all defects
    cursor.execute("SELECT id, description FROM defects WHERE element IS NULL")
    defects = cursor.fetchall()
    
    updated = 0
    for defect_id, description in defects:
        # Try to extract snapshot ID from description
        if 'Snapshot' in description:
            parts = description.split('/')
            if len(parts) >= 2:
                snapshot_id = parts[-1]
                element = snapshot_map.get(snapshot_id)
                if element:
                    cursor.execute("UPDATE defects SET element = ? WHERE id = ?", (element, defect_id))
                    updated += 1
                    print(f"  Updated defect {defect_id}: element = {element}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ Updated {updated} defects with element data")

if __name__ == '__main__':
    update_defects_from_glb()
