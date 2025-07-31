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
# Optional imports for Google Sheets functionality
try:
    from .job_sync_service import get_job_sync_service
    from .google_sheets_service import sheets_service
    GOOGLE_SHEETS_AVAILABLE = True
    print("✅ Google Sheets functionality enabled")
except ImportError as e:
    try:
        # Try without relative imports
        from job_sync_service import get_job_sync_service
        from google_sheets_service import sheets_service
        GOOGLE_SHEETS_AVAILABLE = True
        print("✅ Google Sheets functionality enabled")
    except ImportError as e2:
        print(f"⚠️  Google Sheets functionality disabled: {e2}")
        GOOGLE_SHEETS_AVAILABLE = False
        get_job_sync_service = None
        sheets_service = None

app = FastAPI(title="Job Search Tracker", version="1.0.0")

# CORS middleware for frontend - Allow all origins for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Set to False when using "*"
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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

class GoogleSheetsSync(BaseModel):
    spreadsheet_url: str

class GoogleSheetsResponse(BaseModel):
    success: bool
    message: str
    count: Optional[int] = None

@app.get("/")
async def root():
    return {"message": "Job Search Tracker API", "status": "online", "cors": "enabled"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running", "cors_test": "success"}

@app.get("/api/jobs")
async def get_jobs(
    limit: int = 50,
    status: Optional[str] = None,
    min_score: Optional[int] = None
):
    """Get all jobs with optional filtering"""
    try:
        print(f"🔍 /api/jobs called with params: limit={limit}, status={status}, min_score={min_score}")
        print(f"🔗 DATABASE_URL configured: {bool(DATABASE_URL)}")
        
        if not DATABASE_URL:
            print("❌ DATABASE_URL not configured")
            return JSONResponse(
                status_code=500,
                content={"error": "Database not configured", "detail": "DATABASE_URL environment variable not set"}
            )
        
        # Connect to database
        print(f"🔌 Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # First, check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'jobs'
                );
            """)
            table_exists = cur.fetchone()['exists']
            print(f"📋 Jobs table exists: {table_exists}")
            
            if not table_exists:
                conn.close()
                return JSONResponse(
                    status_code=500,
                    content={"error": "Database not initialized", "detail": "Jobs table does not exist. Please run /api/init-database first."}
                )
            
            # Build query
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
            
            print(f"📝 Executing query: {query}")
            print(f"🔢 With params: {params}")
            
            cur.execute(query, params)
            jobs = cur.fetchall()
            
            print(f"📊 Raw database results: {len(jobs)} jobs found")
            if jobs:
                print(f"📋 First job raw: {dict(jobs[0])}")
            
            # Convert to list of dicts and handle JSON fields
            result = []
            for job in jobs:
                job_dict = dict(job)
                if job_dict['contacts'] is None:
                    job_dict['contacts'] = []
                result.append(job_dict)
            
            conn.close()
            
            print(f"✅ Returning {len(result)} jobs to frontend")
            if result:
                print(f"📋 First job processed keys: {list(result[0].keys())}")
                
            return result
            
    except psycopg2.Error as db_error:
        print(f"❌ Database connection/query error: {str(db_error)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Database error", "detail": str(db_error)}
        )
    except Exception as e:
        print(f"❌ General error in /api/jobs: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

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
        import os
        
        # Get the correct path to the job search script
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "job_search_agent.py")
        
        print(f"🔍 Looking for script at: {script_path}")
        print(f"📁 Current working directory: {os.getcwd()}")
        print(f"📂 Script exists: {os.path.exists(script_path)}")
        
        # Run the job search script
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print(f"🏁 Script finished with return code: {result.returncode}")
        print(f"📝 Output: {result.stdout[:500]}...")  # First 500 chars
        if result.stderr:
            print(f"❌ Errors: {result.stderr[:500]}...")
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Search timed out after 5 minutes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running search: {str(e)}")

@app.get("/api/sheets/status")
async def get_sheets_status():
    """Check Google Sheets API status"""
    if not GOOGLE_SHEETS_AVAILABLE:
        return {
            "available": False,
            "message": "Google Sheets modules not available - check deployment"
        }
    
    return {
        "available": sheets_service.is_available(),
        "message": "Google Sheets API is ready" if sheets_service.is_available() else "Google Sheets API not configured"
    }

@app.post("/api/sheets/sync-to-sheets", response_model=GoogleSheetsResponse)
async def sync_jobs_to_sheets(request: GoogleSheetsSync):
    """Sync all jobs from database to Google Sheets"""
    if not GOOGLE_SHEETS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Google Sheets functionality not available")
    
    try:
        if not DATABASE_URL:
            raise HTTPException(status_code=500, detail="Database not configured")
        
        sync_service = get_job_sync_service(DATABASE_URL)
        success, message = sync_service.sync_jobs_to_sheets(request.spreadsheet_url)
        
        if success:
            return GoogleSheetsResponse(success=True, message=message)
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

@app.post("/api/sheets/import-from-sheets", response_model=GoogleSheetsResponse)
async def import_jobs_from_sheets(request: GoogleSheetsSync):
    """Import jobs from Google Sheets to database"""
    if not GOOGLE_SHEETS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Google Sheets functionality not available")
    
    try:
        if not DATABASE_URL:
            raise HTTPException(status_code=500, detail="Database not configured")
        
        sync_service = get_job_sync_service(DATABASE_URL)
        success, message, count = sync_service.import_jobs_from_sheets(request.spreadsheet_url)
        
        if success:
            return GoogleSheetsResponse(success=True, message=message, count=count)
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)