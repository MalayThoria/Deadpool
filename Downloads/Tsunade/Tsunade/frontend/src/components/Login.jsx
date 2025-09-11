import React, { useState } from 'react';
import './Login.css';

const Login = ({ onLoginSuccess, onSwitchToRegister }) => {
  const [formData, setFormData] = useState({
    username: '', // FastAPI Users uses 'username' field for email
    password: ''
  });
  
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState('');
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [forgotPasswordLoading, setForgotPasswordLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [forgotPasswordSuccess, setForgotPasswordSuccess] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError(''); // Clear error when user types
  };

  const handleForgotPasswordEmailChange = (e) => {
    setForgotPasswordEmail(e.target.value);
    setError('');
  };

  const validateForm = () => {
    if (!formData.username || !formData.password) {
      setError('Please enter both email and password');
      return false;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.username)) {
      setError('Please enter a valid email address');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      // Create form data for FastAPI Users login
      const loginFormData = new FormData();
      loginFormData.append('username', formData.username);
      loginFormData.append('password', formData.password);
      
      const response = await fetch('/api/v1/auth/jwt/login', {
        method: 'POST',
        body: loginFormData
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Store the access token
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('tokenType', data.token_type);
        
        setSuccess('Login successful! Redirecting...');
        
        // Get user profile
        try {
          const profileResponse = await fetch('/api/v1/users/me', {
            headers: {
              'Authorization': `Bearer ${data.access_token}`,
              'Content-Type': 'application/json'
            }
          });
          
          if (profileResponse.ok) {
            const userProfile = await profileResponse.json();
            localStorage.setItem('userProfile', JSON.stringify(userProfile));
          }
        } catch (profileError) {
          console.log('Could not fetch user profile:', profileError);
        }
        
        // Call success callback if provided
        if (onLoginSuccess) {
          onLoginSuccess({
            token: data.access_token,
            tokenType: data.token_type
          });
        }
        
        // Reset form
        setFormData({
          username: '',
          password: ''
        });
        
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Invalid email or password');
      }
    } catch (err) {
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    
    if (!forgotPasswordEmail) {
      setError('Please enter your email address');
      return;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(forgotPasswordEmail)) {
      setError('Please enter a valid email address');
      return;
    }
    
    setForgotPasswordLoading(true);
    setError('');
    setForgotPasswordSuccess('');
    
    try {
      const response = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: forgotPasswordEmail
        })
      });
      
      if (response.ok) {
        setForgotPasswordSuccess('Password reset instructions have been sent to your email.');
        setForgotPasswordEmail('');
        
        // Auto-hide forgot password form after success
        setTimeout(() => {
          setShowForgotPassword(false);
          setForgotPasswordSuccess('');
        }, 3000);
        
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to send password reset email');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setForgotPasswordLoading(false);
    }
  };

  const toggleForgotPassword = () => {
    setShowForgotPassword(!showForgotPassword);
    setError('');
    setSuccess('');
    setForgotPasswordSuccess('');
    setForgotPasswordEmail('');
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h2>🏥 Welcome Back</h2>
          <p>Sign in to your health management account</p>
        </div>
        
        {!showForgotPassword ? (
          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="username">Email Address</label>
              <input
                type="email"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                placeholder="Enter your email address"
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Enter your password"
                required
              />
            </div>
            
            <div className="form-options">
              <button
                type="button"
                onClick={toggleForgotPassword}
                className="forgot-password-link"
              >
                Forgot your password?
              </button>
            </div>
            
            {error && (
              <div className="error-message">
                <p>❌ {error}</p>
              </div>
            )}
            
            {success && (
              <div className="success-message">
                <p>✅ {success}</p>
              </div>
            )}
            
            <button
              type="submit"
              disabled={loading}
              className="login-button"
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleForgotPassword} className="forgot-password-form">
            <div className="forgot-password-header">
              <h3>Reset Your Password</h3>
              <p>Enter your email address and we'll send you instructions to reset your password.</p>
            </div>
            
            <div className="form-group">
              <label htmlFor="forgotEmail">Email Address</label>
              <input
                type="email"
                id="forgotEmail"
                value={forgotPasswordEmail}
                onChange={handleForgotPasswordEmailChange}
                placeholder="Enter your email address"
                required
              />
            </div>
            
            {error && (
              <div className="error-message">
                <p>❌ {error}</p>
              </div>
            )}
            
            {forgotPasswordSuccess && (
              <div className="success-message">
                <p>✅ {forgotPasswordSuccess}</p>
              </div>
            )}
            
            <div className="forgot-password-actions">
              <button
                type="button"
                onClick={toggleForgotPassword}
                className="back-button"
              >
                Back to Sign In
              </button>
              
              <button
                type="submit"
                disabled={forgotPasswordLoading}
                className="reset-button"
              >
                {forgotPasswordLoading ? 'Sending...' : 'Send Reset Instructions'}
              </button>
            </div>
          </form>
        )}
        
        <div className="login-footer">
          <p>
            Don't have an account?{' '}
            <button
              type="button"
              onClick={onSwitchToRegister}
              className="register-link"
            >
              Create Account
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;