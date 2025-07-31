import React, { useState } from 'react';

const SearchControls = ({ onRunSearch, onFilterChange, searchRunning, stats }) => {
  const [filters, setFilters] = useState({
    status: '',
    minScore: '',
    sortBy: 'match_score'
  });

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        {/* Search Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center space-y-4 sm:space-y-0 sm:space-x-4">
          <button
            onClick={onRunSearch}
            disabled={searchRunning}
            className={`flex items-center px-6 py-3 rounded-lg font-medium transition-all ${
              searchRunning
                ? 'bg-blue-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 hover:shadow-lg'
            } text-white`}
          >
            {searchRunning ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Searching...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Run New Search
              </>
            )}
          </button>

          <div className="text-sm text-gray-600">
            <span className="font-medium">Last search:</span> Find senior PM roles in AI, consumer tech, and more
          </div>
        </div>

        {/* Quick Stats */}
        <div className="flex items-center space-x-6 text-sm">
          <div className="text-center">
            <div className="font-bold text-2xl text-blue-600">{stats.total_jobs || 0}</div>
            <div className="text-gray-500">Total Jobs</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-2xl text-green-600">
              {stats.status_counts?.find(s => s.status === 'new')?.count || 0}
            </div>
            <div className="text-gray-500">New</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-2xl text-yellow-600">
              {stats.status_counts?.find(s => s.status === 'applied')?.count || 0}
            </div>
            <div className="text-gray-500">Applied</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center space-y-4 sm:space-y-0 sm:space-x-6">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Status:</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Active Jobs</option>
              <option value="new">New</option>
              <option value="applied">Applied</option>
              <option value="interviewing">Interviewing</option>
              <option value="offer">Offer</option>
              <option value="rejected">Rejected Only</option>
              <option value="all">All (Including Rejected)</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Min Score:</label>
            <input
              type="number"
              value={filters.minScore}
              onChange={(e) => handleFilterChange('minScore', e.target.value)}
              placeholder="e.g. 80"
              className="border border-gray-300 rounded-md px-3 py-2 text-sm w-20 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Sort by:</label>
            <select
              value={filters.sortBy}
              onChange={(e) => handleFilterChange('sortBy', e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="match_score">Match Score</option>
              <option value="created_at">Date Added</option>
              <option value="company_name">Company</option>
            </select>
          </div>

          <div className="flex-1"></div>

          <div className="text-sm text-gray-500">
            Showing {stats.total_jobs || 0} opportunities
          </div>
        </div>
      </div>

      {/* Search Insights */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-2">🎯 Your Search Profile</h4>
        <div className="text-sm text-blue-800 space-y-1">
          <p><strong>Roles:</strong> Senior PM, Principal PM, Founding PM, Chief of Staff, Head of Operations</p>
          <p><strong>Industries:</strong> AI productivity tools, Consumer tech, Marketplaces, Creative tech, Travel</p>
          <p><strong>Locations:</strong> Remote, Seattle, San Francisco, New York</p>
          <p><strong>Background:</strong> MBA from Tuck, 8+ years experience (Amazon, Datavant, Expert Network)</p>
        </div>
      </div>
    </div>
  );
};

export default SearchControls;