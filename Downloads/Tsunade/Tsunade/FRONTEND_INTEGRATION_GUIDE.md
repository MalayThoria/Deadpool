# Frontend Integration Guide for Railway Backend

## 🚀 Backend API Overview

**Production**: `https://deadpool-production.up.railway.app`  
**Local Development**: `http://localhost:8000`

### ✅ Endpoint Status (Verified)
- **Health Check**: `GET /health` ✅ **WORKING**
- **OCR Processing**: `POST /api/v1/ocr` ✅ **WORKING** (Tesseract integrated)
- **Medicine Extraction**: `POST /api/v1/extract-meds` ⚠️ **API QUOTA EXCEEDED**
- **Chat Assistant**: `POST /api/v1/chat` ⚠️ **API QUOTA EXCEEDED**
- **API Documentation**: `GET /docs` ❌ **DISABLED IN PRODUCTION**

### 🧪 Local Testing Results
- ✅ Backend server: Running on `localhost:8000`
- ✅ Frontend server: Running on `localhost:3000`
- ✅ OCR functionality: Fully operational with Tesseract
- ⚠️ ChatGPT features: Working but need valid OpenAI API key with quota

## 🔧 Frontend Configuration

### Environment Variables
Create a `.env.local` file in your frontend project:

```bash
# Railway Backend Configuration
NEXT_PUBLIC_API_BASE_URL=https://deadpool-production.up.railway.app
NEXT_PUBLIC_API_VERSION=v1

# Feature Flags
NEXT_PUBLIC_OCR_ENABLED=true
NEXT_PUBLIC_CHAT_ENABLED=true
NEXT_PUBLIC_MEDICINE_EXTRACTION_ENABLED=true
```

### API Client Configuration

#### React/Next.js Example

```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';

export const API_ENDPOINTS = {
  health: '/health',
  ocr: `/api/${API_VERSION}/ocr`,
  extractMeds: `/api/${API_VERSION}/extract-meds`,
  chat: `/api/${API_VERSION}/chat`,
} as const;

// API Client Class
export class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Health Check
  async checkHealth() {
    return this.request<{status: string, service: string}>(
      API_ENDPOINTS.health
    );
  }

  // OCR Processing
  async processImage(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseURL}${API_ENDPOINTS.ocr}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`OCR failed: ${response.status}`);
    }

    return await response.json();
  }

  // Medicine Extraction
  async extractMedicines(prescriptionText: string) {
    return this.request<{
      medicines: Array<{
        original: string;
        corrected: string;
        confidence: number;
        method: string;
        explanation: string;
        is_valid: boolean;
      }>;
      success: boolean;
      message: string;
      count: number;
    }>(API_ENDPOINTS.extractMeds, {
      method: 'POST',
      body: JSON.stringify({ prescription_text: prescriptionText }),
    });
  }

  // Chat with Assistant
  async chatWithAssistant(message: string, context?: string) {
    return this.request<{
      response: string;
      success: boolean;
      message: string;
    }>(API_ENDPOINTS.chat, {
      method: 'POST',
      body: JSON.stringify({ 
        message, 
        context: context || '' 
      }),
    });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
```

### React Hooks for API Integration

```typescript
// hooks/useApi.ts
import { useState, useCallback } from 'react';
import { apiClient } from '../lib/api';

// OCR Hook
export function useOCR() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processImage = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiClient.processImage(file);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'OCR processing failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { processImage, loading, error };
}

// Medicine Extraction Hook
export function useMedicineExtraction() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const extractMedicines = useCallback(async (text: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiClient.extractMedicines(text);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Medicine extraction failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { extractMedicines, loading, error };
}

// Chat Hook
export function useChat() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (message: string, context?: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiClient.chatWithAssistant(message, context);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Chat failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { sendMessage, loading, error };
}
```

### Component Examples

#### OCR Upload Component

```tsx
// components/OCRUpload.tsx
import React, { useState } from 'react';
import { useOCR } from '../hooks/useApi';

export function OCRUpload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [extractedText, setExtractedText] = useState<string>('');
  const { processImage, loading, error } = useOCR();

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      const result = await processImage(selectedFile);
      if (result.success) {
        setExtractedText(result.text);
      } else {
        console.error('OCR failed:', result.message);
      }
    } catch (err) {
      console.error('Upload failed:', err);
    }
  };

  return (
    <div className="ocr-upload">
      <h3>Upload Prescription Image</h3>
      
      <input
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        disabled={loading}
      />
      
      <button
        onClick={handleUpload}
        disabled={!selectedFile || loading}
      >
        {loading ? 'Processing...' : 'Extract Text'}
      </button>
      
      {error && (
        <div className="error">
          Error: {error}
        </div>
      )}
      
      {extractedText && (
        <div className="extracted-text">
          <h4>Extracted Text:</h4>
          <pre>{extractedText}</pre>
        </div>
      )}
    </div>
  );
}
```

