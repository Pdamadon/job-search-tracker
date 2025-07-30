# Job Search Tracker Frontend

React frontend for the AI-powered job search tracker.

## Features

- 🎯 Personalized job matching with AI analysis
- 📊 Interactive dashboard with application pipeline
- 👥 LinkedIn contact discovery with message templates
- 🔗 Direct job posting links
- 📱 Responsive design with Tailwind CSS

## Environment Variables

- `REACT_APP_API_URL` - Backend API URL (automatically configured for Vercel)

## Deployment

This frontend is deployed to Vercel and connects to the Railway backend API.

- **Production**: Auto-deployed from main branch
- **Backend API**: Railway-hosted FastAPI server
- **Database**: Railway PostgreSQL

## Local Development

```bash
cd frontend
npm install
npm start
```

## Technologies

- React 18
- Tailwind CSS
- Axios for API calls
- Responsive design