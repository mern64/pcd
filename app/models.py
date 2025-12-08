from app.extensions import db

class Scan(db.Model):
    __tablename__ = 'scans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    model_path = db.Column(db.String(500))  # Path to 3D model file
    created_at = db.Column(db.DateTime, default=db.func.now())

    defects = db.relationship('Defect', backref='scan', lazy=True)

class Defect(db.Model):
    __tablename__ = 'defects'
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    z = db.Column(db.Float, nullable=False)
    element = db.Column(db.String(255))  # Auto-populated from mesh name (non-editable)
    location = db.Column(db.String(100))  # Room/area location (editable dropdown)
    defect_type = db.Column(db.String(50), default='Unknown')  # crack, water damage, structural, finish, electrical, plumbing
    severity = db.Column(db.String(20), default='Medium')  # Low, Medium, High, Critical
    description = db.Column(db.Text)  # Auto-populated from mesh label (non-editable)
    status = db.Column(db.String(50), default='Reported')  # Reported, Under Review, Fixed
    image_path = db.Column(db.String(500))  # Path to snapshot image
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())