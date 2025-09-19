import React, { useCallback, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { Upload, Camera, FileText, X, Image as ImageIcon } from 'lucide-react';

const UploadCard = ({ onFileUpload, isProcessing, onAnalyze, hasFile }) => {
  const [preview, setPreview] = useState(null);
  const [fileName, setFileName] = useState('');

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      setFileName(file.name);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
      
      // Call parent handler
      onFileUpload(file);
    }
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp'],
      'application/pdf': ['.pdf']
    },
    multiple: false
  });

  const clearFile = () => {
    setPreview(null);
    setFileName('');
  };

  const captureImage = () => {
    // This would integrate with device camera
    // For now, we'll just trigger file input
    document.querySelector('input[type="file"]')?.click();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
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

      {/* Upload Zone */}
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

      {/* Action Buttons */}
      <div className="flex space-x-3 mt-6">
        <motion.button
          onClick={captureImage}
          disabled={isProcessing}
          className="flex-1 btn-secondary flex items-center justify-center space-x-2"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Camera className="w-4 h-4" />
          <span>Capture</span>
        </motion.button>
        
        <motion.button
          onClick={() => document.querySelector('input[type="file"]')?.click()}
          disabled={isProcessing}
          className="flex-1 btn-primary flex items-center justify-center space-x-2"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <ImageIcon className="w-4 h-4" />
          <span>Browse</span>
        </motion.button>
      </div>

      {/* Analysis Button */}
      <div className="mt-3">
        <motion.button
          onClick={() => {
            if (hasFile && onAnalyze) {
              onAnalyze();
            } else {
              console.log('No file uploaded or analysis function not provided');
            }
          }}
          disabled={isProcessing || !hasFile}
          className={`w-full font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed ${
            hasFile && !isProcessing 
              ? 'bg-red-600 hover:bg-red-700 text-white' 
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
          whileHover={hasFile && !isProcessing ? { scale: 1.02 } : {}}
          whileTap={hasFile && !isProcessing ? { scale: 0.98 } : {}}
        >
          <span>{isProcessing ? 'Analyzing...' : 'Analysis'}</span>
        </motion.button>
      </div>

      {/* Processing State */}
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
              Processing your prescription...
            </span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default UploadCard;