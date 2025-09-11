import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster, toast } from 'react-hot-toast';
import axios from 'axios';
import { HealthProvider, useHealth } from './contexts/HealthContext';
import Header from './components/Header';
import ChatBox from './components/ChatBox';
import ChatInput from './components/ChatInput';
import UploadCard from './components/UploadCard';
import MedicineCard from './components/MedicineCard';
import HealthManagement from './components/HealthManagement';
import PrescriptionUpload from './components/PrescriptionUpload';
import UnifiedDashboard from './components/UnifiedDashboard';
import Login from './components/Login';
import Registration from './components/Registration';
import GoogleCalendarCallback from './components/GoogleCalendarCallback';
import { authAPI } from './services/apiService';
import { Bot, FileText, AlertCircle, AlertTriangle, Heart, User, LogOut, Upload, Activity } from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Main App component wrapped with HealthProvider
function AppContent() {
  const { user, isAuthenticated, login, logout } = useHealth();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [medicines, setMedicines] = useState([]);
  const [medicineCorrections, setMedicineCorrections] = useState([]);
  const [extractedText, setExtractedText] = useState('');
  const [isChatProcessing, setIsChatProcessing] = useState(false);
  
  // Authentication state
  const [currentView, setCurrentView] = useState('login'); // 'login', 'register', 'dashboard', 'chat'
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Check for existing authentication on app load
  useEffect(() => {
    // Check if this is a Google Calendar callback
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('code') && urlParams.has('state')) {
      setCurrentView('calendar-callback');
      return;
    }
    
    if (isAuthenticated) {
      setCurrentView('dashboard'); // Default to dashboard
    } else {
      setCurrentView('login');
    }
  }, [isAuthenticated]);

  // Dark mode effect
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  // Authentication handlers
  const handleLoginSuccess = (authData) => {
    login(authData);
    setCurrentView('dashboard');
    toast.success('Welcome back! Login successful.');
  };

  const handleRegistrationSuccess = (userData) => {
    toast.success('Registration successful! Please log in.');
    setCurrentView('login');
  };

  const handleLogout = () => {
    logout();
    setCurrentView('login');
    toast.success('Logged out successfully');
  };

  const switchToRegister = () => {
    setCurrentView('register');
  };

  const switchToLogin = () => {
    setCurrentView('login');
  };

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const addMessage = (sender, content) => {
    const newMessage = {
      sender,
      content,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const addChatMessage = addMessage;

  const processPrescription = async (file) => {
    setIsProcessing(true);
    setIsTyping(true);
    
    try {
      // Add user message
      addMessage('user', `Uploaded prescription: ${file.name}`);
      
      // Step 1: Extract text using OCR
      const formData = new FormData();
      formData.append('file', file);
      
      const ocrResponse = await axios.post(`${API_BASE_URL}/ocr`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (!ocrResponse.data.success) {
        throw new Error(ocrResponse.data.message);
      }
      
      const extractedText = ocrResponse.data.text;
      setExtractedText(extractedText);
      
      // Add AI message about OCR
      addMessage('ai', `I've extracted the text from your prescription. Found ${extractedText.split(' ').length} words.`);
      
      // Step 2: Extract medicine names
      const medsResponse = await axios.post(`${API_BASE_URL}/extract-meds`, {
        prescription_text: extractedText
      });
      
      if (!medsResponse.data.success) {
        throw new Error('Could not identify medicines in the prescription');
      }
      
      const medicineData = medsResponse.data.medicines;
      const medicineNames = medicineData.map(med => med.corrected);
      
      // Store correction data for display
      setMedicineCorrections(medicineData);
      
      // Add AI message about medicines found with corrections
      let medicineMessage = `I found ${medicineNames.length} medicine(s) in your prescription: ${medicineNames.join(', ')}`;
      
      if (medsResponse.data.correction_summary && medsResponse.data.correction_summary !== "All medicine names were accurate.") {
        medicineMessage += `\n\n${medsResponse.data.correction_summary}`;
      }
      
      addMessage('ai', medicineMessage);
      
      // Step 3: Get detailed medicine information
      const medInfoResponse = await axios.post(`${API_BASE_URL}/med-info`, {
        medicines: medicineNames
      });
      
      if (!medInfoResponse.data.success) {
        throw new Error('Could not retrieve medicine information');
      }
      
      const medicinesInfo = medInfoResponse.data.medicines_info;
      setMedicines(medicinesInfo);
      
      // Add final AI message
      addMessage('ai', `I've analyzed your prescription and prepared detailed information for each medicine. You can view the details below.`);
      
      toast.success('Prescription processed successfully!');
      
    } catch (error) {
      console.error('Error processing prescription:', error);
      addMessage('ai', `Sorry, I encountered an error while processing your prescription: ${error.message}. Please try again with a clearer image.`);
      toast.error('Failed to process prescription. Please try again.');
    } finally {
      setIsTyping(false);
      setIsProcessing(false);
    }
  };

  const handleFileUpload = (file) => {
    processPrescription(file);
  };

  const clearResults = () => {
    setMedicines([]);
    setMedicineCorrections([]);
    setExtractedText('');
    setMessages([]);
  };

  const handleChatMessage = async (message) => {
    setIsChatProcessing(true);
    setIsTyping(true);
    
    try {
      // Add user message
      addMessage('user', message);
      
      // Get context from current medicines
      const context = medicines.length > 0 
        ? `Current medicines: ${medicines.map(m => m.name).join(', ')}`
        : '';
      
      // Send to chat API
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message: message,
        context: context
      });
      
      if (response.data.success) {
        addMessage('ai', response.data.response);
      } else {
        addMessage('ai', 'Sorry, I encountered an error. Please try again.');
      }
      
    } catch (error) {
      console.error('Chat error:', error);
      addMessage('ai', 'Sorry, I encountered an error while processing your message. Please try again.');
    } finally {
      setIsTyping(false);
      setIsChatProcessing(false);
    }
  };

  // Render authentication screens
  if (!isAuthenticated) {
    return (
      <div className={`min-h-screen transition-colors duration-300 ${
        isDarkMode 
          ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900' 
          : 'bg-gradient-to-br from-blue-50 via-white to-purple-50'
      }`}>
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: isDarkMode ? '#374151' : '#ffffff',
              color: isDarkMode ? '#f3f4f6' : '#1f2937',
              border: `1px solid ${isDarkMode ? '#4b5563' : '#e5e7eb'}`,
            },
          }}
        />
        
        <Header isDarkMode={isDarkMode} onToggleDarkMode={toggleDarkMode} />
        
        <div className="container mx-auto px-4 py-8">
          {currentView === 'login' && (
            <Login 
              onLoginSuccess={handleLoginSuccess}
              onSwitchToRegister={switchToRegister}
            />
          )}
          
          {currentView === 'register' && (
            <Registration 
              onRegistrationSuccess={handleRegistrationSuccess}
              onSwitchToLogin={switchToLogin}
            />
          )}
        </div>
      </div>
    );
  }

  // Main authenticated application
  return (
      <div className={`min-h-screen transition-colors duration-300 ${
        isDarkMode 
          ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900' 
          : 'bg-gradient-to-br from-blue-50 via-white to-purple-50'
      }`}>
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: isDarkMode ? '#374151' : '#ffffff',
            color: isDarkMode ? '#f3f4f6' : '#1f2937',
            border: `1px solid ${isDarkMode ? '#4b5563' : '#e5e7eb'}`,
          },
        }}
      />
      
      {/* Navigation Header */}
      <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-700">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-bold text-gray-800 dark:text-gray-200">
                Health Management System
              </h1>
              
              {/* Navigation Tabs */}
              <nav className="flex space-x-1">
                <button
                  onClick={() => setCurrentView('dashboard')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    currentView === 'dashboard'
                      ? 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                  }`}
                >
                  <Heart className="w-4 h-4 inline mr-2" />
                  Health Dashboard
                </button>
                
                <button
                  onClick={() => setCurrentView('chat')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    currentView === 'chat'
                      ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                  }`}
                >
                  <Bot className="w-4 h-4 inline mr-2" />
                  Rx Assistant
                </button>
              </nav>
            </div>
            
            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleDarkMode}
                className="p-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                {isDarkMode ? '☀️' : '🌙'}
              </button>
              
              <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <User className="w-4 h-4" />
                <span>Welcome, {user?.first_name || 'User'}</span>
              </div>
              
              <button
                onClick={handleLogout}
                className="p-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {currentView === 'dashboard' && (
          <UnifiedDashboard 
            onProcessPrescription={processPrescription}
            extractedText={extractedText}
            medicines={medicines}
            onClearResults={clearResults}
            onAddChatMessage={addChatMessage}
          />
        )}
        
        {currentView === 'calendar-callback' && (
          <GoogleCalendarCallback />
        )}
        
        {currentView === 'chat' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
            {/* Chat Area - Left Side */}
            <div className="flex flex-col">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                className="glass-card rounded-2xl shadow-xl overflow-hidden h-[600px] flex flex-col"
              >
                {/* Chat Header */}
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                  <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                    Chat with Rx Assistant
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Ask questions about your medicines or upload a prescription
                  </p>
                </div>
                
                <ChatBox messages={messages} isTyping={isTyping} />
                
                {/* Chat Input */}
                <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                  <ChatInput onSendMessage={handleChatMessage} isProcessing={isChatProcessing} />
                </div>
              </motion.div>
            </div>
            
            {/* Upload & Results Area - Right Side */}
            <div className="space-y-6">
              {/* Upload Card */}
              <UploadCard 
                onFileUpload={handleFileUpload}
                isProcessing={isProcessing}
              />
              
              {/* Results Section */}
              <AnimatePresence>
                {(medicines.length > 0 || extractedText) && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.5 }}
                    className="space-y-4"
                  >
                    {/* Clear Results Button */}
                    <div className="flex justify-end">
                      <motion.button
                        onClick={clearResults}
                        className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        Clear Results
                      </motion.button>
                    </div>
                    
                    {/* Extracted Text (Optional) */}
                    {extractedText && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="glass-card rounded-xl p-4"
                      >
                        <div className="flex items-center space-x-2 mb-3">
                          <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                          <h3 className="text-sm font-medium text-gray-800 dark:text-gray-200">
                            Extracted Text
                          </h3>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                          {extractedText}
                        </p>
                      </motion.div>
                    )}
                    
                    {/* Medicine Corrections */}
                    {medicineCorrections.length > 0 && (
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2">
                          <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                            Medicine Verification
                          </h3>
                        </div>
                        
                        {medicineCorrections.map((medicine, index) => (
                          <div key={index} className="p-4 border rounded-lg bg-gray-50 dark:bg-gray-700">
                            <h4 className="font-medium text-gray-800 dark:text-gray-200">{medicine.name}</h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{medicine.dosage}</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{medicine.frequency}</p>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* Medicines List */}
                    {medicines.length > 0 && (
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2">
                          <Bot className="w-5 h-5 text-green-600 dark:text-green-400" />
                          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                            Medicine Analysis
                          </h3>
                        </div>
                        
                        <div className="space-y-4">
                          {medicines.map((medicine, index) => (
                            <MedicineCard 
                              key={index} 
                              medicine={medicine} 
                              index={index}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            
            {/* Welcome Message for Chat */}
            {messages.length === 0 && !isProcessing && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="col-span-2 text-center py-12"
              >
                <div className="max-w-md mx-auto">
                  <div className="w-20 h-20 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Bot className="w-10 h-10 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-4">
                    Welcome to Rx Assistant
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Upload a prescription image to get detailed information about your medications, including dosage, side effects, and precautions.
                  </p>
                  <div className="flex items-center justify-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
                    <AlertCircle className="w-4 h-4" />
                    <span>This is for educational purposes only. Always consult a healthcare professional.</span>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        )}
      </div>
      </div>
  );
}

// Wrapper component with HealthProvider
function App() {
  return (
    <HealthProvider>
      <AppContent />
    </HealthProvider>
  );
}

export default App;