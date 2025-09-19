import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  Camera, 
  FileText, 
  X, 
  Image as ImageIcon, 
  Stethoscope, 
  Activity, 
  Calendar,
  Utensils,
  AlertCircle,
  CheckCircle,
  Clock,
  Brain,
  Dumbbell
} from 'lucide-react';
import { useHealth } from '../contexts/HealthContext';
import { prescriptionAPI, calendarAPI, healthAPI } from '../services/apiService';

const PrescriptionUpload = ({ onProcessPrescription, extractedText, medicines, onClearResults }) => {
  const { user, processPrescription } = useHealth();
  const [uploadedFile, setUploadedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [fileName, setFileName] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [ocrText, setOcrText] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [error, setError] = useState('');
  const [currentStep, setCurrentStep] = useState('upload'); // upload, ocr, analysis, recommendations
  const [showHealthAnalysis, setShowHealthAnalysis] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      setUploadedFile(file);
      setFileName(file.name);
      setError('');
      
      // Create preview
      const reader = new FileReader();
      reader.onload = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
      
      setCurrentStep('upload');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp'],
      'application/pdf': ['.pdf']
    },
    multiple: false
  });

  const clearFile = () => {
    setUploadedFile(null);
    setPreview(null);
    setFileName('');
    setOcrText('');
    setAnalysisResult(null);
    setRecommendations(null);
    setError('');
    setCurrentStep('upload');
  };

  const processOCR = async () => {
    if (!uploadedFile) {
      setError('Please upload a file first');
      return;
    }

    setIsProcessing(true);
    setError('');
    setCurrentStep('ocr');

    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);

      const response = await prescriptionAPI.extractText(formData);

      if (response.success) {
        setOcrText(response.text);
        setCurrentStep('analysis');
      } else {
        setError(response.message || 'Failed to extract text from image');
      }
    } catch (err) {
      setError('Error processing image: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleHealthAnalysisClick = async () => {
    if (!analysisResult) {
      setError('Please upload and analyze a prescription first');
      return;
    }
    
    setShowHealthAnalysis(true);
    setIsProcessing(true);
    setError('');

    try {
      // Get enhanced recommendations based on detected diseases
      const enhancedRecommendations = await getPersonalizedRecommendations(analysisResult);
      
      if (enhancedRecommendations) {
        setRecommendations(enhancedRecommendations);
        
        // Schedule health events in the background
        await scheduleHealthEvents(analysisResult);
        
        // Update health context
        await processPrescription({
          ...analysisResult,
          recommendations: enhancedRecommendations
        });
        
        setCurrentStep('recommendations');
      } else {
        setError('Unable to generate health recommendations. Please try again.');
      }
    } catch (err) {
      setError('Error generating health analysis: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleHealthAnalysis = async () => {
    if (!uploadedFile) {
      setError('Please upload a prescription first');
      return;
    }

    setIsProcessing(true);
    setError('');
    setCurrentStep('ocr');

    try {
      // First extract text from the prescription
      const formData = new FormData();
      formData.append('file', uploadedFile);

      const ocrResponse = await prescriptionAPI.extractText(formData);

      if (!ocrResponse.success) {
        setError(ocrResponse.message || 'Failed to extract text from prescription');
        return;
      }

      setOcrText(ocrResponse.text);
      setCurrentStep('analysis');

      // Perform comprehensive health analysis
      const analysisResponse = await prescriptionAPI.uploadPrescription({
        prescription_text: ocrResponse.text,
        image_reference: fileName,
        metadata: {
          upload_timestamp: new Date().toISOString(),
          file_type: uploadedFile?.type,
          file_size: uploadedFile?.size
        }
      });

      if (analysisResponse.success) {
        setAnalysisResult(analysisResponse.analysis);
        
        // Get enhanced personalized recommendations including diet and exercise
        const enhancedRecommendations = await getPersonalizedRecommendations(analysisResponse.analysis);
        
        if (enhancedRecommendations) {
          setRecommendations(enhancedRecommendations);
          
          // Schedule health events in calendar
          await scheduleHealthEvents(analysisResponse.analysis);
          
          setCurrentStep('recommendations');
        } else {
          setError('Failed to generate personalized recommendations');
        }
      } else {
        setError(analysisResponse.message || 'Failed to analyze prescription');
      }
    } catch (err) {
      setError('Error during health analysis: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const diagnoseDiseases = async () => {
    if (!ocrText) {
      setError('No text available for analysis');
      return;
    }

    setIsProcessing(true);
    setError('');

    try {
      // Use the new integrated prescription processing endpoint
      const response = await prescriptionAPI.uploadPrescription({
        prescription_text: ocrText,
        image_reference: fileName,
        metadata: {
          upload_timestamp: new Date().toISOString(),
          file_type: uploadedFile?.type,
          file_size: uploadedFile?.size
        }
      });

      if (response.success) {
        // The new endpoint handles everything: analysis, recommendations, and dashboard integration
        setAnalysisResult({
          prescription_id: response.prescription_id,
          integration_summary: response.integration_summary,
          recommendations_created: response.recommendations_created,
          dashboard_entries_created: response.dashboard_entries_created,
          conditions_detected: response.conditions_detected
        });
        
        const prescriptionData = {
          prescription_id: response.prescription_id,
          ocr_text: ocrText,
          timestamp: new Date().toISOString(),
          integration_status: 'completed'
        };
        
        // Use context to update local state
        await processPrescription(prescriptionData);
        
        if (onProcessPrescription) {
          onProcessPrescription(prescriptionData);
        }
        
        setCurrentStep('recommendations');
      } else {
        setError(response.message || 'Failed to process prescription');
      }
    } catch (err) {
      setError('Error processing prescription: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const getPersonalizedRecommendations = async (analysisResult) => {
    try {
      // Extract detected diseases from analysis result
      const detectedDiseases = analysisResult?.extracted_info?.conditions || 
                              analysisResult?.conditions_detected || 
                              [];
      
      if (detectedDiseases.length === 0) {
        console.warn('No diseases detected for recommendations');
        return null;
      }

      // Get comprehensive health recommendations including diet and exercise
      const [dietResponse, exerciseResponse] = await Promise.all([
        // Get day-wise diet chart
        healthAPI.getDayWiseDietChart({
          detected_diseases: detectedDiseases,
          user_preferences: {},
          duration_days: 7
        }),
        // Get disease-based exercise plan
        healthAPI.getDiseaseBasedExercisePlan({
          detected_diseases: detectedDiseases,
          user_preferences: {},
          fitness_level: "beginner",
          available_time: 30
        })
      ]);

      return {
        diseases: detectedDiseases,
        dietChart: dietResponse?.success ? dietResponse : null,
        exercisePlan: exerciseResponse?.success ? exerciseResponse : null,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('Error getting personalized recommendations:', error);
      return null;
    }
  };

  const scheduleHealthEvents = async (analysisData) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      // Create medication reminders
      if (analysisData?.extracted_info?.medications?.length > 0) {
        for (const medicine of analysisData.extracted_info.medications) {
          if (medicine.dosage && medicine.frequency) {
            await createMedicationReminder(medicine);
          }
        }
      }

      // Schedule follow-up appointments if conditions are detected
      if (analysisData?.extracted_info?.medical_conditions?.length > 0) {
        await scheduleFollowUpAppointment(analysisData.extracted_info.medical_conditions);
      }

    } catch (error) {
      console.error('Error scheduling health events:', error);
    }
  };

  const createMedicationReminder = async (medicine) => {
     try {
       const response = await calendarAPI.createEvent({
         title: `Take ${medicine.name}`,
         description: `Medication reminder: ${medicine.name} - ${medicine.dosage}\nFrequency: ${medicine.frequency}`,
         start_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
         duration_minutes: 15,
         recurrence: medicine.frequency && medicine.frequency.toLowerCase().includes('daily') ? 'daily' : null
       });
 
       if (response.success) {
         console.log(`Medication reminder created for ${medicine.name}:`, response.data);
       }
     } catch (error) {
       console.error('Error creating medication reminder:', error);
     }
   };

  const scheduleFollowUpAppointment = async (conditions) => {
     try {
       const response = await calendarAPI.createEvent({
         title: 'Follow-up Medical Appointment',
         description: `Follow-up appointment for: ${conditions.join(', ')}\nScheduled based on prescription analysis`,
         start_time: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
         duration_minutes: 60
       });
 
       if (response.success) {
         console.log('Follow-up appointment scheduled:', response.data);
       }
     } catch (error) {
       console.error('Error scheduling follow-up appointment:', error);
     }
   };

  const [calendarIntegration, setCalendarIntegration] = useState({
    authorized: false,
    loading: false,
    events: [],
    credentials: null
  });

  // Google Calendar Integration
  const handleGoogleCalendarAuth = async () => {
    setCalendarIntegration(prev => ({ ...prev, loading: true }));

    try {
      const response = await calendarAPI.getAuthUrl({ state: 'prescription_analysis' });

      if (response.success) {
        // Open Google OAuth in a new window
        const authWindow = window.open(
          response.authorization_url, 
          'google-auth', 
          'width=500,height=600,scrollbars=yes,resizable=yes'
        );
        
        // Listen for the auth completion
        const checkClosed = setInterval(() => {
          if (authWindow.closed) {
            clearInterval(checkClosed);
            // Check if auth was successful by checking localStorage or making a status call
            const credentials = localStorage.getItem('google_calendar_credentials');
            if (credentials) {
              setCalendarIntegration(prev => ({ 
                ...prev, 
                authorized: true, 
                loading: false,
                credentials: JSON.parse(credentials)
              }));
              localStorage.removeItem('google_calendar_credentials');
            } else {
              setCalendarIntegration(prev => ({ ...prev, loading: false }));
            }
          }
        }, 1000);
      }
    } catch (err) {
      console.error('Error with Google Calendar auth:', err);
      setCalendarIntegration(prev => ({ ...prev, loading: false }));
    }
  };

  const createCalendarEvents = async () => {
    if (!recommendations?.exercise_recommendations || !calendarIntegration.authorized || !calendarIntegration.credentials) return;

    setCalendarIntegration(prev => ({ ...prev, loading: true }));

    try {
      // Format exercise plan for the API
      const exercisePlan = {
        weekly_schedule: recommendations.exercise_recommendations.exercises?.map((exercise, index) => ({
          day: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][index % 7],
          exercises: [{
            name: exercise.name,
            duration: exercise.duration || '30 minutes',
            intensity: exercise.intensity || 'moderate',
            description: exercise.description || ''
          }]
        })) || []
      };

      const response = await calendarAPI.createExerciseEvents({
        credentials: calendarIntegration.credentials,
        exercise_plan: exercisePlan,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      });

      if (response.success) {
        setCalendarIntegration(prev => ({ 
          ...prev, 
          events: response.created_events,
          loading: false 
        }));
        alert(`Successfully created ${response.created_events.length} calendar events!`);
      } else {
        throw new Error('Failed to create calendar events');
      }
    } catch (err) {
      console.error('Error creating calendar events:', err);
      setCalendarIntegration(prev => ({ ...prev, loading: false }));
      alert('Failed to create calendar events. Please try again.');
    }
  };

  const scheduleToCalendar = async (type, item) => {
    try {
      const response = await calendarAPI.createEvent({
        title: `${type}: ${item.name || item.category}`,
        description: item.description || item.notes || '',
        start_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // Tomorrow
        duration_minutes: type === 'Exercise' ? 30 : 60
      });

      if (response.success) {
        alert(`${type} scheduled successfully!`);
      } else {
        alert(`Failed to schedule ${type}`);
      }
    } catch (err) {
      alert(`Error scheduling ${type}: ${err.message}`);
    }
  };

  const renderStepIndicator = () => {
    const steps = [
      { id: 'upload', label: 'Upload', icon: Upload },
      { id: 'ocr', label: 'Extract Text', icon: FileText },
      { id: 'analysis', label: 'Diagnose', icon: Stethoscope },
      { id: 'recommendations', label: 'Recommendations', icon: Activity }
    ];

    const stepIndex = steps.findIndex(step => step.id === currentStep);

    return (
      <div className="flex items-center justify-center mb-6">
        {steps.map((step, index) => {
          const Icon = step.icon;
          const isActive = index <= stepIndex;
          const isCurrent = step.id === currentStep;
          
          return (
            <React.Fragment key={step.id}>
              <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
                isActive ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-500'
              } ${isCurrent ? 'ring-2 ring-primary-300' : ''}`}>
                <Icon className="w-5 h-5" />
              </div>
              {index < steps.length - 1 && (
                <div className={`w-12 h-1 mx-2 ${
                  index < stepIndex ? 'bg-primary-500' : 'bg-gray-200'
                }`} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    );
  };

  const renderUploadSection = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-2xl p-6"
    >
      <div className="text-center mb-6">
        <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">
          Upload Prescription
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Drag & drop your prescription image or click to browse
        </p>
      </div>

      <div
        {...getRootProps()}
        className={`upload-zone ${isDragActive ? 'upload-zone-active' : ''} ${
          isProcessing ? 'pointer-events-none opacity-50' : ''
        }`}
      >
        <input {...getInputProps()} />
        
        <AnimatePresence mode="wait">
          {!preview ? (
            <motion.div
              key="upload-prompt"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <div className="flex justify-center">
                <div className="w-16 h-16 bg-gradient-to-r from-primary-100 to-secondary-100 dark:from-primary-900/20 dark:to-secondary-900/20 rounded-full flex items-center justify-center">
                  <Upload className="w-8 h-8 text-primary-600 dark:text-primary-400" />
                </div>
              </div>
              
              <div>
                <p className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-2">
                  {isDragActive ? 'Drop your file here' : 'Choose a file or drag it here'}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Supports JPG, PNG, GIF, BMP, and PDF files
                </p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="space-y-4"
            >
              <div className="relative">
                {fileName.toLowerCase().endsWith('.pdf') ? (
                  <div className="w-full h-32 bg-gradient-to-r from-red-100 to-red-200 dark:from-red-900/20 dark:to-red-800/20 rounded-lg flex items-center justify-center">
                    <FileText className="w-12 h-12 text-red-500" />
                  </div>
                ) : (
                  <img 
                    src={preview} 
                    alt="Preview" 
                    className="w-full h-32 object-cover rounded-lg"
                  />
                )}
                
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    clearFile();
                  }}
                  className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              
              <div className="text-center">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  {fileName}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Click to change file
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {preview && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-6">
          <motion.button
            onClick={processOCR}
            disabled={isProcessing}
            className="btn-primary flex items-center justify-center space-x-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <FileText className="w-4 h-4" />
            <span>{isProcessing ? 'Processing...' : 'Extract Text'}</span>
          </motion.button>
          
          <motion.button
            onClick={handleHealthAnalysisClick}
            disabled={!analysisResult || isProcessing}
            className={`flex items-center justify-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
              !analysisResult || isProcessing
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white hover:from-emerald-600 hover:to-teal-700 shadow-lg hover:shadow-xl'
            }`}
            whileHover={!analysisResult || isProcessing ? {} : { scale: 1.02 }}
            whileTap={!analysisResult || isProcessing ? {} : { scale: 0.98 }}
          >
            <Activity className="w-4 h-4" />
            <span>{isProcessing ? 'Analyzing...' : 'Health Analysis'}</span>
          </motion.button>
        </div>
      )}
    </motion.div>
  );

  const renderAnalysisSection = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-2xl p-6 mt-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 flex items-center">
          <Brain className="w-6 h-6 mr-2 text-primary-600" />
          AI Analysis
        </h3>
        {ocrText && (
          <motion.button
            onClick={diagnoseDiseases}
            disabled={isProcessing}
            className="btn-primary flex items-center space-x-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Stethoscope className="w-4 h-4" />
            <span>{isProcessing ? 'Diagnosing...' : 'Diagnose Disease'}</span>
          </motion.button>
        )}
      </div>

      {ocrText && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Extracted Text:</h4>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-sm text-gray-700 dark:text-gray-300 max-h-32 overflow-y-auto">
            {ocrText}
          </div>
        </div>
      )}

      {analysisResult && (
        <div className="space-y-4">
          <div className="flex items-center space-x-2 text-green-600">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">{analysisResult.message}</span>
          </div>

          {analysisResult?.extracted_info?.medical_conditions?.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Detected Conditions:</h4>
              <div className="flex flex-wrap gap-2">
                {analysisResult.extracted_info.medical_conditions.map((condition, index) => (
                  <span key={index} className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">
                    {condition}
                  </span>
                ))}
              </div>
            </div>
          )}

          {analysisResult?.extracted_info?.medications?.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Medications:</h4>
              <div className="space-y-2">
                {analysisResult.extracted_info.medications.map((med, index) => (
                  <div key={index} className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
                    <div className="font-medium text-blue-800 dark:text-blue-200">{med.name}</div>
                    {med.dosage && <div className="text-sm text-blue-600 dark:text-blue-300">Dosage: {med.dosage}</div>}
                    {med.frequency && <div className="text-sm text-blue-600 dark:text-blue-300">Frequency: {med.frequency}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );

  const renderRecommendations = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 mt-6"
    >
      {/* Diet Chart Section */}
      {recommendations?.dietChart && (
        <div className="glass-card rounded-2xl p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 flex items-center">
              <Utensils className="w-6 h-6 mr-2 text-orange-600" />
              7-Day Diet Chart
            </h3>
          </div>
          
          <div className="space-y-4">
            {recommendations.dietChart.diet_plan?.map((day, index) => (
              <div key={index} className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4">
                <h4 className="font-medium text-orange-800 dark:text-orange-200 mb-3">
                  Day {day.day} - {day.day_name}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                  {day.meals?.map((meal, mealIndex) => (
                    <div key={mealIndex} className="bg-white dark:bg-gray-800 rounded-lg p-3">
                      <h5 className="font-medium text-orange-700 dark:text-orange-300 capitalize mb-2">
                        {meal.meal_type}
                      </h5>
                      <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                        {meal.foods?.map((food, foodIndex) => (
                          <li key={foodIndex}>• {food}</li>
                        ))}
                      </ul>
                      <div className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                        {meal.calories} cal | {meal.preparation_time}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 text-sm text-orange-600 dark:text-orange-400">
                  <strong>Focus:</strong> {day.nutritional_focus} | <strong>Total:</strong> {day.total_calories} calories
                </div>
              </div>
            ))}
            
            {recommendations.dietChart.general_guidelines && (
              <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4">
                <h4 className="font-medium text-orange-800 dark:text-orange-200 mb-2">General Guidelines:</h4>
                <ul className="text-sm text-orange-700 dark:text-orange-300 space-y-1">
                  {recommendations.dietChart.general_guidelines.map((guideline, index) => (
                    <li key={index}>• {guideline}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Exercise Plan Section */}
      {recommendations?.exercisePlan && (
        <div className="glass-card rounded-2xl p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 flex items-center">
              <Activity className="w-6 h-6 mr-2 text-green-600" />
              Weekly Exercise Plan
            </h3>
            
            {/* Google Calendar Integration */}
            <div className="flex items-center space-x-2">
              {!calendarIntegration.authorized ? (
                <button
                  onClick={handleGoogleCalendarAuth}
                  disabled={calendarIntegration.loading}
                  className="btn-sm btn-primary flex items-center space-x-2"
                >
                  <Calendar className="w-4 h-4" />
                  <span>{calendarIntegration.loading ? 'Connecting...' : 'Connect Google Calendar'}</span>
                </button>
              ) : (
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-1 text-green-600">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-sm">Calendar Connected</span>
                  </div>
                  <button
                    onClick={createCalendarEvents}
                    disabled={calendarIntegration.loading}
                    className="btn-sm btn-secondary flex items-center space-x-1"
                  >
                    <Calendar className="w-4 h-4" />
                    <span>{calendarIntegration.loading ? 'Creating...' : 'Schedule All'}</span>
                  </button>
                </div>
              )}
            </div>
          </div>
          
          <div className="space-y-4">
            {recommendations.exercisePlan.weekly_plan?.map((week, weekIndex) => (
              <div key={weekIndex} className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                <h4 className="font-medium text-green-800 dark:text-green-200 mb-3">
                  Week {week.week_number}
                </h4>
                <div className="space-y-3">
                  {week.exercises?.map((exercise, exerciseIndex) => (
                    <div key={exerciseIndex} className="bg-white dark:bg-gray-800 rounded-lg p-3">
                      <div className="flex justify-between items-start mb-2">
                        <h5 className="font-medium text-green-700 dark:text-green-300">{exercise.name}</h5>
                        <button
                          onClick={() => scheduleToCalendar('Exercise', exercise)}
                          className="btn-sm btn-secondary flex items-center space-x-1"
                        >
                          <Calendar className="w-4 h-4" />
                          <span>Schedule</span>
                        </button>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm text-gray-600 dark:text-gray-400 mb-2">
                        <div><strong>Type:</strong> {exercise.type}</div>
                        <div><strong>Duration:</strong> {exercise.duration}</div>
                        <div><strong>Intensity:</strong> {exercise.intensity}</div>
                        <div><strong>Frequency:</strong> {exercise.frequency}</div>
                      </div>
                      <p className="text-sm text-green-600 dark:text-green-400 mb-2">{exercise.description}</p>
                      {exercise.benefits && (
                        <div className="text-sm text-green-700 dark:text-green-300 mb-2">
                          <strong>Benefits:</strong> {exercise.benefits.join(', ')}
                        </div>
                      )}
                      {exercise.precautions && (
                        <p className="text-sm text-orange-600 dark:text-orange-400">
                          <AlertCircle className="w-4 h-4 inline mr-1" />
                          <strong>Precautions:</strong> {exercise.precautions.join(', ')}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
            
            {recommendations.exercisePlan.general_guidelines && (
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                <h4 className="font-medium text-green-800 dark:text-green-200 mb-2">General Guidelines:</h4>
                <ul className="text-sm text-green-700 dark:text-green-300 space-y-1">
                  {recommendations.exercisePlan.general_guidelines.map((guideline, index) => (
                    <li key={index}>• {guideline}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {calendarIntegration.events.length > 0 && (
              <div className="mt-4">
                <h4 className="font-medium text-gray-800 dark:text-gray-200 mb-2">Scheduled Events:</h4>
                <div className="space-y-2">
                  {calendarIntegration.events.map((event, index) => (
                    <div key={index} className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                      <div className="font-medium text-green-800 dark:text-green-200">{event.exercise_name}</div>
                      <div className="text-sm text-green-600 dark:text-green-400">
                        {event.date} at {event.time}
                      </div>
                      {event.event_link && (
                        <a 
                          href={event.event_link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          View in Google Calendar
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {recommendations?.dietary_recommendations && (
        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 flex items-center mb-4">
            <Utensils className="w-6 h-6 mr-2 text-orange-600" />
            Dietary Recommendations
          </h3>
          <div className="space-y-4">
            {recommendations.dietary_recommendations.foods?.map((food, index) => (
              <div key={index} className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium text-orange-800 dark:text-orange-200">{food.category}</h4>
                  <button
                    onClick={() => scheduleToCalendar('Diet Plan', food)}
                    className="btn-sm btn-secondary flex items-center space-x-1"
                  >
                    <Calendar className="w-4 h-4" />
                    <span>Schedule</span>
                  </button>
                </div>
                {food.recommended && (
                  <p className="text-sm text-green-700 dark:text-green-300 mb-1">
                    <strong>Recommended:</strong> {food.recommended.join(', ')}
                  </p>
                )}
                {food.avoid && (
                  <p className="text-sm text-red-700 dark:text-red-300 mb-1">
                    <strong>Avoid:</strong> {food.avoid.join(', ')}
                  </p>
                )}
                {food.notes && (
                  <p className="text-sm text-orange-600 dark:text-orange-400">{food.notes}</p>
                )}
              </div>
            )) || (
              <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4">
                <p className="text-orange-700 dark:text-orange-300">{recommendations.dietary_recommendations}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-2">
          AI-Powered Prescription Analysis
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Upload your prescription for intelligent disease diagnosis and personalized health recommendations
        </p>
      </div>

      {renderStepIndicator()}
      
      {renderUploadSection()}
      
      {(ocrText || analysisResult) && renderAnalysisSection()}
      
      {/* Health Analysis Results - Compact Display */}
      {showHealthAnalysis && recommendations && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 space-y-6"
        >
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 flex items-center">
                <Activity className="w-6 h-6 mr-2 text-blue-600" />
                Health Analysis & Daily Schedule
              </h3>
              <button
                onClick={() => setShowHealthAnalysis(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {/* Detected Diseases */}
            {recommendations.diseases && recommendations.diseases.length > 0 && (
              <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-2">Detected Conditions:</h4>
                <div className="flex flex-wrap gap-2">
                  {recommendations.diseases.map((disease, index) => (
                    <span key={index} className="px-3 py-1 bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200 rounded-full text-sm">
                      {disease}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          {renderRecommendations()}
        </motion.div>
      )}

      {/* Original Recommendations Display */}
      {currentStep === 'recommendations' && !showHealthAnalysis && renderRecommendations()}

      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800"
        >
          <div className="flex items-center space-x-2 text-red-700 dark:text-red-300">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </motion.div>
      )}

      {isProcessing && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg"
        >
          <div className="flex items-center space-x-3">
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
            <span className="text-sm text-blue-700 dark:text-blue-300">
              {currentStep === 'ocr' ? 'Extracting text from prescription...' :
               currentStep === 'analysis' ? 'Analyzing medical conditions...' :
               'Processing your request...'}
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default PrescriptionUpload;