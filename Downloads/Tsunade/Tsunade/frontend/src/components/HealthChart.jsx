import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Calendar, 
  Activity, 
  Utensils, 
  CheckCircle, 
  Circle, 
  ChevronLeft, 
  ChevronRight,
  Heart,
  Target,
  Clock,
  Info
} from 'lucide-react';

const HealthChart = ({ diseaseName, medicines = [] }) => {
  const [currentWeek, setCurrentWeek] = useState(0);
  const [completedTasks, setCompletedTasks] = useState(new Set());

  // Disease-specific health recommendations database
  const diseaseRecommendations = {
    diabetes: {
      dietary: [
        "Low glycemic index foods (quinoa, oats, legumes)",
        "Portion-controlled meals every 3-4 hours",
        "High fiber vegetables and lean proteins",
        "Limit refined sugars and processed foods",
        "Stay hydrated with 8-10 glasses of water",
        "Include cinnamon and turmeric in meals",
        "Choose whole grains over refined carbs"
      ],
      exercise: [
        "30-minute brisk walk after meals",
        "Resistance training 2-3 times per week",
        "Yoga or stretching for 15 minutes",
        "Swimming or low-impact cardio",
        "Monitor blood sugar before/after exercise",
        "Strength training with light weights",
        "Balance exercises to prevent falls"
      ],
      tips: [
        "Check blood glucose levels regularly",
        "Take medications as prescribed",
        "Maintain consistent meal timing",
        "Keep emergency glucose tablets handy"
      ]
    },
    hypertension: {
      dietary: [
        "DASH diet with low sodium (< 2300mg/day)",
        "Potassium-rich foods (bananas, spinach)",
        "Limit processed and packaged foods",
        "Increase fruits and vegetables intake",
        "Choose lean proteins and fish",
        "Reduce caffeine and alcohol consumption",
        "Include garlic and beetroot in diet"
      ],
      exercise: [
        "Moderate aerobic exercise 150 min/week",
        "Walking, cycling, or swimming",
        "Avoid heavy weightlifting initially",
        "Deep breathing exercises daily",
        "Tai Chi or gentle yoga",
        "Gradual increase in activity intensity",
        "Monitor heart rate during exercise"
      ],
      tips: [
        "Monitor blood pressure daily",
        "Manage stress through meditation",
        "Maintain healthy weight",
        "Limit salt intake strictly"
      ]
    },
    arthritis: {
      dietary: [
        "Anti-inflammatory foods (fatty fish, berries)",
        "Omega-3 rich foods (salmon, walnuts)",
        "Colorful fruits and vegetables",
        "Limit red meat and processed foods",
        "Include turmeric and ginger",
        "Stay hydrated for joint lubrication",
        "Maintain healthy weight to reduce joint stress"
      ],
      exercise: [
        "Low-impact exercises (swimming, cycling)",
        "Range of motion exercises daily",
        "Strength training with light resistance",
        "Water aerobics for joint relief",
        "Gentle stretching and flexibility work",
        "Avoid high-impact activities",
        "Heat/cold therapy as needed"
      ],
      tips: [
        "Take medications with food if needed",
        "Use joint protection techniques",
        "Apply heat before exercise, cold after",
        "Listen to your body and rest when needed"
      ]
    },
    default: {
      dietary: [
        "Balanced diet with variety of nutrients",
        "5-7 servings of fruits and vegetables",
        "Adequate protein from various sources",
        "Whole grains and healthy fats",
        "Stay well hydrated throughout day",
        "Limit processed and sugary foods",
        "Eat regular, portion-controlled meals"
      ],
      exercise: [
        "150 minutes moderate exercise per week",
        "Mix of cardio and strength training",
        "Daily stretching or flexibility work",
        "Find activities you enjoy",
        "Start slowly and progress gradually",
        "Include rest and recovery days",
        "Stay consistent with routine"
      ],
      tips: [
        "Take medications as prescribed",
        "Get adequate sleep (7-9 hours)",
        "Manage stress effectively",
        "Regular medical check-ups"
      ]
    }
  };

  // Get recommendations based on detected disease
  const getRecommendations = () => {
    const disease = diseaseName?.toLowerCase();
    if (disease?.includes('diabetes') || disease?.includes('metformin')) {
      return diseaseRecommendations.diabetes;
    } else if (disease?.includes('hypertension') || disease?.includes('blood pressure') || disease?.includes('amlodipine')) {
      return diseaseRecommendations.hypertension;
    } else if (disease?.includes('arthritis') || disease?.includes('joint') || disease?.includes('inflammation')) {
      return diseaseRecommendations.arthritis;
    }
    return diseaseRecommendations.default;
  };

  const recommendations = getRecommendations();
  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  
  const toggleTask = (taskId) => {
    const newCompleted = new Set(completedTasks);
    if (newCompleted.has(taskId)) {
      newCompleted.delete(taskId);
    } else {
      newCompleted.add(taskId);
    }
    setCompletedTasks(newCompleted);
  };

  const getProgressPercentage = () => {
    const totalTasks = 7 * (recommendations.dietary.length + recommendations.exercise.length);
    return Math.round((completedTasks.size / totalTasks) * 100);
  };

  const TaskItem = ({ task, taskId, icon: Icon, type }) => (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`flex items-start space-x-3 p-3 rounded-lg border transition-all cursor-pointer ${
        completedTasks.has(taskId)
          ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700'
          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600'
      }`}
      onClick={() => toggleTask(taskId)}
    >
      <div className="flex-shrink-0 mt-0.5">
        {completedTasks.has(taskId) ? (
          <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
        ) : (
          <Circle className="w-5 h-5 text-gray-400 dark:text-gray-500" />
        )}
      </div>
      <div className="flex-1">
        <div className="flex items-center space-x-2 mb-1">
          <Icon className={`w-4 h-4 ${type === 'diet' ? 'text-orange-500' : 'text-blue-500'}`} />
          <span className={`text-xs font-medium uppercase tracking-wide ${
            type === 'diet' ? 'text-orange-600 dark:text-orange-400' : 'text-blue-600 dark:text-blue-400'
          }`}>
            {type === 'diet' ? 'Dietary' : 'Exercise'}
          </span>
        </div>
        <p className={`text-sm ${
          completedTasks.has(taskId)
            ? 'text-green-700 dark:text-green-300 line-through'
            : 'text-gray-700 dark:text-gray-300'
        }`}>
          {task}
        </p>
      </div>
    </motion.div>
  );

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
            <Heart className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
              Daily Health Plan
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {diseaseName ? `Tailored for ${diseaseName}` : 'General Health Management'}
            </p>
          </div>
        </div>
        
        {/* Progress Circle */}
        <div className="relative w-16 h-16">
          <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 64 64">
            <circle
              cx="32"
              cy="32"
              r="28"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
              className="text-gray-200 dark:text-gray-700"
            />
            <circle
              cx="32"
              cy="32"
              r="28"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
              strokeDasharray={`${getProgressPercentage() * 1.76} 176`}
              className="text-blue-600 dark:text-blue-400"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              {getProgressPercentage()}%
            </span>
          </div>
        </div>
      </div>

      {/* Week Navigation */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => setCurrentWeek(Math.max(0, currentWeek - 1))}
          className="p-2 hover:bg-white dark:hover:bg-gray-800 rounded-lg transition-colors"
          disabled={currentWeek === 0}
        >
          <ChevronLeft className={`w-5 h-5 ${currentWeek === 0 ? 'text-gray-300' : 'text-gray-600 dark:text-gray-400'}`} />
        </button>
        
        <div className="flex items-center space-x-2">
          <Calendar className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <span className="font-medium text-gray-800 dark:text-gray-200">
            Week {currentWeek + 1}
          </span>
        </div>
        
        <button
          onClick={() => setCurrentWeek(currentWeek + 1)}
          className="p-2 hover:bg-white dark:hover:bg-gray-800 rounded-lg transition-colors"
        >
          <ChevronRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>
      </div>

      {/* Daily Schedule */}
      <div className="space-y-4">
        {daysOfWeek.map((day, dayIndex) => {
          const dayTasks = [
            ...recommendations.dietary.slice(0, 2).map((task, i) => ({
              task,
              id: `${currentWeek}-${dayIndex}-diet-${i}`,
              type: 'diet',
              icon: Utensils
            })),
            ...recommendations.exercise.slice(0, 2).map((task, i) => ({
              task,
              id: `${currentWeek}-${dayIndex}-exercise-${i}`,
              type: 'exercise',
              icon: Activity
            }))
          ];

          return (
            <motion.div
              key={`${currentWeek}-${day}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: dayIndex * 0.1 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">
                  {day}
                </h4>
                <div className="flex items-center space-x-2">
                  <Target className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {dayTasks.filter(t => completedTasks.has(t.id)).length}/{dayTasks.length} completed
                  </span>
                </div>
              </div>
              
              <div className="space-y-2">
                {dayTasks.map((taskItem) => (
                  <TaskItem
                    key={taskItem.id}
                    task={taskItem.task}
                    taskId={taskItem.id}
                    icon={taskItem.icon}
                    type={taskItem.type}
                  />
                ))}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Health Tips */}
      {recommendations.tips && (
        <div className="mt-6 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-3">
            <Info className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
            <h4 className="font-semibold text-yellow-800 dark:text-yellow-300">
              Important Health Tips
            </h4>
          </div>
          <ul className="space-y-1">
            {recommendations.tips.map((tip, index) => (
              <li key={index} className="text-sm text-yellow-700 dark:text-yellow-300 flex items-start space-x-2">
                <span className="text-yellow-500 mt-1">•</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Medicine Reminder */}
      {medicines && medicines.length > 0 && (
        <div className="mt-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Clock className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <h4 className="font-semibold text-purple-800 dark:text-purple-300">
              Medication Reminders
            </h4>
          </div>
          <div className="text-sm text-purple-700 dark:text-purple-300">
            Don't forget to take your prescribed medications: {medicines.slice(0, 3).map(m => m.name || m).join(', ')}
            {medicines.length > 3 && ` and ${medicines.length - 3} more`}
          </div>
        </div>
      )}
    </div>
  );
};

export default HealthChart;