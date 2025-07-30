from typing import List, Dict, Optional, Tuple
import re
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from google_sheets_service import sheets_service
import logging

logger = logging.getLogger(__name__)

class JobSyncService:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.spreadsheet_headers = [
            'Company', 'Position', 'Location', 'Job URL', 'Match Score', 
            'Status', 'Date Added', 'AI Analysis', 'LinkedIn Contacts', 'Notes'
        ]
    
    def extract_spreadsheet_id(self, sheets_url: str) -> Optional[str]:
        """Extract spreadsheet ID from Google Sheets URL"""
        pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, sheets_url)
        return match.group(1) if match else None
    
    def get_jobs_from_database(self) -> List[Dict]:
        """Fetch all jobs from database"""
        try:
            conn = psycopg2.connect(self.database_url)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM jobs 
                    ORDER BY created_at DESC
                """)
                jobs = cur.fetchall()
                conn.close()
                
                return [dict(job) for job in jobs]
                
        except Exception as e:
            logger.error(f"Error fetching jobs from database: {str(e)}")
            return []
    
    def jobs_to_sheet_format(self, jobs: List[Dict]) -> List[List[str]]:
        """Convert database jobs to spreadsheet format"""
        rows = [self.spreadsheet_headers]  # Header row
        
        for job in jobs:
            # Extract contacts as a string
            contacts_text = ""
            if job.get('contacts') and isinstance(job['contacts'], list):
                contact_names = [contact.get('name', 'Unknown') for contact in job['contacts']]
                contacts_text = ', '.join(contact_names)
            
            # Format date
            date_added = ""
            if job.get('created_at'):
                if isinstance(job['created_at'], datetime):
                    date_added = job['created_at'].strftime('%Y-%m-%d')
                else:
                    date_added = str(job['created_at'])[:10]  # Take first 10 chars (YYYY-MM-DD)
            
            row = [
                job.get('company_name', ''),
                job.get('title', ''),
                job.get('location', ''),
                job.get('job_url', ''),
                str(job.get('match_score', '')),
                job.get('status', ''),
                date_added,
                job.get('ai_analysis', ''),
                contacts_text,
                ''  # Notes column - empty for now
            ]
            rows.append(row)
        
        return rows
    
    def sync_jobs_to_sheets(self, spreadsheet_url: str) -> Tuple[bool, str]:
        """
        Sync all jobs from database to Google Sheets
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not sheets_service.is_available():
            return False, "Google Sheets service not available. Please configure service account credentials."
        
        spreadsheet_id = self.extract_spreadsheet_id(spreadsheet_url)
        if not spreadsheet_id:
            return False, "Invalid Google Sheets URL. Please provide a valid spreadsheet URL."
        
        try:
            # Get jobs from database
            jobs = self.get_jobs_from_database()
            if not jobs:
                return False, "No jobs found in database to sync."
            
            # Convert to sheet format
            sheet_data = self.jobs_to_sheet_format(jobs)
            
            # Clear existing data (except headers if we want to keep them)
            # First, let's try to write to a specific range
            range_name = 'Sheet1!A:J'  # Columns A through J
            
            # Write data to spreadsheet
            success = sheets_service.write_to_spreadsheet(
                spreadsheet_id=spreadsheet_id,
                range_name=range_name,
                values=sheet_data,
                value_input_option='USER_ENTERED'
            )
            
            if success:
                return True, f"Successfully synced {len(jobs)} jobs to Google Sheets."
            else:
                return False, "Failed to write data to Google Sheets. Check permissions and spreadsheet ID."
                
        except Exception as e:
            logger.error(f"Error syncing jobs to sheets: {str(e)}")
            return False, f"Error during sync: {str(e)}"
    
    def import_jobs_from_sheets(self, spreadsheet_url: str) -> Tuple[bool, str, int]:
        """
        Import jobs from Google Sheets to database
        
        Returns:
            Tuple of (success: bool, message: str, imported_count: int)
        """
        if not sheets_service.is_available():
            return False, "Google Sheets service not available.", 0
        
        spreadsheet_id = self.extract_spreadsheet_id(spreadsheet_url)
        if not spreadsheet_id:
            return False, "Invalid Google Sheets URL.", 0
        
        try:
            # Read data from spreadsheet
            sheet_data = sheets_service.get_spreadsheet_data(
                spreadsheet_id=spreadsheet_id,
                range_name='Sheet1!A:J'
            )
            
            if not sheet_data or len(sheet_data) < 2:
                return False, "No data found in spreadsheet or only headers present.", 0
            
            # Skip header row
            data_rows = sheet_data[1:]
            imported_count = 0
            
            conn = psycopg2.connect(self.database_url)
            
            for row in data_rows:
                # Pad row if it has fewer columns
                while len(row) < 10:
                    row.append('')
                
                company = row[0].strip() if row[0] else ''
                title = row[1].strip() if row[1] else ''
                location = row[2].strip() if row[2] else ''
                job_url = row[3].strip() if row[3] else ''
                match_score = None
                status = row[5].strip() if row[5] else 'new'
                ai_analysis = row[7].strip() if row[7] else ''
                
                # Skip empty rows
                if not company and not title:
                    continue
                
                # Parse match score
                try:
                    if row[4] and row[4].strip():
                        match_score = int(row[4].strip())
                except (ValueError, IndexError):
                    match_score = None
                
                # Create job hash for deduplication
                job_hash = f"{company}_{title}_{location}".lower().replace(' ', '_')
                job_hash = re.sub(r'[^a-z0-9_]', '', job_hash)[:32]
                
                try:
                    with conn.cursor() as cur:
                        # Check if job already exists
                        cur.execute("SELECT id FROM jobs WHERE job_hash = %s", (job_hash,))
                        if cur.fetchone():
                            logger.info(f"Job already exists: {company} - {title}")
                            continue
                        
                        # Insert new job
                        cur.execute("""
                            INSERT INTO jobs (job_hash, title, company_name, location, 
                                            job_url, match_score, ai_analysis, status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (job_hash, title, company, location, job_url, 
                              match_score, ai_analysis, status))
                        
                        imported_count += 1
                        logger.info(f"Imported job: {company} - {title}")
                
                except psycopg2.Error as e:
                    logger.error(f"Error importing job {company} - {title}: {str(e)}")
                    continue
            
            conn.commit()
            conn.close()
            
            return True, f"Successfully imported {imported_count} jobs from Google Sheets.", imported_count
            
        except Exception as e:
            logger.error(f"Error importing jobs from sheets: {str(e)}")
            return False, f"Error during import: {str(e)}", 0

# Global instance - will be initialized when needed
job_sync_service = None

def get_job_sync_service(database_url: str) -> JobSyncService:
    """Get or create job sync service instance"""
    global job_sync_service
    if job_sync_service is None:
        job_sync_service = JobSyncService(database_url)
    return job_sync_service