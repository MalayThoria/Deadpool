from PIL import Image
import pytesseract
import io
import base64
from typing import Optional

class OCRProcessor:
    def __init__(self):
        # Configure Tesseract path for different OS
        try:
            # For macOS (if installed via Homebrew)
            pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
        except:
            try:
                # For Linux/Ubuntu
                pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
            except:
                # For Windows or default
                pass
    
    def extract_text_from_image(self, image_data: bytes) -> str:
        """
        Extract text from image using Tesseract OCR
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Extracted text string
        """
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image)
            
            # Clean up the text
            cleaned_text = self._clean_ocr_text(text)
            
            return cleaned_text
            
        except Exception as e:
            raise Exception(f"OCR processing failed: {str(e)}")
    
    def _clean_ocr_text(self, text: str) -> str:
        """
        Clean and format OCR extracted text
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace and normalize
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove excessive whitespace
            cleaned_line = ' '.join(line.split())
            if cleaned_line.strip():
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    def extract_text_from_base64(self, base64_string: str) -> str:
        """
        Extract text from base64 encoded image
        
        Args:
            base64_string: Base64 encoded image string
            
        Returns:
            Extracted text string
        """
        try:
            # Remove data URL prefix if present
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]
            
            # Decode base64 to bytes
            image_data = base64.b64decode(base64_string)
            
            return self.extract_text_from_image(image_data)
            
        except Exception as e:
            raise Exception(f"Base64 image processing failed: {str(e)}")

# Global OCR processor instance
ocr_processor = OCRProcessor() 