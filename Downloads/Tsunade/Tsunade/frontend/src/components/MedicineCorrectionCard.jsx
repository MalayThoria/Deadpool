import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, AlertTriangle, Info, Shield, ArrowRight } from 'lucide-react';

const MedicineCorrectionCard = ({ medicineData }) => {
  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return 'text-green-600 dark:text-green-400';
    if (confidence >= 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getConfidenceText = (confidence) => {
    if (confidence >= 80) return 'High';
    if (confidence >= 60) return 'Medium';
    return 'Low';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-xl p-4 mb-4"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
          Medicine Verification
        </h3>
        {medicineData.is_valid && (
          <div className="flex items-center space-x-1">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-sm text-green-600 dark:text-green-400 font-medium">
              Valid Medicine
            </span>
          </div>
        )}
      </div>

      <div className="space-y-3">
        {/* Original vs Corrected */}
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">Original:</span>
          <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
            {medicineData.original}
          </span>
          <ArrowRight className="w-4 h-4 text-gray-400" />
          <span className="text-sm font-medium text-primary-600 dark:text-primary-400">
            {medicineData.corrected}
          </span>
        </div>

        {/* Correction Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="flex items-center space-x-2">
            <Info className="w-4 h-4 text-blue-500" />
            <span className="text-xs text-gray-600 dark:text-gray-400">Method:</span>
            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">
              {medicineData.method.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
            <span className="text-xs text-gray-600 dark:text-gray-400">Confidence:</span>
            <span className={`text-xs font-medium ${getConfidenceColor(medicineData.confidence)}`}>
              {getConfidenceText(medicineData.confidence)} ({medicineData.confidence.toFixed(0)}%)
            </span>
          </div>
        </div>

        {/* Explanation */}
        {medicineData.explanation && (
          <div className="flex items-start space-x-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <Info className="w-4 h-4 text-blue-500 mt-0.5" />
            <span className="text-xs text-blue-700 dark:text-blue-300">
              {medicineData.explanation}
            </span>
          </div>
        )}

        {/* Confidence Summary */}
        <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
          <span className="text-xs text-gray-700 dark:text-gray-300 font-medium">
            GPT-4 Verification Confidence
          </span>
          <span className={`text-xs font-bold ${getConfidenceColor(medicineData.confidence)}`}>
            {medicineData.confidence.toFixed(0)}%
          </span>
        </div>
      </div>
    </motion.div>
  );
};

export default MedicineCorrectionCard; 