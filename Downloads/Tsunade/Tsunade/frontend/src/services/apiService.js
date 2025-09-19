// Unified API service for all health management features
class ApiService {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    this.token = null;
  }

  // Initialize with token
  setToken(token) {
    this.token = token;
  }

  // Get authorization headers
  getHeaders(contentType = 'application/json') {
    const headers = {
      'Content-Type': contentType
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  }

  // Generic request method
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: this.getHeaders(options.contentType),
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Authentication APIs
  async login(credentials) {
    return this.request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
  }

  async register(userData) {
    return this.request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  // Health Profile APIs
  async getHealthProfile() {
    return this.request('/api/v1/medical-profile');
  }

  async updateHealthProfile(profileData) {
    return this.request('/api/v1/medical-profile', {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
  }

  // Prescription APIs
  async uploadPrescription(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.request('/api/v1/ocr', {
      method: 'POST',
      body: formData,
      contentType: undefined // Let browser set multipart boundary
    });
  }

  async analyzePrescription(prescriptionText) {
    return this.request('/api/v1/analyze-prescription', {
      method: 'POST',
      body: JSON.stringify({ prescription_text: prescriptionText })
    });
  }

  // Health Recommendations APIs
  async getPersonalizedRecommendations() {
    return this.request('/api/v1/health-insights/personalized-recommendations');
  }

  async getDiseaseRecommendations(disease, severity = 'moderate', userContext = {}) {
    return this.request('/api/v1/health-insights/disease-recommendations', {
      method: 'POST',
      body: JSON.stringify({
        disease,
        severity,
        user_context: userContext
      })
    });
  }

  // Calendar APIs
  async getCalendarEvents() {
    return this.request('/api/calendar/events');
  }

  async createCalendarEvent(eventData) {
    return this.request('/api/calendar/create-event', {
      method: 'POST',
      body: JSON.stringify(eventData)
    });
  }

  async updateCalendarEvent(eventId, eventData) {
    return this.request(`/api/calendar/events/${eventId}`, {
      method: 'PUT',
      body: JSON.stringify(eventData)
    });
  }

  async deleteCalendarEvent(eventId) {
    return this.request(`/api/calendar/events/${eventId}`, {
      method: 'DELETE'
    });
  }

  // Google Calendar Integration
  async getGoogleCalendarAuthUrl() {
    return this.request('/api/v1/calendar/auth-url');
  }

  async handleGoogleCalendarCallback(code) {
    return this.request('/api/v1/calendar/callback', {
      method: 'POST',
      body: JSON.stringify({ code })
    });
  }

  async createGoogleCalendarEvent(eventData) {
    return this.request('/api/v1/calendar/create-exercise-event', {
      method: 'POST',
      body: JSON.stringify(eventData)
    });
  }

  // Chat APIs
  async sendChatMessage(message, context = {}) {
    return this.request('/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        context
      })
    });
  }

  // Utility methods
  async healthCheck() {
    return this.request('/api/v1/health');
  }

  // Batch operations for efficiency
  async batchRequest(requests) {
    const promises = requests.map(({ endpoint, options }) => 
      this.request(endpoint, options).catch(error => ({ error: error.message }))
    );
    
    return Promise.all(promises);
  }

  // Initialize service with stored token
  init() {
    const token = localStorage.getItem('access_token');
    if (token) {
      this.setToken(token);
    }
  }

  // Clear token on logout
  clearToken() {
    this.token = null;
  }
}

// Create singleton instance
const apiService = new ApiService();

// Initialize on import
apiService.init();

export default apiService;

// Named exports for specific API groups
export const authAPI = {
  login: (credentials) => apiService.login(credentials),
  register: (userData) => apiService.register(userData)
};

export const healthAPI = {
  getProfile: () => apiService.getHealthProfile(),
  updateProfile: (data) => apiService.updateHealthProfile(data),
  getRecommendations: () => apiService.getPersonalizedRecommendations(),
  getDiseaseRecommendations: (disease, severity, context) => 
    apiService.getDiseaseRecommendations(disease, severity, context),
  getDayWiseDietChart: (data) => apiService.request('/api/v1/health-insights/day-wise-diet-chart', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  getDiseaseBasedExercisePlan: (data) => apiService.request('/api/v1/exercise-recommendations/disease-based-exercise-plan', {
    method: 'POST',
    body: JSON.stringify(data)
  })
};

export const prescriptionAPI = {
  upload: (file) => apiService.uploadPrescription(file),
  analyze: (text) => apiService.analyzePrescription(text),
  extractText: (formData) => apiService.request('/api/v1/ocr', {
    method: 'POST',
    body: formData,
    contentType: undefined
  }),
  analyzePrescription: (data) => apiService.request('/api/v1/analyze-prescription', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  uploadPrescription: (data) => apiService.request('/api/v1/prescription-integration/upload', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  getDashboardData: (userId) => apiService.request(`/api/v1/prescription-integration/dashboard/${userId}`),
  getPrescriptionHistory: (userId) => apiService.request(`/api/v1/prescription-integration/prescriptions/${userId}`),
  getRecommendationHistory: (userId) => apiService.request(`/api/v1/prescription-integration/recommendations/${userId}`),
  updateRecommendation: (recommendationId, data) => apiService.request(`/api/v1/prescription-integration/recommendations/${recommendationId}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  getSyncStatus: (userId) => apiService.request(`/api/v1/prescription-integration/sync-status/${userId}`),
  resyncPrescription: (prescriptionId) => apiService.request(`/api/v1/prescription-integration/resync/${prescriptionId}`, {
    method: 'POST'
  }),
  getHealthRecommendations: (data) => apiService.request('/api/v1/health-recommendations', {
    method: 'POST',
    body: JSON.stringify(data)
  })
};

export const calendarAPI = {
  getEvents: () => apiService.getCalendarEvents(),
  createEvent: (data) => apiService.createCalendarEvent(data),
  updateEvent: (id, data) => apiService.updateCalendarEvent(id, data),
  deleteEvent: (id) => apiService.deleteCalendarEvent(id),
  getGoogleAuthUrl: () => apiService.getGoogleCalendarAuthUrl(),
  handleGoogleCallback: (code) => apiService.handleGoogleCalendarCallback(code),
  createGoogleEvent: (data) => apiService.createGoogleCalendarEvent(data)
};

export const chatAPI = {
  sendMessage: (message, context) => apiService.sendChatMessage(message, context)
};