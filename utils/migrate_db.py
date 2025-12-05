#!/usr/bin/env python3
"""
Database migration script to add element, defect_type, and severity columns to defects table
"""
import sqlite3
import os

# Get the database path
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'instance', 'ldms.db')

def migrate():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(defects)")
    columns = [row[1] for row in cursor.fetchall()]
    
    migrations_run = []
    
    # Add element column
    if 'element' not in columns:
        print("Adding 'element' column...")
        cursor.execute("ALTER TABLE defects ADD COLUMN element VARCHAR(255)")
        migrations_run.append("element")
    
    # Add location column
    if 'location' not in columns:
        print("Adding 'location' column...")
        cursor.execute("ALTER TABLE defects ADD COLUMN location VARCHAR(100)")
        migrations_run.append("location")
    
    # Add defect_type column
    if 'defect_type' not in columns:
        print("Adding 'defect_type' column...")
        cursor.execute("ALTER TABLE defects ADD COLUMN defect_type VARCHAR(50) DEFAULT 'Unknown'")
        migrations_run.append("defect_type")
    
    # Add severity column
    if 'severity' not in columns:
        print("Adding 'severity' column...")
        cursor.execute("ALTER TABLE defects ADD COLUMN severity VARCHAR(20) DEFAULT 'Medium'")
        migrations_run.append("severity")
    
    conn.commit()
    conn.close()
    
    if migrations_run:
        print(f"\n✓ Migration completed successfully! Added columns: {', '.join(migrations_run)}")
    else:
        print("\n✓ All columns already exist. No migration needed.")

if __name__ == '__main__':
    migrate()
