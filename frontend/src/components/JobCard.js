import React, { useState } from 'react';

const JobCard = ({ job, onStatusUpdate }) => {
  const [expanded, setExpanded] = useState(false);
  const [showContacts, setShowContacts] = useState(false);

  const getStatusColor = (status) => {
    const colors = {
      'new': 'bg-blue-100 text-blue-800 border-blue-200',
      'applied': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'interviewing': 'bg-green-100 text-green-800 border-green-200',
      'rejected': 'bg-red-100 text-red-800 border-red-200',
      'offer': 'bg-purple-100 text-purple-800 border-purple-200'
    };
    return colors[status] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600 font-bold';
    if (score >= 80) return 'text-blue-600 font-semibold';
    if (score >= 70) return 'text-yellow-600 font-medium';
    return 'text-gray-600';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleStatusUpdate = (newStatus) => {
    onStatusUpdate(job.id, newStatus);
  };

  const contacts = job.contacts ? (Array.isArray(job.contacts) ? job.contacts : []) : [];

  return (
    <div className="bg-white shadow-lg rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h3 className="text-xl font-bold text-gray-900">{job.title}</h3>
              <span className={`px-3 py-1 text-sm font-medium rounded-full border ${getStatusColor(job.status)}`}>
                {job.status.toUpperCase()}
              </span>
              {job.match_score && (
                <span className={`text-lg font-bold ${getScoreColor(job.match_score)}`}>
                  {job.match_score}% Match
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-4 text-gray-600">
              <span className="font-semibold text-gray-800">{job.company_name}</span>
              {job.location && <span>📍 {job.location}</span>}
              <span className="text-sm">🕒 {formatDate(job.created_at)}</span>
            </div>

            {job.job_url && (
              <a
                href={job.job_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center mt-3 text-blue-600 hover:text-blue-800 font-medium"
              >
                <span>View Job Posting</span>
                <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col space-y-2 ml-4">
            {job.status === 'new' && (
              <button
                onClick={() => handleStatusUpdate('applied')}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Mark Applied
              </button>
            )}
            {job.status === 'applied' && (
              <button
                onClick={() => handleStatusUpdate('interviewing')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Interviewing
              </button>
            )}
            <button
              onClick={() => handleStatusUpdate('rejected')}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Not Interested
            </button>
          </div>
        </div>
      </div>

      {/* Expandable Content */}
      <div className="px-6 py-4">
        <div className="flex space-x-4">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {expanded ? '🔽 Hide Details' : '▶️ Show AI Analysis'}
          </button>
          {contacts.length > 0 && (
            <button
              onClick={() => setShowContacts(!showContacts)}
              className="text-purple-600 hover:text-purple-800 text-sm font-medium"
            >
              {showContacts ? '🔽 Hide Contacts' : `▶️ Show ${contacts.length} Contacts`}
            </button>
          )}
        </div>

        {/* AI Analysis */}
        {expanded && job.ai_analysis && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-2">🤖 AI Match Analysis</h4>
            <p className="text-blue-800 text-sm leading-relaxed">{job.ai_analysis}</p>
          </div>
        )}

        {/* Contacts */}
        {showContacts && contacts.length > 0 && (
          <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
            <h4 className="font-semibold text-purple-900 mb-3">👥 LinkedIn Contacts</h4>
            <div className="space-y-3">
              {contacts.map((contact, index) => (
                <div key={index} className="bg-white p-3 rounded-md border border-purple-200">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h5 className="font-medium text-gray-900">{contact.name}</h5>
                      {contact.snippet && (
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">{contact.snippet}</p>
                      )}
                    </div>
                    {contact.linkedin && (
                      <a
                        href={contact.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-3 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors"
                      >
                        LinkedIn
                      </a>
                    )}
                  </div>
                  
                  {/* Networking Message Template */}
                  <div className="mt-3 p-2 bg-gray-50 rounded text-xs">
                    <strong>Suggested Message:</strong>
                    <p className="mt-1 text-gray-700">
                      "Hi {contact.name?.split(' ')[0] || 'there'}, I came across {job.company_name}'s {job.title} posting and was impressed by [specific company insight]. As a Tuck MBA with PM experience at Amazon and healthcare data companies, I'm drawn to [relevant challenge]. Would you be open to a brief conversation about the product challenges you're tackling?"
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Job Description Preview */}
        {job.description && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-700 line-clamp-3">{job.description}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobCard;