import React, { useState, useEffect } from 'react';
import axios from 'axios';
import JobCard from './components/JobCard';
import SearchControls from './components/SearchControls';
import Dashboard from './components/Dashboard';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: '',
    minScore: '',
    sortBy: 'match_score'
  });
  const [searchRunning, setSearchRunning] = useState(false);
  const [initializingDb, setInitializingDb] = useState(false);

  useEffect(() => {
    initializeApp();
  }, []);

  useEffect(() => {
    if (!loading) {
      fetchJobs();
    }
  }, [filters, loading]);

  const initializeApp = async () => {
    try {
      // First try to fetch jobs to see if DB exists
      await fetchJobs();
      await fetchStats();
    } catch (error) {
      console.log('Database might need initialization...');
      // Try to initialize database if jobs fetch fails
      await initializeDatabase();
    }
  };

  const initializeDatabase = async () => {
    setInitializingDb(true);
    try {
      const response = await axios.post(`${API_BASE}/api/init-database`);
      console.log('Database initialized:', response.data);
      // Now fetch jobs and stats
      await fetchJobs();
      await fetchStats();
    } catch (error) {
      console.error('Error initializing database:', error);
    } finally {
      setInitializingDb(false);
    }
  };

  const fetchJobs = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.minScore) params.append('min_score', filters.minScore);
      
      const response = await axios.get(`${API_BASE}/api/jobs?${params}`);
      setJobs(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const updateJobStatus = async (jobId, status, notes = '') => {
    try {
      await axios.put(`${API_BASE}/api/jobs/${jobId}/status`, {
        action_type: status,
        notes: notes
      });
      fetchJobs(); // Refresh the list
      fetchStats(); // Refresh stats
    } catch (error) {
      console.error('Error updating job status:', error);
    }
  };

  const runJobSearch = async () => {
    setSearchRunning(true);
    try {
      const response = await axios.post(`${API_BASE}/api/run-search`);
      console.log('Search result:', response.data);
      // Refresh jobs after search
      setTimeout(() => {
        fetchJobs();
        fetchStats();
        setSearchRunning(false);
      }, 3000);
    } catch (error) {
      console.error('Error running search:', error);
      setSearchRunning(false);
    }
  };

  if (loading || initializingDb) {
    return (
      <div className="flex flex-col justify-center items-center h-screen bg-gray-50">
        <div className="text-center">
          <svg className="animate-spin -ml-1 mr-3 h-12 w-12 text-blue-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <h2 className="mt-4 text-xl font-semibold text-gray-900">
            {initializingDb ? 'Setting up your job tracker...' : 'Loading...'}
          </h2>
          <p className="mt-2 text-gray-600">
            {initializingDb ? 'Creating database tables and preparing your personalized job search.' : 'Getting your jobs ready.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">AI Job Search Tracker</h1>
              <p className="text-sm text-gray-600 mt-1">Personalized for MBA Product Leaders</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">Powered by OpenAI + SerpAPI</div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard */}
        <Dashboard stats={stats} />

        {/* Search Controls */}
        <SearchControls
          onRunSearch={runJobSearch}
          onFilterChange={handleFilterChange}
          searchRunning={searchRunning}
          stats={stats}
        />

        {/* Jobs List */}
        <div className="space-y-6">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onStatusUpdate={updateJobStatus}
            />
          ))}
        </div>

        {/* Empty State */}
        {jobs.length === 0 && !searchRunning && (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-2xl font-semibold text-gray-900 mb-2">Ready to Find Your Next Role?</h3>
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              Run your first AI-powered search to discover senior product management opportunities 
              tailored specifically to your MBA background and startup experience.
            </p>
            <button
              onClick={runJobSearch}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg text-lg transition-colors"
            >
              🚀 Start Job Search
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;