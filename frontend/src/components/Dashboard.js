import React from 'react';

const Dashboard = ({ stats }) => {
  const statusCounts = stats.status_counts || [];
  const totalJobs = stats.total_jobs || 0;
  const avgScore = Math.round(stats.avg_match_score || 0);
  const topCompanies = stats.top_companies || [];

  const getStatusInfo = (status) => {
    const statusMap = {
      'new': { label: 'New Opportunities', color: 'blue', icon: '🆕' },
      'applied': { label: 'Applications Sent', color: 'yellow', icon: '📄' },
      'interviewing': { label: 'In Interview Process', color: 'green', icon: '💬' },
      'offer': { label: 'Offers Received', color: 'purple', icon: '🎉' },
      'rejected': { label: 'Not Moving Forward', color: 'red', icon: '❌' }
    };
    return statusMap[status] || { label: status, color: 'gray', icon: '📊' };
  };

  const getColorClasses = (color) => {
    const colorMap = {
      'blue': 'bg-blue-100 text-blue-800 border-blue-200',
      'yellow': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'green': 'bg-green-100 text-green-800 border-green-200',
      'purple': 'bg-purple-100 text-purple-800 border-purple-200',
      'red': 'bg-red-100 text-red-800 border-red-200',
      'gray': 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colorMap[color] || colorMap.gray;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {/* Total Jobs */}
      <div className="bg-white overflow-hidden shadow-lg rounded-lg border border-gray-200">
        <div className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="text-3xl font-bold text-indigo-600">{totalJobs}</div>
            </div>
            <div className="ml-4 w-0 flex-1">
              <dt className="text-sm font-medium text-gray-500 truncate">Total Opportunities</dt>
              <dd className="text-xs text-gray-400 mt-1">All time</dd>
            </div>
            <div className="text-2xl">🎯</div>
          </div>
        </div>
      </div>

      {/* Average Match Score */}
      <div className="bg-white overflow-hidden shadow-lg rounded-lg border border-gray-200">
        <div className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="text-3xl font-bold text-green-600">{avgScore}%</div>
            </div>
            <div className="ml-4 w-0 flex-1">
              <dt className="text-sm font-medium text-gray-500 truncate">Avg Match Score</dt>
              <dd className="text-xs text-gray-400 mt-1">AI-powered matching</dd>
            </div>
            <div className="text-2xl">🤖</div>
          </div>
        </div>
      </div>

      {/* Application Status Breakdown */}
      {statusCounts.slice(0, 2).map((statusCount) => {
        const statusInfo = getStatusInfo(statusCount.status);
        return (
          <div key={statusCount.status} className="bg-white overflow-hidden shadow-lg rounded-lg border border-gray-200">
            <div className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`text-3xl font-bold text-${statusInfo.color}-600`}>
                    {statusCount.count}
                  </div>
                </div>
                <div className="ml-4 w-0 flex-1">
                  <dt className="text-sm font-medium text-gray-500 truncate">{statusInfo.label}</dt>
                  <dd className="text-xs text-gray-400 mt-1">Current status</dd>
                </div>
                <div className="text-2xl">{statusInfo.icon}</div>
              </div>
            </div>
          </div>
        );
      })}

      {/* Status Breakdown */}
      {statusCounts.length > 0 && (
        <div className="md:col-span-2 lg:col-span-2 bg-white overflow-hidden shadow-lg rounded-lg border border-gray-200">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Application Pipeline</h3>
            <div className="space-y-3">
              {statusCounts.map((statusCount) => {
                const statusInfo = getStatusInfo(statusCount.status);
                const percentage = totalJobs > 0 ? Math.round((statusCount.count / totalJobs) * 100) : 0;
                
                return (
                  <div key={statusCount.status} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-lg">{statusInfo.icon}</span>
                      <span className="text-sm font-medium text-gray-700">{statusInfo.label}</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full bg-${statusInfo.color}-500`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-bold text-gray-900 w-8">{statusCount.count}</span>
                      <span className="text-xs text-gray-500 w-10">{percentage}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Top Companies */}
      {topCompanies.length > 0 && (
        <div className="md:col-span-2 lg:col-span-2 bg-white overflow-hidden shadow-lg rounded-lg border border-gray-200">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🏢 Top Companies</h3>
            <div className="space-y-2">
              {topCompanies.slice(0, 5).map((company, index) => (
                <div key={company.company_name} className="flex items-center justify-between py-2">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-medium text-gray-600">#{index + 1}</span>
                    <span className="text-sm font-semibold text-gray-900">{company.company_name}</span>
                  </div>
                  <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                    {company.count} jobs
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="lg:col-span-4 bg-gradient-to-r from-blue-50 to-indigo-50 overflow-hidden shadow-lg rounded-lg border border-blue-200">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">🚀 Next Steps</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-white rounded-lg shadow-sm">
              <div className="text-2xl mb-2">🔍</div>
              <h4 className="font-medium text-gray-900">Keep Searching</h4>
              <p className="text-sm text-gray-600 mt-1">Run daily searches to find new opportunities</p>
            </div>
            <div className="text-center p-4 bg-white rounded-lg shadow-sm">
              <div className="text-2xl mb-2">📬</div>
              <h4 className="font-medium text-gray-900">Apply to Top Matches</h4>
              <p className="text-sm text-gray-600 mt-1">Focus on jobs with 85+ match scores</p>
            </div>
            <div className="text-center p-4 bg-white rounded-lg shadow-sm">
              <div className="text-2xl mb-2">🤝</div>
              <h4 className="font-medium text-gray-900">Network with Contacts</h4>
              <p className="text-sm text-gray-600 mt-1">Reach out to LinkedIn connections</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;