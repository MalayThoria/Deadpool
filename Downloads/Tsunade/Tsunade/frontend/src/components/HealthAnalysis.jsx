import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Heart, 
  Search, 
  Filter, 
  Calendar, 
  Clock, 
  Target, 
  TrendingUp,
  ChevronRight,
  Activity,
  AlertCircle,
  CheckCircle,
  Star,
  Play,
  Pause,
  RotateCcw
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import apiService from '../services/apiService';

const HealthAnalysis = ({ user, isDarkMode }) => {
  const [diseases, setDiseases] = useState([]);
  const [selectedDisease, setSelectedDisease] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('diseases');
  const [schedules, setSchedules] = useState([]);

  useEffect(() => {
    if (user) {
      fetchDiseases();
      fetchUserProfile();
    }
  }, [user]);

  const fetchDiseases = async () => {
    try {
      const response = await apiService.get('/api/v1/health-analysis/diseases');
      setDiseases(response.data);
    } catch (error) {
      console.error('Error fetching diseases:', error);
      toast.error('Failed to load disease conditions');
    }
  };

  const fetchUserProfile = async () => {
    try {
      const response = await apiService.get('/api/v1/health-analysis/profile');
      setUserProfile(response.data);
    } catch (error) {
      console.error('Error fetching user profile:', error);
    }
  };

  const handleDiseaseSelect = async (disease) => {
    setSelectedDisease(disease);
    setLoading(true);
    
    try {
      const response = await apiService.post('/api/v1/health-analysis/recommendations', {
        disease_ids: [disease.id],
        fitness_level: userProfile?.fitness_level || 'beginner',
        preferences: {
          duration_preference: 30,
          intensity_preference: 'moderate'
        }
      });
      
      setRecommendations(response.data.recommendations);
      setActiveTab('recommendations');
      toast.success(`Found ${response.data.recommendations.length} exercises for ${disease.name}`);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      toast.error('Failed to get exercise recommendations');
    } finally {
      setLoading(false);
    }
  };

  const createSchedule = async (exerciseId, frequency) => {
    try {
      const response = await apiService.post('/api/v1/health-analysis/schedule', {
        exercise_id: exerciseId,
        frequency: frequency,
        start_date: new Date().toISOString().split('T')[0],
        duration_weeks: 4
      });
      
      toast.success('Exercise schedule created successfully!');
      fetchSchedules();
    } catch (error) {
      console.error('Error creating schedule:', error);
      toast.error('Failed to create exercise schedule');
    }
  };

  const fetchSchedules = async () => {
    try {
      const response = await apiService.get('/api/v1/health-analysis/schedules');
      setSchedules(response.data);
    } catch (error) {
      console.error('Error fetching schedules:', error);
    }
  };

  const filteredDiseases = diseases.filter(disease =>
    disease.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    disease.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const DiseaseCard = ({ disease }) => (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      whileHover={{ scale: 1.02, y: -2 }}
      className="glass-card p-6 cursor-pointer border border-white/20 dark:border-gray-700/20"
      onClick={() => handleDiseaseSelect(disease)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {disease.name}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            {disease.description}
          </p>
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              disease.severity === 'mild' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
              disease.severity === 'moderate' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
              'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
            }`}>
              {disease.severity}
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {disease.exercise_count} exercises available
            </span>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-gray-400" />
      </div>
    </motion.div>
  );

  const ExerciseCard = ({ exercise }) => (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card p-6 border border-white/20 dark:border-gray-700/20"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {exercise.name}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            {exercise.description}
          </p>
        </div>
        <div className="flex items-center space-x-1">
          {[...Array(5)].map((_, i) => (
            <Star
              key={i}
              className={`w-4 h-4 ${
                i < exercise.suitability_score ? 'text-yellow-400 fill-current' : 'text-gray-300'
              }`}
            />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="flex items-center space-x-2">
          <Clock className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {exercise.duration_minutes} min
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <Target className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {exercise.difficulty_level}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {exercise.category}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {exercise.calories_per_minute} cal/min
          </span>
        </div>
      </div>

      {exercise.instructions && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
            Instructions:
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {exercise.instructions}
          </p>
        </div>
      )}

      <div className="flex space-x-2">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => createSchedule(exercise.id, 'weekly')}
          className="flex-1 bg-gradient-to-r from-primary-500 to-secondary-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:shadow-lg transition-all duration-200"
        >
          <Calendar className="w-4 h-4 inline mr-2" />
          Schedule Weekly
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => createSchedule(exercise.id, 'daily')}
          className="flex-1 bg-white/50 dark:bg-gray-800/50 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg text-sm font-medium border border-white/20 dark:border-gray-700/20 hover:shadow-lg transition-all duration-200"
        >
          <Clock className="w-4 h-4 inline mr-2" />
          Schedule Daily
        </motion.button>
      </div>
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="flex items-center justify-center mb-4">
            <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-2xl">
              <Heart className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold gradient-text mb-2">
            Health Analysis & Exercise Recommendations
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Get personalized exercise recommendations based on your health conditions
          </p>
        </motion.div>

        {/* Navigation Tabs */}
        <div className="flex justify-center mb-8">
          <div className="glass-card p-1 rounded-xl border border-white/20 dark:border-gray-700/20">
            <div className="flex space-x-1">
              {[
                { id: 'diseases', label: 'Health Conditions', icon: Heart },
                { id: 'recommendations', label: 'Recommendations', icon: Target },
                { id: 'schedules', label: 'My Schedules', icon: Calendar }
              ].map((tab) => (
                <motion.button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white shadow-lg'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <tab.icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </motion.button>
              ))}
            </div>
          </div>
        </div>

        {/* Content */}
        <AnimatePresence mode="wait">
          {activeTab === 'diseases' && (
            <motion.div
              key="diseases"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              {/* Search */}
              <div className="mb-6">
                <div className="relative max-w-md mx-auto">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search health conditions..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 glass-card border border-white/20 dark:border-gray-700/20 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>

              {/* Disease Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <AnimatePresence>
                  {filteredDiseases.map((disease) => (
                    <DiseaseCard key={disease.id} disease={disease} />
                  ))}
                </AnimatePresence>
              </div>
            </motion.div>
          )}

          {activeTab === 'recommendations' && (
            <motion.div
              key="recommendations"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              {selectedDisease ? (
                <div>
                  <div className="text-center mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                      Exercise Recommendations for {selectedDisease.name}
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400">
                      Personalized exercises tailored to your condition
                    </p>
                  </div>

                  {loading ? (
                    <div className="flex items-center justify-center py-12">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {recommendations.map((rec) => (
                        <ExerciseCard key={rec.id} exercise={rec} />
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12">
                  <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    No Health Condition Selected
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Please select a health condition to see personalized exercise recommendations
                  </p>
                  <motion.button
                    onClick={() => setActiveTab('diseases')}
                    className="bg-gradient-to-r from-primary-500 to-secondary-500 text-white px-6 py-3 rounded-lg font-medium hover:shadow-lg transition-all duration-200"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Browse Health Conditions
                  </motion.button>
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'schedules' && (
            <motion.div
              key="schedules"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  My Exercise Schedules
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Track your scheduled exercises and progress
                </p>
              </div>

              {schedules.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {schedules.map((schedule) => (
                    <motion.div
                      key={schedule.id}
                      layout
                      className="glass-card p-6 border border-white/20 dark:border-gray-700/20"
                    >
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        {schedule.exercise_name}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                        {schedule.frequency} • {schedule.duration_weeks} weeks
                      </p>
                      <div className="flex items-center justify-between">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          schedule.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                          'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
                        }`}>
                          {schedule.is_active ? 'Active' : 'Completed'}
                        </span>
                        <div className="flex space-x-2">
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            className="p-2 rounded-lg bg-white/50 dark:bg-gray-800/50 text-gray-600 dark:text-gray-400 hover:text-primary-500"
                          >
                            <Play className="w-4 h-4" />
                          </motion.button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    No Schedules Yet
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Create your first exercise schedule by selecting exercises from recommendations
                  </p>
                  <motion.button
                    onClick={() => setActiveTab('diseases')}
                    className="bg-gradient-to-r from-primary-500 to-secondary-500 text-white px-6 py-3 rounded-lg font-medium hover:shadow-lg transition-all duration-200"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Get Started
                  </motion.button>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default HealthAnalysis;