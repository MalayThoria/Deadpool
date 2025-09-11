import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Send, MessageCircle, Bot } from 'lucide-react';

const ChatInput = ({ onSendMessage, isProcessing }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isProcessing) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const suggestedQuestions = [
    "What are the side effects of this medicine?",
    "Can I take this with food?",
    "What should I avoid while taking this?",
    "How long should I take this medicine?",
    "Is this safe for pregnant women?",
    "What are the common interactions?"
  ];

  return (
    <div className="glass-card rounded-xl p-4">
      {/* Suggested Questions */}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-3">
          <Bot className="w-4 h-4 text-primary-600" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Ask me about your medicines:
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {suggestedQuestions.map((question, index) => (
            <motion.button
              key={index}
              onClick={() => onSendMessage(question)}
              disabled={isProcessing}
              className="px-3 py-1 text-xs bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full hover:bg-primary-200 dark:hover:bg-primary-800/50 transition-colors"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {question}
            </motion.button>
          ))}
        </div>
      </div>

      {/* Chat Input */}
      <form onSubmit={handleSubmit} className="flex space-x-3">
        <div className="flex-1 relative">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask about your medicines, side effects, interactions..."
            disabled={isProcessing}
            className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all"
          />
          <MessageCircle className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        </div>
        
        <motion.button
          type="submit"
          disabled={!message.trim() || isProcessing}
          className="px-6 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:from-primary-600 hover:to-primary-700 transition-all"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Send className="w-5 h-5" />
        </motion.button>
      </form>
    </div>
  );
};

export default ChatInput; 