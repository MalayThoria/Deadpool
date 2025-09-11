import React, { useState, useEffect } from 'react';
import './HealthManagement.css';
import { useHealth } from '../contexts/HealthContext';
import { healthAPI } from '../services/apiService';

const HealthManagement = () => {
  const { 
    user, 
    healthProfile, 
    recommendations, 
    loading, 
    errors,
    fetchHealthProfile,
    fetchRecommendations 
  } = useHealth();
  const [activeTab, setActiveTab] = useState('recommendations');
  const [diseaseInput, setDiseaseInput] = useState('');
  const [localLoading, setLocalLoading] = useState(false);
  const [localError, setLocalError] = useState('');

  // Fetch user profile on component mount
  useEffect(() => {
    if (user && !healthProfile) {
      fetchHealthProfile();
    }
    if (user && !recommendations) {
      fetchRecommendations();
    }
  }, [user, healthProfile, recommendations]);



  const getRecommendations = async () => {
    if (!diseaseInput.trim()) {
      setLocalError('Please enter a medical condition');
      return;
    }

    setLocalLoading(true);
    setLocalError('');

    try {
      const data = await healthAPI.getHealthRecommendations({
        disease: diseaseInput,
        severity: 'moderate',
        user_context: {
          age: healthProfile?.age || 30,
          gender: healthProfile?.gender || 'not_specified',
          fitness_level: healthProfile?.fitness_level || 'beginner'
        }
      });
      // Recommendations are now managed by HealthContext
    } catch (err) {
      setLocalError('Error getting recommendations');
    } finally {
      setLocalLoading(false);
    }
  };

  const getPersonalizedRecommendations = async () => {
    if (!healthProfile) {
      setLocalError('User profile not available');
      return;
    }
    await fetchRecommendations();
  };

  const renderRecommendations = () => {
    if (!recommendations) return null;

    return (
      <div className="recommendations-container">
        {recommendations.exercise_recommendations && (
          <div className="recommendation-section">
            <h3>🏃‍♂️ Exercise Recommendations</h3>
            <div className="recommendation-content">
              {recommendations.exercise_recommendations.exercises?.map((exercise, index) => (
                <div key={index} className="exercise-card">
                  <h4>{exercise.name}</h4>
                  <p><strong>Type:</strong> {exercise.type}</p>
                  <p><strong>Duration:</strong> {exercise.duration}</p>
                  <p><strong>Intensity:</strong> {exercise.intensity}</p>
                  <p><strong>Description:</strong> {exercise.description}</p>
                  {exercise.precautions && (
                    <p className="precautions"><strong>⚠️ Precautions:</strong> {exercise.precautions}</p>
                  )}
                </div>
              )) || (
                <div className="ai-recommendation">
                  <p>{recommendations.exercise_recommendations}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {recommendations.dietary_recommendations && (
          <div className="recommendation-section">
            <h3>🥗 Dietary Recommendations</h3>
            <div className="recommendation-content">
              {recommendations.dietary_recommendations.foods?.map((food, index) => (
                <div key={index} className="diet-card">
                  <h4>{food.category}</h4>
                  <p><strong>Recommended:</strong> {food.recommended?.join(', ')}</p>
                  <p><strong>Avoid:</strong> {food.avoid?.join(', ')}</p>
                  <p><strong>Notes:</strong> {food.notes}</p>
                </div>
              )) || (
                <div className="ai-recommendation">
                  <p>{recommendations.dietary_recommendations}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {recommendations.general_advice && (
          <div className="recommendation-section">
            <h3>💡 General Health Advice</h3>
            <div className="recommendation-content">
              <p>{recommendations.general_advice}</p>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="health-management">
      <div className="health-header">
        <h2>🏥 Health Management System</h2>
        <p>Get personalized health recommendations based on your medical conditions</p>
      </div>

      <div className="tab-navigation">
        <button 
          className={`tab-button ${activeTab === 'recommendations' ? 'active' : ''}`}
          onClick={() => setActiveTab('recommendations')}
        >
          Disease Recommendations
        </button>
        <button 
          className={`tab-button ${activeTab === 'personalized' ? 'active' : ''}`}
          onClick={() => setActiveTab('personalized')}
        >
          Personalized Plan
        </button>
        <button 
          className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          Health Profile
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'recommendations' && (
          <div className="recommendations-tab">
            <div className="input-section">
              <h3>Get Disease-Specific Recommendations</h3>
              <div className="input-group">
                <input
                  type="text"
                  placeholder="Enter your medical condition (e.g., diabetes, hypertension)"
                  value={diseaseInput}
                  onChange={(e) => setDiseaseInput(e.target.value)}
                  className="disease-input"
                />
                <button 
                  onClick={getRecommendations}
                  disabled={localLoading}
                  className="get-recommendations-btn"
                >
                  {localLoading ? 'Getting Recommendations...' : 'Get Recommendations'}
                </button>
              </div>
            </div>
            {renderRecommendations()}
          </div>
        )}

        {activeTab === 'personalized' && (
          <div className="personalized-tab">
            <div className="input-section">
              <h3>Get Personalized Health Plan</h3>
              <p>Based on your complete health profile and medical history</p>
              <button 
                onClick={getPersonalizedRecommendations}
                disabled={loading || !healthProfile}
                className="get-recommendations-btn"
              >
                {loading ? 'Generating Plan...' : 'Generate Personalized Plan'}
              </button>
            </div>
            {renderRecommendations()}
          </div>
        )}

        {activeTab === 'profile' && (
          <div className="profile-tab">
            <h3>Your Health Profile</h3>
            {healthProfile ? (
              <div className="profile-info">
                <div className="profile-section">
                  <h4>Personal Information</h4>
                  <p><strong>Name:</strong> {healthProfile.first_name} {healthProfile.last_name}</p>
                  <p><strong>Age:</strong> {healthProfile.age || 'Not specified'}</p>
                  <p><strong>Gender:</strong> {healthProfile.gender || 'Not specified'}</p>
                  <p><strong>Fitness Level:</strong> {healthProfile.fitness_level || 'Not specified'}</p>
                </div>
                
                <div className="profile-section">
                  <h4>Medical Information</h4>
                  <p><strong>Medical Conditions:</strong> {healthProfile.medical_conditions || 'None specified'}</p>
                  <p><strong>Allergies:</strong> {healthProfile.allergies || 'None specified'}</p>
                  <p><strong>Current Medications:</strong> {healthProfile.current_medications || 'None specified'}</p>
                  <p><strong>Emergency Contact:</strong> {healthProfile.emergency_contact || 'Not specified'}</p>
                </div>
              </div>
            ) : (
              <p>Loading profile information...</p>
            )}
          </div>
        )}
      </div>

      {(localError || errors?.profile || errors?.recommendations) && (
        <div className="error-message">
          <p>❌ {localError || errors?.profile || errors?.recommendations}</p>
        </div>
      )}
    </div>
  );
};

export default HealthManagement;