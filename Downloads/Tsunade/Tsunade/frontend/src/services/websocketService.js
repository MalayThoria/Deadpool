class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000;
    this.listeners = new Map();
    this.isConnected = false;
    this.token = null;
  }

  // Initialize WebSocket connection
  connect(token) {
    this.token = token;
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `ws://localhost:8000/ws/prescription-sync?token=${token}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnected = false;
          
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  // Handle incoming WebSocket messages
  handleMessage(data) {
    const { type, payload } = data;
    
    // Emit to specific listeners
    if (this.listeners.has(type)) {
      this.listeners.get(type).forEach(callback => {
        try {
          callback(payload);
        } catch (error) {
          console.error(`Error in ${type} listener:`, error);
        }
      });
    }

    // Emit to general listeners
    if (this.listeners.has('message')) {
      this.listeners.get('message').forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in message listener:', error);
        }
      });
    }
  }

  // Subscribe to specific message types
  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType).add(callback);

    // Return unsubscribe function
    return () => {
      if (this.listeners.has(eventType)) {
        this.listeners.get(eventType).delete(callback);
      }
    };
  }

  // Remove all listeners for an event type
  off(eventType) {
    this.listeners.delete(eventType);
  }

  // Send message to server
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }

  // Schedule reconnection
  scheduleReconnect() {
    this.reconnectAttempts++;
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
    
    setTimeout(() => {
      if (this.token) {
        this.connect(this.token).catch(error => {
          console.error('Reconnection failed:', error);
        });
      }
    }, this.reconnectInterval * this.reconnectAttempts);
  }

  // Disconnect WebSocket
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.isConnected = false;
    this.listeners.clear();
  }

  // Get connection status
  getStatus() {
    return {
      connected: this.isConnected,
      readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED,
      reconnectAttempts: this.reconnectAttempts
    };
  }
}

// Prescription-specific WebSocket handlers
class PrescriptionWebSocketManager {
  constructor() {
    this.wsService = new WebSocketService();
    this.dashboardUpdateCallbacks = new Set();
    this.prescriptionUploadCallbacks = new Set();
    this.recommendationCallbacks = new Set();
    this.syncStatusCallbacks = new Set();
  }

  // Initialize connection with authentication
  async initialize(token) {
    try {
      await this.wsService.connect(token);
      this.setupEventHandlers();
      return true;
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      return false;
    }
  }

  // Setup event handlers for prescription-related events
  setupEventHandlers() {
    // Handle prescription upload notifications
    this.wsService.on('prescription_uploaded', (data) => {
      console.log('Prescription uploaded:', data);
      this.dashboardUpdateCallbacks.forEach(callback => callback({
        type: 'prescription_uploaded',
        data
      }));
    });

    // Handle dashboard update notifications
    this.wsService.on('dashboard_updated', (data) => {
      console.log('Dashboard updated:', data);
      this.dashboardUpdateCallbacks.forEach(callback => callback({
        type: 'dashboard_updated',
        data
      }));
    });

    // Handle new recommendation notifications
    this.wsService.on('recommendation_added', (data) => {
      console.log('New recommendation:', data);
      this.recommendationCallbacks.forEach(callback => callback(data));
    });

    // Handle sync status updates
    this.wsService.on('sync_status', (data) => {
      console.log('Sync status:', data);
      this.syncStatusCallbacks.forEach(callback => callback(data));
    });

    // Handle medication reminders
    this.wsService.on('medication_reminder', (data) => {
      console.log('Medication reminder:', data);
      // Show notification or update UI
      this.showMedicationReminder(data);
    });
  }

  // Subscribe to dashboard updates
  onDashboardUpdate(callback) {
    this.dashboardUpdateCallbacks.add(callback);
    return () => this.dashboardUpdateCallbacks.delete(callback);
  }

  // Subscribe to prescription uploads
  onPrescriptionUpload(callback) {
    this.prescriptionUploadCallbacks.add(callback);
    return () => this.prescriptionUploadCallbacks.delete(callback);
  }

  // Subscribe to new recommendations
  onNewRecommendation(callback) {
    this.recommendationCallbacks.add(callback);
    return () => this.recommendationCallbacks.delete(callback);
  }

  // Subscribe to sync status updates
  onSyncStatus(callback) {
    this.syncStatusCallbacks.add(callback);
    return () => this.syncStatusCallbacks.delete(callback);
  }

  // Show medication reminder notification
  showMedicationReminder(data) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(`Medication Reminder: ${data.medication}`, {
        body: data.message,
        icon: '/medication-icon.png',
        tag: `medication-${data.medication_id}`
      });
    }
  }

  // Request notification permissions
  async requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return Notification.permission === 'granted';
  }

  // Send heartbeat to keep connection alive
  sendHeartbeat() {
    this.wsService.send({
      type: 'heartbeat',
      timestamp: new Date().toISOString()
    });
  }

  // Get connection status
  getConnectionStatus() {
    return this.wsService.getStatus();
  }

  // Disconnect
  disconnect() {
    this.wsService.disconnect();
    this.dashboardUpdateCallbacks.clear();
    this.prescriptionUploadCallbacks.clear();
    this.recommendationCallbacks.clear();
    this.syncStatusCallbacks.clear();
  }
}

// Create singleton instance
const prescriptionWebSocket = new PrescriptionWebSocketManager();

export default prescriptionWebSocket;
export { WebSocketService, PrescriptionWebSocketManager };