from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import uvicorn

app = FastAPI(title="Job Search Tracker", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()

# Pydantic models
class JobResponse(BaseModel):
    id: str
    title: str
    company_name: str
    location: Optional[str]
    description: Optional[str]
    job_url: Optional[str]
    match_score: Optional[int]
    ai_analysis: Optional[str]
    contacts: Optional[dict]
    status: str
    created_at: datetime
    updated_at: datetime

class JobAction(BaseModel):
    action_type: str
    notes: Optional[str] = None

class ContactCreate(BaseModel):
    name: str
    company: Optional[str]
    linkedin_url: Optional[str]
    position: Optional[str]
    notes: Optional[str]

@app.get("/")
async def root():
    return {"message": "Job Search Tracker API"}

@app.get("/api/jobs", response_model=List[JobResponse])
async def get_jobs(
    limit: int = 50,
    status: Optional[str] = None,
    min_score: Optional[int] = None,
    conn = Depends(get_db)
):
    """Get all jobs with optional filtering"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT * FROM jobs 
                WHERE 1=1
            """
            params = []
            
            if status:
                query += " AND status = %s"
                params.append(status)
                
            if min_score:
                query += " AND match_score >= %s"
                params.append(min_score)
                
            query += " ORDER BY match_score DESC, created_at DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            jobs = cur.fetchall()
            
            # Convert to list of dicts and handle JSON fields
            result = []
            for job in jobs:
                job_dict = dict(job)
                if job_dict['contacts'] is None:
                    job_dict['contacts'] = []
                result.append(job_dict)
                
            return result
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, conn = Depends(get_db)):
    """Get single job by ID"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
            job = cur.fetchone()
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
                
            job_dict = dict(job)
            if job_dict['contacts'] is None:
                job_dict['contacts'] = []
                
            return job_dict
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/api/jobs/{job_id}/status")
async def update_job_status(
    job_id: str, 
    action: JobAction,
    conn = Depends(get_db)
):
    """Update job status and add action"""
    try:
        with conn.cursor() as cur:
            # Update job status
            cur.execute(
                "UPDATE jobs SET status = %s WHERE id = %s",
                (action.action_type, job_id)
            )
            
            # Add action record
            cur.execute("""
                INSERT INTO job_actions (job_id, action_type, notes)
                VALUES (%s, %s, %s)
            """, (job_id, action.action_type, action.notes))
            
            conn.commit()
            
            return {"message": "Job status updated successfully"}
            
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/stats")
async def get_stats(conn = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Total jobs
            cur.execute("SELECT COUNT(*) as total FROM jobs")
            total_jobs = cur.fetchone()['total']
            
            # Jobs by status
            cur.execute("""
                SELECT status, COUNT(*) as count 
                FROM jobs 
                GROUP BY status 
                ORDER BY count DESC
            """)
            status_counts = cur.fetchall()
            
            # Average match score
            cur.execute("SELECT AVG(match_score) as avg_score FROM jobs WHERE match_score IS NOT NULL")
            avg_score = cur.fetchone()['avg_score']
            
            # Top companies
            cur.execute("""
                SELECT company_name, COUNT(*) as count 
                FROM jobs 
                GROUP BY company_name 
                ORDER BY count DESC 
                LIMIT 10
            """)
            top_companies = cur.fetchall()
            
            return {
                "total_jobs": total_jobs,
                "status_counts": [dict(row) for row in status_counts],
                "avg_match_score": float(avg_score) if avg_score else 0,
                "top_companies": [dict(row) for row in top_companies]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/init-database")
async def init_database():
    """Initialize database with schema - run this once after deployment"""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
        
        # Schema SQL
        schema_sql = """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

        CREATE TABLE IF NOT EXISTS job_actions (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
            action_type VARCHAR(50) NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

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

        CREATE TABLE IF NOT EXISTS job_contacts (
            job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
            contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
            relationship VARCHAR(100),
            PRIMARY KEY (job_id, contact_id)
        );

        CREATE INDEX IF NOT EXISTS idx_jobs_match_score ON jobs(match_score DESC);
        CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
        CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_name);

        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';

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

@app.post("/api/run-search")
async def run_job_search():
    """Trigger job search script"""
    try:
        import subprocess
        result = subprocess.run(
            ["python", "job_search_agent.py"],
            capture_output=True,
            text=True,
            cwd=".."
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running search: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)