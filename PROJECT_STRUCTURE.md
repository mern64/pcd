# LIDAR Defect Viewer - Project Structure

## 📁 Directory Overview

```
/usr/src/app/
├── app/                          # Main application package
│   ├── __init__.py              # Flask app initialization
│   ├── config.py                # Configuration settings
│   ├── extensions.py            # Flask extensions (SQLAlchemy)
│   ├── models.py                # Database models (Scan, Defect)
│   │
│   ├── defects/                 # Defect visualization & management
│   │   ├── __init__.py
│   │   └── routes.py            # Routes: /projects, /scans/<id>/visualize
│   │
│   ├── upload_data/             # File upload module
│   │   ├── __init__.py
│   │   ├── routes.py            # Route: /upload-data
│   │   └── pdf_utils.py         # PDF image extraction utilities
│   │
│   ├── process_data/            # Defect processing module
│   │   ├── __init__.py
│   │   ├── routes.py            # Route: /process-data
│   │   └── glb_snapshot.py      # GLB 3D model parsing utilities
│   │
│   └── templates/               # HTML templates
│       ├── defects/
│       │   ├── projects.html    # Projects listing page
│       │   └── visualization.html # 3D visualization viewer
│       ├── upload_data/
│       │   └── upload.html      # Upload form
│       └── process_data/
│           └── process_result.html # Review & link images
│
├── instance/                     # Runtime data (not in git)
│   ├── ldms.db                  # SQLite database
│   ├── uploads/                 # Uploaded files
│   │   └── upload_data/
│   │       ├── latest_upload.json
│   │       ├── *.glb            # 3D model files
│   │       ├── *.pdf            # Report PDFs
│   │       └── *_images/        # Extracted images
│   └── processed/               # Processed data cache
│
├── utils/                        # Utility scripts
│   ├── migrate_db.py            # Database migration script
│   └── update_defect_elements.py # Batch update script
│
├── PBR_IMPLEMENTATION.md        # PBR materials technical documentation
├── PBR_QUICKSTART.md            # Quick reference for PBR setup
├── docker-compose.yml           # Docker composition
├── Dockerfile                   # Docker image definition
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## 🔄 Application Flow

### 1. **Projects Page** (`/` or `/projects`)
- **File:** `app/defects/routes.py` → `list_projects()`
- **Template:** `app/templates/defects/projects.html`
- **Purpose:** Display all scans/projects from database
- **User Action:** Click on a project card

### 2. **Upload New Scan** (`/upload-data`)
- **File:** `app/upload_data/routes.py` → `upload_scan_data()`
- **Template:** `app/templates/upload_data/upload.html`
- **Purpose:** Upload GLB model + PDF report
- **User Action:** Submit form → Redirects to Process

### 3. **Process Scan** (`/process-data`)
- **File:** `app/process_data/routes.py` → `process_defect_file()`
- **Template:** `app/templates/process_data/process_result.html`
- **Purpose:** Review extracted defects, link images
- **User Action:** Save to database → Redirects to Visualization

### 4. **Visualization Viewer** (`/scans/<id>/visualize`)
- **File:** `app/defects/routes.py` → `visualize_scan()`
- **Template:** `app/templates/defects/visualization.html`
- **Purpose:** Full-page 3D viewer with Babylon.js
- **Features:**
  - 3D model rendering
  - Defect markers (color-coded by severity)
  - Edit defects (location, type, severity, notes)
  - X-ray mode, camera controls, theme toggle

---

## 🗄️ Database Models

### `Scan` (Table: `scans`)
- `id` - Primary key
- `name` - Scan/project name
- `model_path` - Path to GLB file
- `created_at` - Timestamp

### `Defect` (Table: `defects`)
- `id` - Primary key
- `scan_id` - Foreign key to Scan
- `x, y, z` - 3D coordinates
- `element` - Building element (from GLB)
- `location` - Room/area (dropdown: Kitchen, Bedroom, etc.)
- `defect_type` - Type (Crack, Water Damage, Structural, etc.)
- `severity` - Low, Medium, High, Critical
- `description` - Auto-populated from GLB
- `status` - Reported, Under Review, Fixed
- `image_path` - Path to defect image
- `notes` - User notes
- `created_at`, `updated_at` - Timestamps

---

## 📦 Key Dependencies

- **Flask** - Web framework
- **SQLAlchemy** - ORM for database
- **pygltflib** - Parse GLB 3D models
- **PyPDF2** - Extract images from PDFs
- **Pillow** - Image processing
- **Babylon.js 8.40.1** (CDN) - 3D rendering with PBR materials

---

## 🎨 3D Rendering Features

### PBR Materials System
Physically Based Rendering (PBR) materials for photorealistic visualization:
- **HDRI Environment Lighting**: Image-Based Lighting (IBL) for realistic reflections
- **10 Material Recipes**: Optimized for walls, floors, glass, metal, wood
- **Auto-Assignment**: Detects IFC element types and applies appropriate materials
- **X-Ray Mode Compatible**: Preserves transparency functionality

**Documentation**:
- Technical details: `PBR_IMPLEMENTATION.md`
- Quick start guide: `PBR_QUICKSTART.md`

**Material Examples**:
- Walls (plaster): Matte finish, roughness 0.95
- Windows (glass): 40% transparent, high reflectivity, metallic 0.9
- Sinks (steel): Polished metal, metallic 1.0, roughness 0.2
- Floors (wood): Semi-matte, roughness 0.7

---

## 🛠️ Utility Scripts

Located in `utils/` folder:

### `migrate_db.py`
Add new columns to database schema:
```bash
python utils/migrate_db.py
```

### `update_defect_elements.py`
Batch update defect elements from GLB files:
```bash
python utils/update_defect_elements.py
```

---

## 🚀 Running the Application

### Development:
```bash
flask run
```

### Docker:
```bash
docker-compose up
```

Access at: `http://localhost:5000`

