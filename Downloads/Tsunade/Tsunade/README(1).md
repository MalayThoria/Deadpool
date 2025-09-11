# Rx Assistant - AI Healthcare Chatbot

A beautiful and functional full-stack healthcare chatbot web app that analyzes prescriptions using OCR and AI to provide detailed medicine information.

## 🚀 Features

### Frontend (React + TailwindCSS)
- **Modern UI**: Beautiful, responsive design with glassmorphism effects
- **Dark/Light Mode**: Toggle between themes with smooth animations
- **Drag & Drop Upload**: Easy prescription image upload with preview
- **Real-time Chat**: Interactive chat interface with typing indicators
- **Medicine Cards**: Detailed medicine information with expandable sections
- **Animations**: Smooth Framer Motion animations throughout the app

### Backend (FastAPI)
- **OCR Processing**: Extract text from prescription images using Tesseract
- **AI Medicine Extraction**: Use GPT-4 to identify medicine names
- **Medicine Information**: Get detailed dosage, side effects, and precautions
- **RESTful API**: Clean, documented API endpoints
- **Error Handling**: Comprehensive error handling and validation

## 🛠️ Tech Stack

### Frontend
- React 18
- TailwindCSS
- Framer Motion
- Lucide React Icons
- Axios
- React Dropzone
- React Hot Toast

### Backend
- FastAPI
- Python 3.8+
- Tesseract OCR
- OpenAI GPT-4
- Pydantic
- Uvicorn

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Tesseract OCR
- OpenAI API Key

### Backend Setup

1. **Install Tesseract OCR**:
   ```bash
   # macOS
   brew install tesseract
   
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # Windows
   # Download from https://github.com/UB-Mannheim/tesseract/wiki
   ```

2. **Clone and setup backend**:
   ```bash
   cd backend
   pip install -r ../requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```

4. **Run the backend**:
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Run the frontend**:
   ```bash
   npm start
   ```

The app will be available at `http://localhost:3000`

## 🔧 API Endpoints

### OCR Processing
- `POST /api/v1/ocr` - Extract text from uploaded image
- `POST /api/v1/ocr/base64` - Extract text from base64 image

### Medicine Extraction
- `POST /api/v1/extract-meds` - Extract medicine names from text
- `GET /api/v1/extract-meds/test` - Test endpoint

### Medicine Information
- `POST /api/v1/med-info` - Get detailed medicine information
- `GET /api/v1/med-info/{medicine_name}` - Get info for single medicine
- `GET /api/v1/med-info/test` - Test endpoint

## 🎯 Usage

1. **Upload Prescription**: Drag and drop or click to upload a prescription image
2. **OCR Processing**: The app extracts text from the image
3. **Medicine Detection**: AI identifies medicine names from the text
4. **Information Retrieval**: Get detailed information about each medicine
5. **View Results**: See dosage, side effects, and precautions in beautiful cards

## 🎨 Design Features

- **Glassmorphism**: Modern glass-like UI elements
- **Gradient Backgrounds**: Soft, professional color schemes
- **Smooth Animations**: Framer Motion powered transitions
- **Responsive Design**: Works on all device sizes
- **Accessibility**: Proper contrast and keyboard navigation

## 🔒 Security & Privacy

- **No Data Storage**: App works statelessly, no data is stored
- **Secure API**: Environment variables for sensitive data
- **Input Validation**: Comprehensive validation on all inputs
- **Error Handling**: Graceful error handling and user feedback

## 🚀 Deployment

### Backend Deployment
```bash
# Using Docker
docker build -t rx-assistant-backend .
docker run -p 8000:8000 rx-assistant-backend

# Using Heroku
heroku create rx-assistant-backend
git push heroku main
```

### Frontend Deployment
```bash
# Build for production
npm run build

# Deploy to Vercel/Netlify
# Upload the build folder
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This application is for educational purposes only. Always consult with a healthcare professional before taking any medication. The information provided should not be used as a substitute for professional medical advice.

## 🆘 Support

If you encounter any issues:
1. Check the console for error messages
2. Ensure all dependencies are installed
3. Verify your OpenAI API key is valid
4. Make sure Tesseract OCR is properly installed

## 🔮 Future Enhancements

- [ ] Voice input using Whisper API
- [ ] QR code generation for medicine purchase links
- [ ] PDF export functionality
- [ ] Google Calendar integration for dosage reminders
- [ ] Multi-language support
- [ ] Advanced OCR with Google Vision API
- [ ] Medicine interaction checker
- [ ] Dosage calculator 