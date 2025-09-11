import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Pill, Info, AlertTriangle, Clock, ChevronDown, ChevronUp, CheckCircle, Shield } from 'lucide-react';

const MedicineCard = ({ medicine, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getCategoryColor = (category) => {
    const colors = {
      'antibiotic': 'from-blue-500 to-blue-600',
      'pain reliever': 'from-red-500 to-red-600',
      'anti-inflammatory': 'from-orange-500 to-orange-600',
      'antihistamine': 'from-purple-500 to-purple-600',
      'antacid': 'from-green-500 to-green-600',
      'vitamin': 'from-yellow-500 to-yellow-600',
      'supplement': 'from-indigo-500 to-indigo-600',
      'general medication': 'from-gray-500 to-gray-600'
    };
    return colors[category?.toLowerCase()] || 'from-gray-500 to-gray-600';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="medicine-card"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 bg-gradient-to-r ${getCategoryColor(medicine.category)} rounded-xl flex items-center justify-center`}>
            <Pill className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                {medicine.name}
              </h3>
              {medicine.verified && (
                <div className="flex items-center space-x-1">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                    Verified
                  </span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-2 mt-1">
              <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full bg-gradient-to-r ${getCategoryColor(medicine.category)} text-white`}>
                {medicine.category}
              </span>
              {medicine.verification_sources && medicine.verification_sources.length > 0 && (
                <div className="flex items-center space-x-1">
                  <Shield className="w-3 h-3 text-blue-500" />
                  <span className="text-xs text-blue-600 dark:text-blue-400">
                    {medicine.verification_sources.join(', ')}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <motion.button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          )}
        </motion.button>
      </div>

      {/* Description */}
      <div className="mb-4">
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          {medicine.description}
        </p>
      </div>

      {/* Dosage Info */}
      <div className="flex items-start space-x-3 mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
        <div>
          <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">
            Dosage Information
          </h4>
          <p className="text-sm text-blue-700 dark:text-blue-300">
            {medicine.dosage}
          </p>
        </div>
      </div>

      {/* Expanded Details */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-4"
          >
            {/* Precautions */}
            <div className="flex items-start space-x-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-1">
                  Precautions
                </h4>
                <p className="text-sm text-yellow-700 dark:text-yellow-300">
                  {medicine.precautions}
                </p>
              </div>
            </div>

            {/* Side Effects */}
            <div className="flex items-start space-x-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <Info className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-red-800 dark:text-red-200 mb-1">
                  Side Effects
                </h4>
                <p className="text-sm text-red-700 dark:text-red-300">
                  {medicine.side_effects}
                </p>
              </div>
            </div>

            {/* Interactions */}
            {medicine.interactions && (
              <div className="flex items-start space-x-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <Info className="w-5 h-5 text-purple-600 dark:text-purple-400 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-purple-800 dark:text-purple-200 mb-1">
                    Drug Interactions
                  </h4>
                  <p className="text-sm text-purple-700 dark:text-purple-300">
                    {medicine.interactions}
                  </p>
                </div>
              </div>
            )}

            {/* Pregnancy Safety */}
            {medicine.pregnancy_safety && (
              <div className="flex items-start space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <Info className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-green-800 dark:text-green-200 mb-1">
                    Pregnancy Safety
                  </h4>
                  <p className="text-sm text-green-700 dark:text-green-300">
                    {medicine.pregnancy_safety}
                  </p>
                </div>
              </div>
            )}

            {/* Storage */}
            {medicine.storage && (
              <div className="flex items-start space-x-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">
                    Storage Instructions
                  </h4>
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    {medicine.storage}
                  </p>
                </div>
              </div>
            )}

            {/* Missed Dose */}
            {medicine.missed_dose && (
              <div className="flex items-start space-x-3 p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                <Info className="w-5 h-5 text-orange-600 dark:text-orange-400 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-orange-800 dark:text-orange-200 mb-1">
                    Missed Dose
                  </h4>
                  <p className="text-sm text-orange-700 dark:text-orange-300">
                    {medicine.missed_dose}
                  </p>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Disclaimer */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          This information is for educational purposes only. Always consult with a healthcare professional before taking any medication.
        </p>
      </div>
    </motion.div>
  );
};

export default MedicineCard; 