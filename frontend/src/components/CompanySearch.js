import React, { useState } from 'react';
import axios from 'axios';

const CompanySearch = ({ apiBase, onSearchComplete }) => {
  const [companyName, setCompanyName] = useState('');
  const [searching, setSearching] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'

  const showMessage = (text, type) => {
    setMessage(text);
    setMessageType(type);
    setTimeout(() => {
      setMessage('');
      setMessageType('');
    }, 5000);
  };

  const handleCompanySearch = async () => {
    const company = companyName.trim();
    if (!company) {
      showMessage('Please enter a company name', 'error');
      return;
    }

    setSearching(true);
    console.log(`🏢 Starting company search for: ${company}`);

    try {
      const response = await axios.post(`${apiBase}/api/search-company`, {
        company_name: company
      }, {
        timeout: 120000, // 2 minute timeout
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log('✅ Company search completed:', response.data);
      
      const { jobs_found, new_jobs_saved, message: responseMessage } = response.data;
      
      if (jobs_found > 0) {
        showMessage(`🎉 ${responseMessage}`, 'success');
      } else {
        showMessage(`🔍 ${responseMessage}`, 'success');
      }

      // Refresh the main job list if new jobs were found
      if (new_jobs_saved > 0 && onSearchComplete) {
        onSearchComplete('company_search');
      }

    } catch (error) {
      console.error('❌ Company search error:', error);
      
      let errorMsg = 'Company search failed';
      if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      showMessage(`❌ ${errorMsg}`, 'error');
    } finally {
      setSearching(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !searching) {
      handleCompanySearch();
    }
  };

  const suggestedCompanies = [
    'Microsoft', 'Google', 'Apple', 'Meta', 'Netflix', 'Salesforce',
    'Stripe', 'Figma', 'Notion', 'Canva', 'Spotify', 'Uber', 'Lyft',
    'Coinbase', 'Robinhood', 'Calm', 'Headspace', 'Peloton', 'Nike'
  ];

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">🏢 Custom Company Search</h3>
        <div className="text-xs text-gray-500">
          Search any company for PM roles
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Company Name
          </label>
          <div className="flex space-x-3">
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="e.g., Microsoft, Google, Stripe..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              disabled={searching}
            />
            <button
              onClick={handleCompanySearch}
              disabled={searching || !companyName.trim()}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
                searching || !companyName.trim()
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {searching ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Searching...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  Search Company
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick Company Suggestions */}
        <div>
          <p className="text-xs text-gray-500 mb-2">Quick suggestions:</p>
          <div className="flex flex-wrap gap-2">
            {suggestedCompanies.slice(0, 8).map((company) => (
              <button
                key={company}
                onClick={() => setCompanyName(company)}
                disabled={searching}
                className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                {company}
              </button>
            ))}
          </div>
        </div>

        {message && (
          <div className={`p-3 rounded-md text-sm ${
            messageType === 'success' 
              ? 'bg-green-50 text-green-700 border border-green-200' 
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
            {message}
          </div>
        )}

        <div className="text-xs text-gray-500 bg-blue-50 p-3 rounded-md">
          <strong>🔍 Search Strategy:</strong> This searches the company's career pages, Google Jobs, 
          and web for product manager, senior PM, head of product, and director roles. 
          Results are AI-scored and automatically added to your tracker.
        </div>
      </div>
    </div>
  );
};

export default CompanySearch;