#!/usr/bin/env python3
"""
Database migration script for Google OAuth integration
Adds google_id column to users table
"""

import sqlite3
import os
import sys
from pathlib import Path

def migrate_database():
    """Add google_id column to existing database"""
    db_path = 'agentic_crm.db'
    
    if not os.path.exists(db_path):
        print("Database doesn't exist yet - will be created with new schema")
        return True
    
    print(f"Migrating database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if google_id column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'google_id' in columns:
            print("google_id column already exists - migration not needed")
            conn.close()
            return True
        
        # Add google_id column
        print("Adding google_id column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN google_id VARCHAR(100) UNIQUE")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
