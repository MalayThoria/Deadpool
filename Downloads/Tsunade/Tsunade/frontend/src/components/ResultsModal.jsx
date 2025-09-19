import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, FileText, Pill, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import HealthChart from './HealthChart';

const ResultsModal = ({ isOpen, onClose, results }) => {
  if (!isOpen || !results) return null;

  const { extractedText, medicines, medicineCorrections, fileName } = results;

  // Disease detection logic based on medicines and extracted text
  const detectDisease = () => {
    const allText = (extractedText || '').toLowerCase();
    const medicineNames = medicines?.map(m => (m.name || m.corrected || m).toLowerCase()).join(' ') || '';
    const combinedText = `${allText} ${medicineNames}`;

    // Common disease indicators
    if (combinedText.includes('metformin') || combinedText.includes('insulin') || 
        combinedText.includes('diabetes') || combinedText.includes('glucose') ||
        combinedText.includes('glipizide') || combinedText.includes('glyburide')) {
      return 'Diabetes';
    }
    
    if (combinedText.includes('amlodipine') || combinedText.includes('lisinopril') || 
        combinedText.includes('hypertension') || combinedText.includes('blood pressure') ||
        combinedText.includes('atenolol') || combinedText.includes('losartan')) {
      return 'Hypertension';
    }
    
    if (combinedText.includes('ibuprofen') || combinedText.includes('arthritis') || 
        combinedText.includes('joint') || combinedText.includes('inflammation') ||
        combinedText.includes('naproxen') || combinedText.includes('celecoxib')) {
      return 'Arthritis';
    }
    
    if (combinedText.includes('asthma') || combinedText.includes('inhaler') ||
        combinedText.includes('albuterol') || combinedText.includes('bronchodilator')) {
      return 'Asthma';
    }
    
    if (combinedText.includes('depression') || combinedText.includes('anxiety') ||
        combinedText.includes('sertraline') || combinedText.includes('fluoxetine')) {
      return 'Mental Health';
    }

    return null;
  };

  const detectedDisease = detectDisease();

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                  <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                    Analysis Complete
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {fileName && `File: ${fileName}`}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              <div className="space-y-6">
                
                {/* Medicines Found Section */}
                {medicines && medicines.length > 0 && (
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
                    <div className="flex items-center space-x-2 mb-3">
                      <Pill className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                      <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-300">
                        Medicines Identified ({medicines.length})
                      </h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {medicines.map((medicine, index) => (
                        <div
                          key={index}
                          className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-blue-200 dark:border-blue-700"
                        >
                          <div className="font-medium text-gray-800 dark:text-gray-200">
                            {medicine.name || medicine.corrected || medicine}
                          </div>
                          {medicine.dosage && (
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              Dosage: {medicine.dosage}
                            </div>
                          )}
                          {medicine.frequency && (
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              Frequency: {medicine.frequency}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Medicine Corrections Section */}
                {medicineCorrections && medicineCorrections.length > 0 && (
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-4">
                    <div className="flex items-center space-x-2 mb-3">
                      <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                      <h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-300">
                        Medicine Name Corrections
                      </h3>
                    </div>
                    <div className="space-y-2">
                      {medicineCorrections.map((correction, index) => (
                        <div
                          key={index}
                          className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-yellow-200 dark:border-yellow-700"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="text-sm text-gray-600 dark:text-gray-400">
                                Original: <span className="line-through">{correction.original}</span>
                              </div>
                              <div className="font-medium text-gray-800 dark:text-gray-200">
                                Corrected: {correction.corrected}
                              </div>
                            </div>
                            <div className="text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded">
                              Auto-corrected
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Extracted Text Section */}
                {extractedText && (
                  <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-4">
                    <div className="flex items-center space-x-2 mb-3">
                      <FileText className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-300">
                        Extracted Text ({extractedText.split(' ').length} words)
                      </h3>
                    </div>
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                      <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">
                        {extractedText}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Summary Stats */}
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl p-4">
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-300 mb-3">
                    Analysis Summary
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                        {medicines ? medicines.length : 0}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Medicines Found
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                        {extractedText ? extractedText.split(' ').length : 0}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Words Extracted
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                        {medicineCorrections ? medicineCorrections.length : 0}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Corrections Made
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                        <Clock className="w-6 h-6 mx-auto" />
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Just Completed
                      </div>
                    </div>
                  </div>
                </div>

                {/* Health Chart Section */}
                <HealthChart 
                  diseaseName={detectedDisease} 
                  medicines={medicines || []} 
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end p-6 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={onClose}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ResultsModal;