#### Medicine Extraction Component

```tsx
// components/MedicineExtraction.tsx
import React, { useState } from 'react';
import { useMedicineExtraction } from '../hooks/useApi';

interface Props {
  prescriptionText: string;
}

export function MedicineExtraction({ prescriptionText }: Props) {
  const [medicines, setMedicines] = useState<any[]>([]);
  const { extractMedicines, loading, error } = useMedicineExtraction();

  const handleExtraction = async () => {
    if (!prescriptionText.trim()) return;

    try {
      const result = await extractMedicines(prescriptionText);
      if (result.success) {
        setMedicines(result.medicines);
      }
    } catch (err) {
      console.error('Medicine extraction failed:', err);
    }
  };

  return (
    <div className="medicine-extraction">
      <h3>Extract Medicines</h3>
      
      <button
        onClick={handleExtraction}
        disabled={!prescriptionText.trim() || loading}
      >
        {loading ? 'Extracting...' : 'Extract Medicines'}
      </button>
      
      {error && (
        <div className="error">
          Error: {error}
        </div>
      )}
      
      {medicines.length > 0 && (
        <div className="medicines-list">
          <h4>Found Medicines:</h4>
          <ul>
            {medicines.map((medicine, index) => (
              <li key={index}>
                <strong>{medicine.corrected}</strong>
                {medicine.original !== medicine.corrected && (
                  <span> (corrected from: {medicine.original})</span>
                )}
                <br />
                <small>Confidence: {(medicine.confidence * 100).toFixed(1)}%</small>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

## 🔒 CORS Configuration

The backend is configured to allow requests from common frontend domains. If you're deploying your frontend to a custom domain, make sure to:

1. **Update Railway Environment Variables**:
   ```bash
   ALLOWED_ORIGINS=https://your-frontend-domain.com,http://localhost:3000
   ```

2. **For Development**: The backend already allows `localhost:3000` and `127.0.0.1:3000`

## 🚀 Deployment Options

### Vercel Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Set environment variables
vercel env add NEXT_PUBLIC_API_BASE_URL
# Enter: https://deadpool-production.up.railway.app
```

### Netlify Deployment

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Build and deploy
npm run build
netlify deploy --prod --dir=dist

# Set environment variables in Netlify dashboard
```

## 🧪 Testing Integration

### Health Check Test

```typescript
// Test if backend is accessible
async function testBackendConnection() {
  try {
    const health = await apiClient.checkHealth();
    console.log('Backend status:', health.status);
    return true;
  } catch (error) {
    console.error('Backend connection failed:', error);
    return false;
  }
}
```

### Full Integration Test

```typescript
// Test complete OCR + Medicine Extraction flow
async function testFullFlow(imageFile: File) {
  try {
    // 1. Process image with OCR
    const ocrResult = await apiClient.processImage(imageFile);
    console.log('OCR Result:', ocrResult);
    
    if (ocrResult.success && ocrResult.text) {
      // 2. Extract medicines from text
      const medicineResult = await apiClient.extractMedicines(ocrResult.text);
      console.log('Medicine Extraction:', medicineResult);
      
      if (medicineResult.success && medicineResult.medicines.length > 0) {
        // 3. Chat about the first medicine
        const firstMedicine = medicineResult.medicines[0].corrected;
        const chatResult = await apiClient.chatWithAssistant(
          `Tell me about ${firstMedicine}`,
          `Patient has been prescribed: ${medicineResult.medicines.map(m => m.corrected).join(', ')}`
        );
        console.log('Chat Response:', chatResult);
      }
    }
  } catch (error) {
    console.error('Full flow test failed:', error);
  }
}
```

## 🔧 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check that your frontend domain is in `ALLOWED_ORIGINS`
   - Verify the backend URL is correct

2. **API Key Errors**
   - Medicine extraction and chat will fail until OpenAI API key is set
   - Set `OPENAI_API_KEY` in Railway environment variables

3. **File Upload Issues**
   - Ensure images are in supported formats (JPEG, PNG)
   - Check file size limits
   - Verify Content-Type headers

4. **Network Timeouts**
   - OCR processing can take 10-30 seconds for large images
   - Chat responses may take 5-15 seconds
   - Increase timeout values if needed

### Debug Mode

```typescript
// Enable debug logging
const apiClient = new ApiClient();
apiClient.debug = true; // Add this property to log all requests
```

## 📱 Mobile Considerations

- **Camera Integration**: Use `accept="image/*"` for camera access
- **File Size**: Compress images before upload for better performance
- **Offline Support**: Consider caching successful results
- **Progressive Enhancement**: Provide fallbacks for failed API calls

---

**Next Steps:**
1. Set up your frontend project with the provided configuration
2. Test the health endpoint first
3. Implement OCR upload functionality
4. Add OpenAI API key to Railway for full functionality
5. Deploy your frontend and update CORS settings