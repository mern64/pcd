#!/usr/bin/env python3
"""
Migration script to add priority column to defects table.
Run this once to update your existing database (SQLite file: instance/ldms.db).
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db

def add_priority_column():
    """Add priority column to defects table if it doesn't exist"""
    app = create_app()
    
    with app.app_context():
        try:
            # Try to add the column
            with db.engine.connect() as conn:
                # Check if column exists
                result = conn.execute(db.text(
                    "SELECT COUNT(*) FROM pragma_table_info('defects') WHERE name='priority'"
                ))
                exists = result.scalar() > 0
                
                if not exists:
                    print("Adding 'priority' column to defects table...")
                    conn.execute(db.text(
                        "ALTER TABLE defects ADD COLUMN priority VARCHAR(20) DEFAULT 'Medium'"
                    ))
                    conn.commit()
                    print("✓ Successfully added 'priority' column with default value 'Medium'")
                else:
                    print("✓ 'priority' column already exists")
                    
        except Exception as e:
            print(f"Error adding column: {e}")
            print("\nAlternative: Drop and recreate the database:")
            print("  1. Delete instance/ldms.db")
            print("  2. Restart the application (tables will be recreated)")

if __name__ == '__main__':
    add_priority_column()
