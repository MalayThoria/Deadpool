import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, AlertCircle, Loader } from 'lucide-react';
import axios from 'axios';

const GoogleCalendarCallback = () => {
  const [status, setStatus] = useState('processing'); // 'processing', 'success', 'error'
  const [message, setMessage] = useState('Processing Google Calendar authorization...');

  useEffect(() => {
    const handleCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const error = urlParams.get('error');

      if (error) {
        console.error('OAuth error:', error);
        setStatus('error');
        setMessage('Authorization was denied or failed. Please try again.');
        
        // Close popup or redirect on error
        if (window.opener) {
          window.close();
        } else {
          setTimeout(() => {
            window.location.href = '/';
          }, 3000);
        }
        return;
      }

      if (code) {
        try {
          // Exchange code for tokens
          const response = await fetch('/api/v1/calendar/exchange-token', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              authorization_code: code,
              state: state
            }),
          });

          const data = await response.json();
          
          if (data.success) {
            // Store credentials in localStorage for the parent window to pick up
            localStorage.setItem('google_calendar_credentials', JSON.stringify(data.credentials));
            
            setStatus('success');
            setMessage('Google Calendar authorization successful!');
            
            // Close the popup window if this is running in a popup
            if (window.opener) {
              window.close();
            } else {
              // Redirect to main app if not in popup
              setTimeout(() => {
                window.location.href = '/';
              }, 2000);
            }
          } else {
            console.error('Failed to exchange token:', data);
            setStatus('error');
            setMessage('Failed to authorize Google Calendar. Please try again.');
          }
        } catch (err) {
          console.error('Error exchanging token:', err);
          setStatus('error');
          setMessage('An error occurred during authorization. Please try again.');
        }
      }
    };

    handleCallback();
  }, []);

  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-16 w-16 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-16 w-16 text-red-500" />;
      default:
        return <Loader className="h-16 w-16 text-blue-500 animate-spin" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-blue-600';
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <motion.div 
        className="text-center p-8 bg-white rounded-lg shadow-lg max-w-md mx-4"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <motion.div 
          className="mb-6"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
        >
          {getStatusIcon()}
        </motion.div>
        
        <motion.h2 
          className={`text-xl font-semibold mb-4 ${getStatusColor()}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          {status === 'processing' && 'Processing Authorization'}
          {status === 'success' && 'Authorization Successful'}
          {status === 'error' && 'Authorization Failed'}
        </motion.h2>
        
        <motion.p 
          className="text-gray-600 leading-relaxed"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          {message}
        </motion.p>
        
        {status === 'success' && (
          <motion.p 
            className="text-sm text-gray-500 mt-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            This window will close automatically...
          </motion.p>
        )}
        
        {status === 'error' && (
          <motion.p 
            className="text-sm text-gray-500 mt-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            Redirecting back to the app...
          </motion.p>
        )}
      </motion.div>
    </div>
  );
};

export default GoogleCalendarCallback;