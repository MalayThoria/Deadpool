import React, { createContext, useContext, useReducer, useEffect } from 'react';
import apiService, { healthAPI, calendarAPI, prescriptionAPI } from '../services/apiService';

// Initial state
const initialState = {
  user: null,
  isAuthenticated: false,
  prescriptions: [],
  healthProfile: null,
  recommendations: [],
  calendarEvents: [],
  currentPrescription: null,
  loading: {
    profile: false,
    prescriptions: false,
    recommendations: false,
    calendar: false
  },
  errors: {
    profile: null,
    prescriptions: null,
    recommendations: null,
    calendar: null
  }
};

// Action types
const ActionTypes = {
  SET_USER: 'SET_USER',
  SET_AUTHENTICATED: 'SET_AUTHENTICATED',
  ADD_PRESCRIPTION: 'ADD_PRESCRIPTION',
  SET_HEALTH_PROFILE: 'SET_HEALTH_PROFILE',
  SET_RECOMMENDATIONS: 'SET_RECOMMENDATIONS',
  ADD_CALENDAR_EVENT: 'ADD_CALENDAR_EVENT',
  SET_CALENDAR_EVENTS: 'SET_CALENDAR_EVENTS',
  SET_CURRENT_PRESCRIPTION: 'SET_CURRENT_PRESCRIPTION',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  RESET_STATE: 'RESET_STATE'
};

// Reducer
const healthReducer = (state, action) => {
  switch (action.type) {
    case ActionTypes.SET_USER:
      return { ...state, user: action.payload };
    
    case ActionTypes.SET_AUTHENTICATED:
      return { ...state, isAuthenticated: action.payload };
    
    case ActionTypes.ADD_PRESCRIPTION:
      return {
        ...state,
        prescriptions: [action.payload, ...state.prescriptions.slice(0, 9)], // Keep last 10
        currentPrescription: action.payload
      };
    
    case ActionTypes.SET_HEALTH_PROFILE:
      return { ...state, healthProfile: action.payload };
    
    case ActionTypes.SET_RECOMMENDATIONS:
      return { ...state, recommendations: action.payload };
    
    case ActionTypes.ADD_CALENDAR_EVENT:
      return {
        ...state,
        calendarEvents: [action.payload, ...state.calendarEvents]
      };
    
    case ActionTypes.SET_CALENDAR_EVENTS:
      return { ...state, calendarEvents: action.payload };
    
    case ActionTypes.SET_CURRENT_PRESCRIPTION:
      return { ...state, currentPrescription: action.payload };
    
    case ActionTypes.SET_LOADING:
      return {
        ...state,
        loading: { ...state.loading, [action.payload.key]: action.payload.value }
      };
    
    case ActionTypes.SET_ERROR:
      return {
        ...state,
        errors: { ...state.errors, [action.payload.key]: action.payload.value }
      };
    
    case ActionTypes.CLEAR_ERROR:
      return {
        ...state,
        errors: { ...state.errors, [action.payload]: null }
      };
    
    case ActionTypes.RESET_STATE:
      return initialState;
    
    default:
      return state;
  }
};

// Context
const HealthContext = createContext();

// Provider component
export const HealthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(healthReducer, initialState);

  // Helper functions
  const setLoading = (key, value) => {
    dispatch({ type: ActionTypes.SET_LOADING, payload: { key, value } });
  };

  const setError = (key, value) => {
    dispatch({ type: ActionTypes.SET_ERROR, payload: { key, value } });
  };

  const clearError = (key) => {
    dispatch({ type: ActionTypes.CLEAR_ERROR, payload: key });
  };

  // API functions
  const fetchHealthProfile = async () => {
    setLoading('profile', true);
    clearError('profile');
    
    try {
      const data = await healthAPI.getProfile();
      dispatch({ type: ActionTypes.SET_HEALTH_PROFILE, payload: data });
    } catch (error) {
      setError('profile', error.message);
    } finally {
      setLoading('profile', false);
    }
  };

  const fetchRecommendations = async () => {
    setLoading('recommendations', true);
    clearError('recommendations');
    
    try {
      const data = await healthAPI.getRecommendations();
      dispatch({ type: ActionTypes.SET_RECOMMENDATIONS, payload: data.recommendations || [] });
    } catch (error) {
      setError('recommendations', error.message);
    } finally {
      setLoading('recommendations', false);
    }
  };

  const fetchCalendarEvents = async () => {
    setLoading('calendar', true);
    clearError('calendar');
    
    try {
      const data = await calendarAPI.getEvents();
      dispatch({ type: ActionTypes.SET_CALENDAR_EVENTS, payload: data });
    } catch (error) {
      setError('calendar', error.message);
    } finally {
      setLoading('calendar', false);
    }
  };

  const processPrescription = async (prescriptionData) => {
    // Add prescription to state
    dispatch({ type: ActionTypes.ADD_PRESCRIPTION, payload: prescriptionData });
    
    // Automatically refresh related data
    await Promise.all([
      fetchHealthProfile(),
      fetchRecommendations()
    ]);
    
    // Create calendar events for medications
    if (prescriptionData.extracted_info?.medications) {
      for (const medication of prescriptionData.extracted_info.medications) {
        await createMedicationReminder(medication);
      }
    }
  };

  const createMedicationReminder = async (medication) => {
    try {
      const eventData = await calendarAPI.createEvent({
        title: `Take ${medication.name}`,
        description: `Medication reminder: ${medication.name} - ${medication.dosage}\nFrequency: ${medication.frequency}`,
        start_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        duration_minutes: 15,
        recurrence: medication.frequency?.toLowerCase().includes('daily') ? 'daily' : null
      });
      
      dispatch({ type: ActionTypes.ADD_CALENDAR_EVENT, payload: eventData });
    } catch (error) {
      console.error('Error creating medication reminder:', error);
    }
  };

  const login = (userData) => {
    dispatch({ type: ActionTypes.SET_USER, payload: userData });
    dispatch({ type: ActionTypes.SET_AUTHENTICATED, payload: true });
    
    // Update API service token
    const token = localStorage.getItem('access_token');
    if (token) {
      apiService.setToken(token);
    }
    
    // Fetch initial data
    fetchHealthProfile();
    fetchRecommendations();
    fetchCalendarEvents();
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_profile');
    apiService.clearToken();
    dispatch({ type: ActionTypes.RESET_STATE });
  };

  // Initialize data on authentication
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const userProfile = localStorage.getItem('user_profile');
    
    if (token && userProfile) {
      try {
        const user = JSON.parse(userProfile);
        apiService.setToken(token);
        dispatch({ type: ActionTypes.SET_USER, payload: user });
        dispatch({ type: ActionTypes.SET_AUTHENTICATED, payload: true });
        
        // Fetch initial data
        fetchHealthProfile();
        fetchRecommendations();
        fetchCalendarEvents();
      } catch (error) {
        console.error('Error parsing user profile:', error);
        logout();
      }
    }
  }, []);

  const value = {
    // State
    ...state,
    
    // Actions
    login,
    logout,
    processPrescription,
    fetchHealthProfile,
    fetchRecommendations,
    fetchCalendarEvents,
    createMedicationReminder,
    setLoading,
    setError,
    clearError,
    
    // Dispatch for custom actions
    dispatch
  };

  return (
    <HealthContext.Provider value={value}>
      {children}
    </HealthContext.Provider>
  );
};

// Hook to use the context
export const useHealth = () => {
  const context = useContext(HealthContext);
  if (!context) {
    throw new Error('useHealth must be used within a HealthProvider');
  }
  return context;
};

export default HealthContext;