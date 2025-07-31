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
    "title_keywords": ["senior product manager", "principal product manager", "founding product manager", "director of product", "vp product", "head of product", "chief of staff", "head of operations", "general manager", "co-founder", "head of growth", "head of strategy"],
    "locations": {
        "preferred": ["remote", "seattle", "bellevue", "kirkland", "redmond", "eastside"],  # +15 bonus points
        "acceptable": ["austin", "denver", "boston", "los angeles", "portland", "vancouver"],  # neutral
        "avoid": ["san francisco", "new york", "nyc", "sf", "manhattan", "palo alto"]  # -10 penalty points
    },
    "location_priority_weights": {
        "remote": 15,
        "seattle": 15, 
        "bellevue": 15,
        "kirkland": 15,
        "redmond": 15,
        "eastside": 15,
        "austin": 0,
        "denver": 0,
        "boston": 0,
        "los angeles": 0,
        "portland": 5,
        "vancouver": 5,
        "san francisco": -10,
        "sf": -10,
        "new york": -10,
        "nyc": -10,
        "manhattan": -10,
        "palo alto": -10
    },
    "industries": ["AI/ML", "generative AI", "productivity tools", "developer tools", "consumer tech", "fintech", "healthtech", "edtech", "marketplaces", "e-commerce", "creator economy", "climate tech", "web3", "cybersecurity", "data/analytics", "SaaS B2B", "mobile apps", "social platforms"],
    "experience_level": "senior",
    "background": "MBA, 8+ years experience, healthcare data, Amazon, Expert Network, startup sensibilities",
    "avoid": ["traditional finance", "consulting", "big pharma", "energy", "industrials", "government", "non-profit"],
    "company_stages": ["seed", "series A", "series B", "series C", "growth stage", "pre-IPO"],
    "company_sizes": ["10-50", "50-200", "200-1000", "startup", "scale-up"],
    "startup_focused": True,
    "target_companies": {
        # Health & Wellness
        "health_wellness": ["Calm", "Headspace", "BetterHelp", "Grow Therapy", "Ro", "Zocdoc", "Oura", "Levels", "Accolade", "Superpower", "Visible Health", "Equip", "Brightside", "Turquoise Health", "Xealth"],
        
        # Fintech & Finance  
        "fintech": ["Remitly", "Betterment", "Stripe", "Monarch Money", "Farther", "Possible Finance"],
        
        # Travel & Lifestyle
        "travel_lifestyle": ["Navan", "TripActions", "Going", "Scott's Cheap Flights", "Hopper", "The Dyrt", "Outdoorsy", "Fora", "Airbnb", "Expedia"],
        
        # Consumer & E-commerce
        "consumer_ecommerce": ["Strava", "VSCO", "Cuyana", "Italic", "Preply", "Duolingo", "Cambly", "REI"],
        
        # Productivity & Design
        "productivity_design": ["Descript", "Canva", "Figma", "Notion", "Bending Spoons", "Evernote", "Aha!", "Scribe", "LinkedIn"],
        
        # Real Estate & Housing
        "real_estate": ["Zillow", "Knock", "Pacaso"],
        
        # Climate & Sustainability  
        "climate": ["Nori", "Future"],
        
        # Enterprise & B2B
        "enterprise": ["Amazon", "Microsoft", "Google", "Katalyst", "Symbl.ai", "Center"],
        
        # Other Consumer Tech
        "other_consumer": ["Otto", "Tolan", "Portola", "Sketchy", "Ravenna", "Jargon"]
    }
}

def get_db_connection():
    """Get database connection"""
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    return None

