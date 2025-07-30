import os
import json
import hashlib
from datetime import datetime
from openai import OpenAI
from serpapi import GoogleSearch
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

user_profile = {
    "title_keywords": ["senior product manager", "principal product manager", "founding product manager", "chief of staff", "head of operations", "general manager"],
    "locations": ["remote", "seattle", "san francisco", "new york"],
    "industries": ["AI productivity tools", "consumer tech", "marketplaces", "wearables", "fitness tech", "creative tech", "creator economy", "consumer fintech", "travel", "digital health B2C"],
    "experience_level": "senior",
    "background": "MBA, 8+ years experience, healthcare data, Amazon, Expert Network, startup sensibilities",
    "avoid": ["traditional finance", "deep B2B healthcare", "SaaS healthcare", "energy", "industrials", "bureaucratic orgs"]
}

def get_db_connection():
    """Get database connection"""
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    return None

def create_job_hash(job):
    """Create unique hash for job to prevent duplicates"""
    key_data = f"{job.get('company_name', '')}-{job.get('title', '')}-{job.get('location', '')}"
    return hashlib.md5(key_data.encode()).hexdigest()

def job_exists(job_hash):
    """Check if job already exists in database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM jobs WHERE job_hash = %s", (job_hash,))
            return cur.fetchone() is not None
    except:
        return False
    finally:
        conn.close()

def save_job_to_db(job_data):
    """Save job to database"""
    conn = get_db_connection()
    if not conn:
        print("No database connection - saving to local JSON")
        save_to_json(job_data)
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jobs (
                    job_hash, title, company_name, location, description,
                    job_url, match_score, ai_analysis, contacts, 
                    created_at, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                job_data['job_hash'],
                job_data['title'],
                job_data['company_name'], 
                job_data['location'],
                job_data['description'],
                job_data['job_url'],
                job_data['match_score'],
                job_data['ai_analysis'],
                json.dumps(job_data['contacts']),
                datetime.now(),
                'new'
            ))
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        save_to_json(job_data)
    finally:
        conn.close()

def save_to_json(job_data):
    """Fallback: save to JSON file"""
    filename = 'jobs_backup.json'
    try:
        with open(filename, 'r') as f:
            jobs = json.load(f)
    except:
        jobs = []
    
    jobs.append(job_data)
    
    with open(filename, 'w') as f:
        json.dump(jobs, f, indent=2, default=str)


def search_jobs_serpapi(query: str, location: str = "Remote"):
    params = {
        "engine": "google_jobs",
        "q": f"{query} {location}",
        "hl": "en",
        "api_key": SERPAPI_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    return results.get("jobs_results", [])


def match_job_to_user(job, user_profile):
    prompt = f"""
    You are evaluating job fit for a senior product leader with this profile:
    - Background: MBA from Tuck/Dartmouth, 8+ years experience including Amazon, healthcare data company (Datavant), and Expert Network
    - Seeking: {user_profile['title_keywords']} 
    - Industries: {user_profile['industries']}
    - Locations: {user_profile['locations']}
    - Preferences: High-agency, startup sensibilities, thrives in ambiguity, enjoys building from ground up
    - Avoids: {user_profile['avoid']}

    Job posting:
    Title: {job.get('title')}
    Company: {job.get('company_name')}
    Location: {job.get('location', 'Not specified')}
    Description: {job.get('description', '')}

    Score this job 0-100 considering:
    1. Seniority level match (needs senior/principal/founding roles)
    2. Industry alignment with preferences
    3. Company stage/culture fit (prefers growth-stage, not bureaucratic)
    4. Role complexity and strategic impact potential

    Provide score and 2-3 sentence explanation focusing on fit factors.
    """

    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()


def find_team_members(company, role_keywords=["product manager", "chief of staff"]):
    people = []
    for keyword in role_keywords:
        params = {
            "engine": "google",
            "q": f"site:linkedin.com/in/ {keyword} {company}",
            "api_key": SERPAPI_KEY
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        if "organic_results" in results:
            for res in results["organic_results"][:3]:
                people.append({
                    "name": res.get("title"),
                    "linkedin": res.get("link"),
                    "snippet": res.get("snippet")
                })
    return people


def main():
    print("🔎 Searching for senior product leadership roles...")
    
    # Search for multiple role types
    search_queries = [
        "senior product manager remote",
        "principal product manager remote", 
        "founding product manager remote",
        "chief of staff remote",
        "head of operations remote"
    ]
    
    all_jobs = []
    for query in search_queries:
        jobs = search_jobs_serpapi(query)
        all_jobs.extend(jobs)
    
    # Remove duplicates based on company + title
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job.get('company_name', ''), job.get('title', ''))
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    print(f"Found {len(unique_jobs)} unique opportunities")

    final_results = []

    new_jobs_count = 0
    
    # Process jobs and save new ones to database
    for job in unique_jobs[:15]:  # analyze top 15 opportunities
        job_hash = create_job_hash(job)
        
        # Skip if we've already processed this job
        if job_exists(job_hash):
            continue
            
        new_jobs_count += 1
        print(f"\n🆕 NEW JOB: {job['title']} at {job['company_name']}")
        
        score_output = match_job_to_user(job, user_profile)
        print(f"🧠 Match Score: {score_output}")

        contacts = find_team_members(job['company_name'], ["senior product manager", "principal product manager", "chief of staff", "head of product"])

        # Extract numeric score for sorting
        import re
        score_numbers = re.findall(r'\b(\d+)\b', score_output)
        numeric_score = int(score_numbers[0]) if score_numbers else 0
        
        # Prepare job data for database
        job_data = {
            'job_hash': job_hash,
            'title': job.get('title', ''),
            'company_name': job.get('company_name', ''),
            'location': job.get('location', 'Remote'),
            'description': job.get('description', ''),
            'job_url': job.get('link', ''),  # SerpAPI provides 'link' field
            'match_score': numeric_score,
            'ai_analysis': score_output,
            'contacts': contacts
        }
        
        # Save to database
        save_job_to_db(job_data)

        final_results.append({
            "job": job,
            "score": score_output,
            "contacts": contacts,
            "job_url": job.get('link', ''),
            "numeric_score": numeric_score
        })
    
    print(f"\n📊 Found {new_jobs_count} new jobs out of {len(unique_jobs)} total opportunities")
    
    # Sort results by numeric score
    final_results.sort(key=lambda x: x['numeric_score'], reverse=True)

    print("\n\n📝 Final Report:")
    for result in final_results:
        print(f"\n🔹 {result['job']['title']} at {result['job']['company_name']}")
        print(f"🔗 Job URL: {result['job_url']}")
        print(f"🧠 Match: {result['score']}")
        print("👥 Potential Contacts:")
        for person in result['contacts']:
            print(f"  - {person['name']} | {person['linkedin']}")
            print(f"    ↳ {person['snippet']}")
            
    if new_jobs_count == 0:
        print("\n✨ No new jobs found - all current opportunities already in database!")


if __name__ == "__main__":
    main()