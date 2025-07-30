"""
Add this endpoint to your FastAPI app to initialize the database
"""

from fastapi import HTTPException
import psycopg2
import os

def add_db_init_endpoint(app):
    @app.post("/api/init-database")
    async def init_database():
        """Initialize database with schema - run this once after deployment"""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
            
            # Read schema file
            schema_sql = """
            -- Database schema for job tracking application

            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

            -- Jobs table
            CREATE TABLE IF NOT EXISTS jobs (
                id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
                job_hash VARCHAR(32) UNIQUE NOT NULL,
                title VARCHAR(255) NOT NULL,
                company_name VARCHAR(255) NOT NULL,
                location VARCHAR(255),
                description TEXT,
                job_url TEXT,
                match_score INTEGER,
                ai_analysis TEXT,
                contacts JSONB,
                status VARCHAR(50) DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Job status tracking (applied, interviewing, rejected, etc.)
            CREATE TABLE IF NOT EXISTS job_actions (
                id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
                job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
                action_type VARCHAR(50) NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Contact tracking
            CREATE TABLE IF NOT EXISTS contacts (
                id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                company VARCHAR(255),
                linkedin_url TEXT,
                position VARCHAR(255),
                notes TEXT,
                last_contacted TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Link contacts to jobs
            CREATE TABLE IF NOT EXISTS job_contacts (
                job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
                contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
                relationship VARCHAR(100),
                PRIMARY KEY (job_id, contact_id)
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_jobs_match_score ON jobs(match_score DESC);
            CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
            CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_name);

            -- Update timestamp function
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';

            -- Update timestamp trigger
            DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
            CREATE TRIGGER update_jobs_updated_at 
                BEFORE UPDATE ON jobs 
                FOR EACH ROW 
                EXECUTE FUNCTION update_updated_at_column();
            """
            
            # Connect and execute schema
            conn = psycopg2.connect(database_url)
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()
            conn.close()
            
            return {"message": "✅ Database initialized successfully! Tables created."}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")