def calculate_location_priority_score(job_location, user_profile):
    """Calculate location priority score based on job location"""
    if not job_location:
        return 0
    
    location_lower = job_location.lower().strip()
    location_weights = user_profile.get('location_priority_weights', {})
    
    # Check for exact matches first
    for location_key, weight in location_weights.items():
        if location_key.lower() in location_lower:
            return weight
    
    # Check for common variations and keywords
    location_keywords = {
        'remote': ['remote', 'work from home', 'anywhere', 'distributed'],
        'seattle': ['seattle', 'wa', 'washington'],
        'bellevue': ['bellevue'],
        'kirkland': ['kirkland'],
        'redmond': ['redmond'],
        'eastside': ['eastside', 'east side'],
        'san francisco': ['san francisco', 'sf', 'bay area', 'silicon valley'],
        'new york': ['new york', 'nyc', 'brooklyn', 'queens', 'bronx'],
        'austin': ['austin', 'tx', 'texas'],
        'denver': ['denver', 'co', 'colorado'],
        'boston': ['boston', 'ma', 'massachusetts', 'cambridge'],
        'los angeles': ['los angeles', 'la', 'california', 'ca'],
        'portland': ['portland', 'or', 'oregon'],
        'vancouver': ['vancouver', 'bc', 'british columbia']
    }
    
    for base_location, keywords in location_keywords.items():
        if any(keyword in location_lower for keyword in keywords):
            return location_weights.get(base_location, 0)
    
    return 0  # No location bonus/penalty

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
    """Search jobs using SerpAPI - Google Jobs"""
    params = {
        "engine": "google_jobs",
        "q": f"{query} {location}",
        "hl": "en",
        "api_key": SERPAPI_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    jobs = results.get("jobs_results", [])
    
    # Add source metadata
    for job in jobs:
        job['source'] = 'google_jobs'
        job['source_url'] = job.get('apply_options', [{}])[0].get('link', job.get('share_link', ''))
    
    return jobs

def search_jobs_ycombinator():
    """Search Y Combinator jobs using SerpAPI - QUICK VERSION"""
    if not SERPAPI_KEY:
        return []
    
    params = {
        "engine": "google",
        "q": "site:ycombinator.com/jobs product manager",
        "api_key": SERPAPI_KEY,
        "num": 10  # Reduced from 20
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])
        
        jobs = []
        for result in organic_results[:5]:  # Only check first 5
            if '/jobs/' in result.get('link', ''):
                jobs.append({
                    'title': result.get('title', ''),
                    'company_name': 'YC Company',
                    'location': 'Various',
                    'description': result.get('snippet', ''),
                    'job_url': result.get('link', ''),
                    'source': 'ycombinator',
                    'source_url': result.get('link', '')
                })
        
        return jobs  # Return all found (max 5)
    except Exception as e:
        print(f"Error searching YC jobs: {e}")
        return []

def search_jobs_angellist():
    """Search AngelList jobs using SerpAPI - QUICK VERSION"""
    if not SERPAPI_KEY:
        return []
    
    # Single optimized query instead of 3
    query = "site:wellfound.com OR site:angel.co product manager startup"
    
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": 8  # Reduced from 15
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])
        
        jobs = []
        for result in organic_results[:6]:  # Only check first 6
            if any(keyword in result.get('link', '') for keyword in ['/jobs/', '/job/']):
                title = result.get('title', '')
                company_name = 'Startup'
                if ' at ' in title:
                    parts = title.split(' at ')
                    if len(parts) > 1:
                        company_name = parts[1].split(' - ')[0].strip()
                
                jobs.append({
                    'title': title.split(' at ')[0] if ' at ' in title else title,
                    'company_name': company_name,
                    'location': 'Remote/Various',
                    'description': result.get('snippet', ''),
                    'job_url': result.get('link', ''),
                    'source': 'angellist',
                    'source_url': result.get('link', '')
                })
        
        return jobs  # Return all found (max 6)
    except Exception as e:
        print(f"Error searching AngelList: {e}")
        return []

