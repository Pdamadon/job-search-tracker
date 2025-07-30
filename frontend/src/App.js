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
    // Debug environment variables on load
    console.log('🔧 App initialized with:');
    console.log('📡 REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
    console.log('🔗 API_BASE:', API_BASE);
    console.log('🌍 NODE_ENV:', process.env.NODE_ENV);
    
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
      
      const url = `${API_BASE}/api/jobs?${params}`;
      console.log('📥 Fetching jobs from:', url);
      console.log('🔍 Current filters:', filters);
      console.log('📡 Making request with axios config:', {
        url,
        method: 'GET',
        timeout: 30000
      });
      
      const response = await axios.get(url, { timeout: 30000 });
      
      console.log('✅ Response received!');
      console.log('📊 Full response object:', response);
      console.log('📋 Response status:', response.status);
      console.log('📄 Response headers:', response.headers);
      console.log('📊 Jobs response data:', response.data);
      console.log('📈 Number of jobs received:', response.data?.length || 'undefined');
      console.log('📝 Type of response.data:', typeof response.data);
      console.log('🔍 Is response.data an array?', Array.isArray(response.data));
      
      if (response.data && Array.isArray(response.data)) {
        console.log('✅ Valid jobs array received, setting state...');
        if (response.data.length > 0) {
          console.log('📋 First job sample:', response.data[0]);
        }
        setJobs(response.data);
      } else {
        console.warn('⚠️ Invalid response format - expected array, got:', typeof response.data);
        setJobs([]);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('❌ Error fetching jobs:', error);
      console.error('📄 Error response:', error.response?.data);
      console.error('🔢 Error status:', error.response?.status);
      console.error('📋 Error config:', error.config);
      setJobs([]);
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
    console.log('🚀 Button clicked! Starting job search...');
    console.log('🔗 API_BASE:', API_BASE);
    console.log('🌍 Environment:', process.env.NODE_ENV);
    console.log('📡 REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
    
    setSearchRunning(true);
    
    try {
      console.log('📤 Making API request to:', `${API_BASE}/api/run-search`);
      
      const response = await axios.post(`${API_BASE}/api/run-search`, {}, {
        timeout: 120000, // 2 minute timeout
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('✅ Search completed successfully:', response.data);
      
      // Show success message
      alert('🎉 Job search completed! Found new opportunities. Refreshing results...');
      
      // Refresh jobs after search
      await fetchJobs();
      await fetchStats();
      
    } catch (error) {
      console.error('❌ Error running search:', error);
      
      // Detailed error logging
      if (error.response) {
        console.error('📄 Error response:', error.response.data);
        console.error('🔢 Status code:', error.response.status);
        alert(`❌ Search failed: ${error.response.data?.detail || error.response.statusText}`);
      } else if (error.request) {
        console.error('📡 No response received:', error.request);
        alert('❌ No response from server. Check your internet connection.');
      } else {
        console.error('⚙️ Request setup error:', error.message);
        alert(`❌ Request error: ${error.message}`);
      }
    } finally {
      console.log('🏁 Search process finished, updating UI...');
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
          {/* Debug Info */}
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
            <div className="text-sm text-yellow-700">
              <strong>🔍 Debug Info:</strong><br/>
              Jobs array length: {jobs.length}<br/>
              Jobs array type: {typeof jobs}<br/>
              Is jobs an array: {Array.isArray(jobs) ? 'Yes' : 'No'}<br/>
              {jobs.length > 0 && `First job ID: ${jobs[0]?.id || 'undefined'}`}
            </div>
          </div>
          
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
            <div className="space-y-4">
              <button
                onClick={runJobSearch}
                disabled={searchRunning}
                className={`${
                  searchRunning 
                    ? 'bg-blue-300 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700'
                } text-white font-bold py-3 px-8 rounded-lg text-lg transition-colors`}
              >
                {searchRunning ? (
                  <>
                    <span className="animate-spin inline-block mr-2">⏳</span>
                    Searching... This may take 60+ seconds
                  </>
                ) : (
                  '🚀 Start Job Search'
                )}
              </button>
              
              {/* Debug test button */}
              <button
                onClick={() => {
                  console.log('🧪 Test button clicked!');
                  alert('Button click works! API_BASE: ' + API_BASE);
                }}
                className="bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded text-sm"
              >
                🧪 Test Button Click
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;