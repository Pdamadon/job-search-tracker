#!/usr/bin/env python3
"""
Database setup script - run this after deployment to create tables
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    """Create database tables"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Read schema file
        with open('schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Connect to database
        print("🔗 Connecting to database...")
        conn = psycopg2.connect(database_url)
        
        # Execute schema
        print("📝 Creating tables...")
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        
        conn.commit()
        conn.close()
        
        print("✅ Database setup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    setup_database()