import React, { useState, useEffect } from 'react';
import axios from 'axios';

const GoogleSheetsSync = ({ apiBase, onSyncComplete }) => {
  const [sheetsUrl, setSheetsUrl] = useState('');
  const [sheetsStatus, setSheetsStatus] = useState(null);
  const [syncLoading, setSyncLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'

  useEffect(() => {
    checkSheetsStatus();
  }, []);

  const checkSheetsStatus = async () => {
    try {
      const response = await axios.get(`${apiBase}/api/sheets/status`);
      setSheetsStatus(response.data);
    } catch (error) {
      console.error('Error checking sheets status:', error);
      setSheetsStatus({ available: false, message: 'Error checking status' });
    }
  };

  const showMessage = (text, type) => {
    setMessage(text);
    setMessageType(type);
    setTimeout(() => {
      setMessage('');
      setMessageType('');
    }, 5000);
  };

  const handleSyncToSheets = async () => {
    if (!sheetsUrl.trim()) {
      showMessage('Please enter a Google Sheets URL', 'error');
      return;
    }

    setSyncLoading(true);
    try {
      const response = await axios.post(`${apiBase}/api/sheets/sync-to-sheets`, {
        spreadsheet_url: sheetsUrl
      });

      showMessage(response.data.message, 'success');
      if (onSyncComplete) onSyncComplete('sync');
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to sync to Google Sheets';
      showMessage(errorMsg, 'error');
    } finally {
      setSyncLoading(false);
    }
  };

  const handleImportFromSheets = async () => {
    if (!sheetsUrl.trim()) {
      showMessage('Please enter a Google Sheets URL', 'error');
      return;
    }

    setImportLoading(true);
    try {
      const response = await axios.post(`${apiBase}/api/sheets/import-from-sheets`, {
        spreadsheet_url: sheetsUrl
      });

      showMessage(response.data.message, 'success');
      if (onSyncComplete) onSyncComplete('import');
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to import from Google Sheets';
      showMessage(errorMsg, 'error');
    } finally {
      setImportLoading(false);
    }
  };

  if (!sheetsStatus) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Checking Google Sheets status...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">📊 Google Sheets Integration</h3>
        <div className={`px-3 py-1 rounded-full text-sm ${
          sheetsStatus.available 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          {sheetsStatus.available ? '✅ Ready' : '❌ Not Configured'}
        </div>
      </div>

      {!sheetsStatus.available && (
        <div className="mb-4 p-4 bg-yellow-50 border-l-4 border-yellow-400">
          <div className="text-sm text-yellow-700">
            <strong>Setup Required:</strong> Google Sheets API is not configured. 
            Please add the GOOGLE_SERVICE_ACCOUNT_JSON environment variable to Railway.
          </div>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Google Sheets URL
          </label>
          <input
            type="url"
            value={sheetsUrl}
            onChange={(e) => setSheetsUrl(e.target.value)}
            placeholder="https://docs.google.com/spreadsheets/d/your-sheet-id/edit..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            disabled={!sheetsStatus.available}
          />
          <p className="text-xs text-gray-500 mt-1">
            Make sure the service account has edit access to this spreadsheet
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleSyncToSheets}
            disabled={!sheetsStatus.available || syncLoading || !sheetsUrl.trim()}
            className={`flex-1 flex items-center justify-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              !sheetsStatus.available || syncLoading || !sheetsUrl.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {syncLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Syncing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Export to Sheets
              </>
            )}
          </button>

          <button
            onClick={handleImportFromSheets}
            disabled={!sheetsStatus.available || importLoading || !sheetsUrl.trim()}
            className={`flex-1 flex items-center justify-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              !sheetsStatus.available || importLoading || !sheetsUrl.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            {importLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Importing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 11l3 3m0 0l3-3m-3 3V8" />
                </svg>
                Import from Sheets
              </>
            )}
          </button>
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

        <div className="text-xs text-gray-500 space-y-1">
          <p><strong>Export to Sheets:</strong> Overwrites the spreadsheet with all jobs from your tracker</p>
          <p><strong>Import from Sheets:</strong> Adds new jobs from the spreadsheet to your tracker (duplicates are skipped)</p>
        </div>
      </div>
    </div>
  );
};

export default GoogleSheetsSync;