---

## 📝 Module Descriptions

### `app/defects/`
Handles defect visualization and project listing. Main routes:
- GET `/projects` - List all scans
- GET `/scans/<id>/visualize` - 3D viewer
- GET `/scans/<id>/defects` - API: Get defects for scan
- GET `/defect/<id>` - API: Get defect details
- PUT `/defect/<id>/status` - API: Update defect

### `app/upload_data/`
Handles file uploads and metadata collection. Uses Google Maps API for address autocomplete.

### `app/process_data/`
Parses GLB models to extract defect snapshots, extracts images from PDFs, allows linking images to defects before saving to database.

### `app/templates/`
Jinja2 HTML templates with embedded CSS and JavaScript. All pages use a light card-style design for consistency.

---

## 🎨 Design System

- **Font:** system-ui (native system font)
- **Colors:**
  - Primary: `#3b82f6` (blue)
  - Background: `#f3f4f6` (light gray)
  - Card: `#ffffff` (white)
  - Dark mode: `#0f172a`, `#1e293b` backgrounds
- **Icons:** Font Awesome 6.4.0
- **3D Engine:** Babylon.js 8.40.1

---

## 📂 Upload Data Storage

All uploads stored in `instance/uploads/upload_data/`:
- GLB files: `*.glb`
- PDF reports: `*.pdf`
- Extracted images: `upload_YYYYMMDDHHMMSS_images/`
- Metadata: `latest_upload.json`

---

## 🔐 Instance Folder

The `instance/` folder contains runtime data:
- SQLite database (`ldms.db`)
- Uploaded files
- Processed data cache

**Note:** This folder is in `.gitignore` and not committed to version control.

---

## 📱 Responsive Design

Visualization page uses full viewport height with flexbox layout:
- Navbar (top, fixed height)
- Project info banner (top, fixed height)
- Main container (fills remaining space)
  - 3D viewer (flex-grow)
  - Sidebar (fixed 320px width)
