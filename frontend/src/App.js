import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [minScore, setMinScore] = useState('');
  const [searchRunning, setSearchRunning] = useState(false);

  useEffect(() => {
    fetchJobs();
    fetchStats();
  }, [filterStatus, minScore]);

  const fetchJobs = async () => {
    try {
      const params = new URLSearchParams();
      if (filterStatus) params.append('status', filterStatus);
      if (minScore) params.append('min_score', minScore);
      
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
      }, 2000);
    } catch (error) {
      console.error('Error running search:', error);
      setSearchRunning(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'new': 'bg-blue-100 text-blue-800',
      'applied': 'bg-yellow-100 text-yellow-800',
      'interviewing': 'bg-green-100 text-green-800',
      'rejected': 'bg-red-100 text-red-800',
      'offer': 'bg-purple-100 text-purple-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600 font-bold';
    if (score >= 80) return 'text-blue-600 font-semibold';
    if (score >= 70) return 'text-yellow-600';
    return 'text-gray-600';
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">Job Search Tracker</h1>
            <button
              onClick={runJobSearch}
              disabled={searchRunning}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-bold py-2 px-4 rounded"
            >
              {searchRunning ? 'Running Search...' : 'Run New Search'}
            </button>
          </div>
        </div>
      </header>

      {/* Stats Dashboard */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="text-2xl font-bold text-blue-600">{stats.total_jobs || 0}</div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Jobs</dt>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="text-2xl font-bold text-green-600">
                    {Math.round(stats.avg_match_score || 0)}
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Avg Match Score</dt>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="text-2xl font-bold text-purple-600">
                    {stats.status_counts?.find(s => s.status === 'new')?.count || 0}
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">New Jobs</dt>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="text-2xl font-bold text-yellow-600">
                    {stats.status_counts?.find(s => s.status === 'applied')?.count || 0}
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Applied</dt>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="flex space-x-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Status Filter</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
              >
                <option value="">All Statuses</option>
                <option value="new">New</option>
                <option value="applied">Applied</option>
                <option value="interviewing">Interviewing</option>
                <option value="rejected">Rejected</option>
                <option value="offer">Offer</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Min Score</label>
              <input
                type="number"
                value={minScore}
                onChange={(e) => setMinScore(e.target.value)}
                placeholder="e.g. 80"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
              />
            </div>
          </div>
        </div>

        {/* Jobs List */}
        <div className="space-y-4">
          {jobs.map((job) => (
            <div key={job.id} className="bg-white shadow rounded-lg p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(job.status)}`}>
                      {job.status}
                    </span>
                    <span className={`text-sm ${getScoreColor(job.match_score)}`}>
                      Score: {job.match_score || 'N/A'}
                    </span>
                  </div>
                  <p className="text-gray-600 mt-1">{job.company_name} • {job.location}</p>
                  
                  {job.job_url && (
                    <a
                      href={job.job_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 text-sm mt-2 inline-block"
                    >
                      View Job Posting →
                    </a>
                  )}
                  
                  {job.ai_analysis && (
                    <div className="mt-3 text-sm text-gray-700 bg-gray-50 p-3 rounded">
                      <strong>AI Analysis:</strong> {job.ai_analysis.substring(0, 200)}...
                    </div>
                  )}
                </div>
                
                <div className="flex space-x-2 ml-4">
                  {job.status === 'new' && (
                    <button
                      onClick={() => updateJobStatus(job.id, 'applied')}
                      className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Mark Applied
                    </button>
                  )}
                  <button
                    onClick={() => updateJobStatus(job.id, 'rejected')}
                    className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
                  >
                    Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {jobs.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No jobs found. Run a search to get started!</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;