# Job Search Tracker

AI-powered job search and tracking application with PostgreSQL database and React frontend.

## Features

- 🔍 **AI-Powered Job Matching**: Uses OpenAI to score job fit based on your profile
- 🚀 **Duplicate Prevention**: Never see the same job twice
- 📊 **Progress Tracking**: Track application status, interviews, offers
- 🔗 **Direct Job Links**: Click through to original job postings
- 👥 **LinkedIn Contact Discovery**: Find key contacts at each company
- 📈 **Analytics Dashboard**: View stats and trends
- ⚡ **Daily Automation**: Runs searches automatically
- 🌐 **Web Interface**: Clean, responsive UI for job management

## Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Add your API keys to .env:
# - OpenAI API key
# - SerpAPI key
# - PostgreSQL database URL (Railway or local)
```

### 2. Database Setup
```bash
# If using Railway:
# 1. Create new Railway project
# 2. Add PostgreSQL service
# 3. Copy DATABASE_URL to .env
# 4. Run schema:
psql $DATABASE_URL < schema.sql

# For local PostgreSQL:
createdb job_tracker
psql job_tracker < schema.sql
```

### 3. Backend Setup
```bash
# Install dependencies
pip install -r requirements-backend.txt

# Run backend server
uvicorn backend.app:app --reload --port 8000
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm start
```

Visit http://localhost:3000 to see the app!

## Deployment to Railway

### 1. Backend Deployment
```bash
# Connect to Railway
railway login
railway link

# Add environment variables in Railway dashboard:
# - OPENAI_API_KEY
# - SERPAPI_KEY
# - DATABASE_URL (auto-added by PostgreSQL service)

# Deploy
railway up
```

### 2. Frontend Deployment
```bash
cd frontend
# Build for production
npm run build

# Deploy to Railway or Vercel/Netlify
```

## Daily Automation

### Option 1: Railway Cron (Recommended)
```bash
# Add cron service in Railway dashboard
# Command: python daily_job_search.py
# Schedule: 0 9 * * * (9 AM daily)
```

### Option 2: Local Cron
```bash
# Add to crontab
crontab -e

# Add line (runs at 9 AM daily):
0 9 * * * cd /path/to/job_tracker && python daily_job_search.py
```

## API Endpoints

- `GET /api/jobs` - List all jobs with filtering
- `GET /api/jobs/{id}` - Get single job details
- `PUT /api/jobs/{id}/status` - Update job status
- `GET /api/stats` - Dashboard statistics
- `POST /api/run-search` - Trigger manual search

## Job Status Workflow

1. **New** - Just discovered by search
2. **Applied** - You've submitted application
3. **Interviewing** - In interview process
4. **Offer** - Received job offer
5. **Rejected** - Not moving forward

## Customization

### Profile Configuration
Edit `user_profile` in `job_search_agent.py`:
```python
user_profile = {
    "title_keywords": ["senior product manager", "principal PM"],
    "locations": ["remote", "seattle", "san francisco"],
    "industries": ["AI", "consumer tech", "fintech"],
    "avoid": ["traditional finance", "healthcare"]
}
```

### Search Queries
Modify `search_queries` in `main()` function to target different roles.

### AI Scoring
Update the prompt in `match_job_to_user()` to change how jobs are evaluated.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│────│  FastAPI Backend│────│   PostgreSQL    │
│                 │    │                 │    │                 │
│ • Job browsing  │    │ • REST API      │    │ • Job storage   │
│ • Status updates│    │ • Job search    │    │ • Deduplication │
│ • Dashboard     │    │ • AI scoring    │    │ • Analytics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │              ┌─────────────────┐
         │              │  Daily Cron Job │
         │              │                 │
         └──────────────│ • Automated     │
                        │   search runs   │
                        │ • New job alerts│
                        └─────────────────┘
```

## Tech Stack

- **Backend**: FastAPI, PostgreSQL, OpenAI API, SerpAPI
- **Frontend**: React, Tailwind CSS, Axios
- **Deployment**: Railway (PostgreSQL + backend), Vercel/Netlify (frontend)
- **Automation**: Railway Cron or system crontab

## Troubleshooting

### Database Connection Issues
```bash
# Test connection
python -c "import psycopg2; print('DB OK')"

# Check Railway logs
railway logs
```

### API Key Issues
```bash
# Test OpenAI
python -c "from openai import OpenAI; print('OpenAI OK')"

# Test SerpAPI
python -c "from serpapi import GoogleSearch; print('SerpAPI OK')"
```

### No New Jobs Found
- Check if search queries match current job market
- Verify SerpAPI quota hasn't been exceeded
- Review job matching criteria (may be too restrictive)

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details.