def search_jobs_builtin():
    """Search Built In jobs using SerpAPI"""
    if not SERPAPI_KEY:
        return []
    
    locations = ["sf", "nyc", "austin", "seattle", "boston"]
    all_jobs = []
    
    for location in locations:
        params = {
            "engine": "google",
            "q": f"site:builtin.com/{location} (senior OR principal OR head) product manager",
            "api_key": SERPAPI_KEY,
            "num": 10
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            organic_results = results.get("organic_results", [])
            
            for result in organic_results:
                if '/jobs/' in result.get('link', ''):
                    all_jobs.append({
                        'title': result.get('title', ''),
                        'company_name': 'Tech Company',
                        'location': location.upper(),
                        'description': result.get('snippet', ''),
                        'job_url': result.get('link', ''),
                        'source': 'builtin',
                        'source_url': result.get('link', '')
                    })
        except Exception as e:
            print(f"Error searching Built In jobs for {location}: {e}")
            continue
    
    return all_jobs[:10]  # Limit to 10 results

def search_startup_jobs_general():
    """Search for startup jobs using general startup-focused queries"""
    if not SERPAPI_KEY:
        return []
    
    startup_queries = [
        "\"senior product manager\" startup \"series A\" OR \"series B\" OR \"seed funded\"",
        "\"head of product\" \"early stage\" startup remote",
        "\"founding product manager\" \"well funded\" startup",
        "\"director of product\" fintech OR healthtech OR \"climate tech\" startup"
    ]
    
    all_jobs = []
    
    for query in startup_queries:
        params = {
            "engine": "google_jobs",
            "q": query,
            "api_key": SERPAPI_KEY
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            jobs = results.get("jobs_results", [])
            
            for job in jobs:
                job['source'] = 'startup_focused'
                job['source_url'] = job.get('apply_options', [{}])[0].get('link', job.get('share_link', ''))
            
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"Error searching startup jobs with query '{query}': {e}")
            continue
    
    return all_jobs[:20]  # Limit to 20 results

def search_target_companies():
    """Search for jobs at specific target companies - OPTIMIZED"""
    if not SERPAPI_KEY:
        return []
    
    all_jobs = []
    
    # FOCUS ON TOP-TIER COMPANIES ONLY (much faster)
    priority_companies = [
        "Stripe", "Figma", "Notion", "Canva", "Strava", 
        "Calm", "Headspace", "Oura", "Remitly", "Betterment",
        "Airbnb", "Amazon", "Microsoft"  # 13 companies max
    ]
    
    # Single broad query per company (instead of multiple role queries)
    for company in priority_companies:
        try:
            query = f'"product manager" OR "head of product" OR "chief of staff" site:{company.lower()}.com'
            
            params = {
                "engine": "google",
                "q": query,
                "api_key": SERPAPI_KEY,
                "num": 3  # Reduced from 5
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            organic_results = results.get("organic_results", [])
            
            for result in organic_results:
                link = result.get('link', '')
                if any(keyword in link.lower() for keyword in ['job', 'career', 'hiring']):
                    all_jobs.append({
                        'title': result.get('title', ''),
                        'company_name': company,
                        'location': 'See Company Site',
                        'description': result.get('snippet', ''),
                        'job_url': link,
                        'source': 'target_company_direct',
                        'source_url': link
                    })
                    break  # Only take first relevant result per company
        
        except Exception as e:
            print(f"Error searching {company}: {e}")
            continue
    
    return all_jobs[:10]  # Further limit results

def search_company_careers_general():
    """Search for jobs using general company + role queries - OPTIMIZED"""
    if not SERPAPI_KEY:
        return []
    
    all_jobs = []
    
    # STREAMLINED: Just 2 high-impact queries
    targeted_queries = [
        '"senior product manager" OR "principal product manager" (Stripe OR Figma OR Notion OR Calm OR Strava OR Airbnb)',
        '"head of product" OR "director product" (Amazon OR Microsoft OR Remitly OR Betterment OR Canva OR Oura)'
    ]
    
    for query in targeted_queries:
        try:
            params = {
                "engine": "google_jobs", 
                "q": query,
                "api_key": SERPAPI_KEY
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            jobs = results.get("jobs_results", [])
            
            for job in jobs:
                job['source'] = 'target_company_jobs'
                job['source_url'] = job.get('apply_options', [{}])[0].get('link', job.get('share_link', ''))
            
            all_jobs.extend(jobs[:10])  # Limit to 10 per query
            
        except Exception as e:
            print(f"Error searching: {e}")
            continue
    
    return all_jobs[:15]  # Total limit of 15

def search_all_sources():
    """Search jobs from all available sources - OPTIMIZED VERSION"""
    print("🔎 Searching for senior product leadership roles...")
    
    all_jobs = []
    sources_searched = []
    
    # STREAMLINED: Fewer, more targeted queries
    core_queries = [
        "senior product manager remote OR seattle OR bellevue",
        "principal product manager startup OR \"series A\" OR fintech OR healthtech", 
        "head of product \"early stage\" OR \"growth stage\" remote",
        "founding product manager OR director product startup"
    ]
    
    # PRIMARY SEARCH: Focus on high-value sources only
    print("🎯 Phase 1: Core job board search...")
    for query in core_queries:
        try:
            jobs = search_jobs_serpapi(query, "")  # No location filter, it's in the query
            all_jobs.extend(jobs)
            print(f"  ✓ Found {len(jobs)} jobs: {query[:50]}...")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    sources_searched.append(f"Google Jobs optimized ({len(all_jobs)} jobs)")
    
    # TARGET COMPANIES: Only high-priority ones
    print("🏢 Phase 2: Target company search...")
    try:
        company_jobs = search_company_careers_general()  # This is more efficient
        all_jobs.extend(company_jobs)
        sources_searched.append(f"Target companies ({len(company_jobs)} jobs)")
        print(f"  ✓ Found {len(company_jobs)} jobs from target companies")
    except Exception as e:
        print(f"  ❌ Target company search error: {e}")
    
    # STARTUP SOURCES: Quick sampling only
    print("🚀 Phase 3: Startup platforms...")
    
    # Y Combinator - quick search
    try:
        yc_jobs = search_jobs_ycombinator()
        if yc_jobs:
            all_jobs.extend(yc_jobs[:5])  # Limit to top 5
            sources_searched.append(f"Y Combinator ({len(yc_jobs[:5])} jobs)")
            print(f"  ✓ Found {len(yc_jobs[:5])} YC jobs")
    except Exception as e:
        print(f"  ❌ YC search error: {e}")
    
    # AngelList - quick search
    try:
        angel_jobs = search_jobs_angellist()
        if angel_jobs:
            all_jobs.extend(angel_jobs[:8])  # Limit to top 8
            sources_searched.append(f"AngelList ({len(angel_jobs[:8])} jobs)")
            print(f"  ✓ Found {len(angel_jobs[:8])} AngelList jobs")
    except Exception as e:
        print(f"  ❌ AngelList search error: {e}")
    
    print(f"\n📊 SEARCH COMPLETE")
    print(f"📈 Sources: {', '.join(sources_searched)}")
    print(f"🎯 Total opportunities found: {len(all_jobs)}")
    
    return all_jobs


def match_job_to_user(job, user_profile):
    # Calculate location priority score
    location_bonus = calculate_location_priority_score(job.get('location', ''), user_profile)
    
    # Calculate target company bonus
    target_company_bonus = 0
    company_name = job.get('company_name', '').lower()
    target_companies = user_profile.get('target_companies', {})
    
    # Check if this is one of our target companies
    for category, companies in target_companies.items():
        for target_company in companies:
            if target_company.lower() in company_name or company_name in target_company.lower():
                target_company_bonus = 10  # +10 points for target companies
                break
    
    total_bonus = location_bonus + target_company_bonus
    
    prompt = f"""
    You are evaluating job fit for a senior product leader with this startup-focused profile:
    
    CANDIDATE PROFILE:
    - Background: MBA from Tuck/Dartmouth, 8+ years experience at Amazon, healthcare data company (Datavant), and Expert Network
    - Target Roles: {', '.join(user_profile['title_keywords'][:8])}  # Limit for brevity
    - Preferred Industries: {', '.join(user_profile['industries'][:10])}
    - LOCATION PREFERENCES:
      * HIGHLY PREFERRED (+15 pts): Remote, Seattle, Bellevue, Kirkland, Redmond, Eastside
      * ACCEPTABLE (neutral): Austin, Denver, Boston, LA, Portland, Vancouver  
      * AVOID (-10 pts): San Francisco, NYC, Manhattan, Palo Alto
    - TARGET COMPANIES (+10 pts): Stripe, Figma, Notion, Calm, Strava, Headspace, Oura, Remitly, Betterment, Canva, Duolingo, Airbnb, Amazon, Microsoft, Google, and ~40 other consumer/fintech/healthtech companies
    - Company Stages: {', '.join(user_profile['company_stages'])}
    - Personality: High-agency, startup sensibilities, thrives in ambiguity, enjoys building from ground up, proven at scale
    - Avoids: {', '.join(user_profile['avoid'])}

    JOB DETAILS:
    Title: {job.get('title', 'N/A')}
    Company: {job.get('company_name', 'N/A')} [Target Company Bonus: {target_company_bonus:+d}]
    Location: {job.get('location', 'Not specified')} [Location Priority Score: {location_bonus:+d}]
    Source: {job.get('source', 'unknown')}
    Description: {job.get('description', 'No description available')[:500]}...

    SCORING CRITERIA (Base 0-100):
    1. Seniority Match (25 points): Senior/Principal/Head/Director level roles preferred
    2. Industry Fit (25 points): Strong preference for AI/ML, fintech, healthtech, productivity tools, consumer tech
    3. Company Stage (25 points): Startup/scale-up preferred (seed to Series C), avoid large corporations
    4. Role Impact (25 points): Strategic role with product ownership, not execution-only

    BONUS FACTORS:
    - Target company fit: Already calculated as {target_company_bonus:+d} points
    - Location fit: Already calculated as {location_bonus:+d} points
    - Remote work option: +10 points
    - Startup/venture-backed company: +10 points
    - "Founding" or "0-to-1" opportunity: +10 points
    - AI/ML/data focus: +10 points
    - Consumer or B2B SaaS: +5 points

    IMPORTANT: Factor the total bonus/penalty of {total_bonus:+d} points ({location_bonus:+d} location + {target_company_bonus:+d} company) heavily into your scoring.

    Provide: SCORE (0-100) and 2-3 sentences explaining the match rationale, highlighting company fit, location preference, role seniority, industry alignment, and any concerns.
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3  # Lower temperature for more consistent scoring
        )
        ai_response = completion.choices[0].message.content.strip()
        
        # Apply location bonus to the final score
        import re
        score_match = re.search(r'score:?\s*(\d+)', ai_response.lower())
        if score_match:
            base_score = int(score_match.group(1))
            adjusted_score = max(0, min(100, base_score + total_bonus))  # Clamp between 0-100
            
            # Update the response with the adjusted score
            ai_response = re.sub(r'score:?\s*\d+', f'Score: {adjusted_score}', ai_response, flags=re.IGNORECASE)
            if target_company_bonus > 0:
                ai_response += f" [Base: {base_score}, Location: {location_bonus:+d}, Company: {target_company_bonus:+d}]"
            else:
                ai_response += f" [Base: {base_score}, Location: {location_bonus:+d}]"
        
        return ai_response
    except Exception as e:
        print(f"Error getting AI match score: {e}")
        return f"Score: 70 - Unable to analyze job details due to API error. Bonuses: Location {location_bonus:+d}, Company {target_company_bonus:+d}"


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
    # Use the comprehensive search function
    all_jobs = search_all_sources()
    
    # Remove duplicates based on company + title + location
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        # Create a more robust key for deduplication
        title = job.get('title', '').lower().strip()
        company = job.get('company_name', '').lower().strip()
        location = job.get('location', '').lower().strip()
        
        key = f"{company}|{title}|{location}"
        if key not in seen and title and company:  # Only include jobs with title and company
            seen.add(key)
            unique_jobs.append(job)
    
    print(f"\n🔍 Deduplication complete: {len(unique_jobs)} unique opportunities")

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
        
        # Get job URL from various possible fields
        job_url = (job.get('job_url') or 
                  job.get('link') or 
                  job.get('source_url') or 
                  job.get('apply_options', [{}])[0].get('link', '') if job.get('apply_options') else '')
        
        # Prepare job data for database
        job_data = {
            'job_hash': job_hash,
            'title': job.get('title', ''),
            'company_name': job.get('company_name', ''),
            'location': job.get('location', 'Remote'),
            'description': job.get('description', ''),
            'job_url': job_url,
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
            "job_url": job_url,
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