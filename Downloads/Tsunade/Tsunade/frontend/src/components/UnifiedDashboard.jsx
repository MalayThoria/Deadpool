import React, { useState, useEffect } from 'react';
import { Calendar, Heart, FileText, Activity, Clock, User, Plus, CheckCircle } from 'lucide-react';
import { useHealth } from '../contexts/HealthContext';
import PrescriptionUpload from './PrescriptionUpload';

const UnifiedDashboard = ({ 
  onProcessPrescription, 
  extractedText, 
  medicines, 
  onClearResults,
  onAddChatMessage 
}) => {
  const { 
    user, 
    prescriptions, 
    healthProfile, 
    recommendations, 
    calendarEvents, 
    loading, 
    errors,
    processPrescription 
  } = useHealth();
  const [activeSection, setActiveSection] = useState('overview');

  // Handle prescription processing with context integration
  const handlePrescriptionProcess = async (prescriptionData) => {
    await processPrescription(prescriptionData);
    if (onProcessPrescription) {
      onProcessPrescription(prescriptionData);
    }
  };



  const renderOverview = () => (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <div className="flex items-center">
            <FileText className="h-8 w-8 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Prescriptions</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {prescriptions.length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <div className="flex items-center">
            <Heart className="h-8 w-8 text-red-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Conditions</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {healthProfile?.medical_conditions?.length || 0}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <div className="flex items-center">
            <Activity className="h-8 w-8 text-green-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Recommendations</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {recommendations.length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <div className="flex items-center">
            <Calendar className="h-8 w-8 text-purple-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Upcoming</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {calendarEvents.length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Prescriptions */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Prescriptions
          </h3>
          {prescriptions.length > 0 ? (
            <div className="space-y-3">
              {prescriptions.slice(0, 3).map((prescription, index) => (
                <div key={index} className="flex items-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <FileText className="h-5 w-5 text-blue-500 mr-3" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {prescription.medicines?.length || 0} medicines detected
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date().toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400 text-sm">No prescriptions analyzed yet</p>
          )}
        </div>

        {/* Health Recommendations */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Health Recommendations
          </h3>
          {recommendations.length > 0 ? (
            <div className="space-y-3">
              {recommendations.slice(0, 3).map((rec, index) => (
                <div key={index} className="flex items-start p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {rec.title || rec.exercise || rec.food || 'Health recommendation'}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {rec.description || rec.duration || rec.benefits || 'Personalized for you'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400 text-sm">No recommendations available</p>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => setActiveSection('prescription')}
            className="flex items-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
          >
            <Plus className="h-6 w-6 text-blue-500 mr-3" />
            <div className="text-left">
              <p className="font-medium text-blue-900 dark:text-blue-100">Upload Prescription</p>
              <p className="text-sm text-blue-600 dark:text-blue-300">Analyze new prescription</p>
            </div>
          </button>
          
          <button
            onClick={() => setActiveSection('calendar')}
            className="flex items-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors"
          >
            <Calendar className="h-6 w-6 text-purple-500 mr-3" />
            <div className="text-left">
              <p className="font-medium text-purple-900 dark:text-purple-100">Schedule Events</p>
              <p className="text-sm text-purple-600 dark:text-purple-300">Manage calendar</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeSection) {
      case 'prescription':
        return (
          <PrescriptionUpload
            onProcessPrescription={handlePrescriptionProcess}
            extractedText={extractedText}
            medicines={medicines}
            onClearResults={onClearResults}
            onAddChatMessage={onAddChatMessage}
          />
        );
      case 'calendar':
        return (
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Calendar Integration
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Calendar functionality is integrated within the prescription analysis and health management workflows.
              Upload a prescription or get health recommendations to automatically schedule related events.
            </p>
          </div>
        );
      default:
        return renderOverview();
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Navigation Tabs */}
      <div className="mb-6">
        <nav className="flex space-x-1 bg-gray-100 dark:bg-gray-700 p-1 rounded-lg">
          {[
            { id: 'overview', label: 'Overview', icon: Activity },
            { id: 'prescription', label: 'RX Assistant', icon: FileText },
            { id: 'calendar', label: 'Calendar', icon: Calendar }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveSection(id)}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeSection === id
                  ? 'bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Icon className="h-4 w-4 mr-2" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Error Display */}
      {(errors.profile || errors.recommendations) && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-red-600 dark:text-red-400">{errors.profile || errors.recommendations}</p>
        </div>
      )}

      {/* Loading State */}
      {(loading.profile || loading.recommendations) && (
        <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <p className="text-blue-600 dark:text-blue-400">Loading data...</p>
        </div>
      )}

      {/* Main Content */}
      {renderContent()}
    </div>
  );
};

export default UnifiedDashboard;