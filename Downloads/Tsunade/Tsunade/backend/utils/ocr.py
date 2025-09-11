from PIL import Image
import pytesseract
import io
import base64
from typing import Optional

class OCRProcessor:
    def __init__(self):
        # Configure Tesseract path for different OS
        import os
        import sys
        
        # Set tessdata prefix if not already set
        if not os.environ.get('TESSDATA_PREFIX'):
            if sys.platform == 'linux':
                os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata/'
            else:
                os.environ['TESSDATA_PREFIX'] = 'C:\\Users\\Admin\\Downloads\\LP-Assistant\\LP-Assistant\\tessdata'
            
        # Check if Tesseract is installed
        self.tesseract_installed = False
        try:
            # For Windows, check common installation paths
            if sys.platform == 'win32':
                possible_paths = [
                    'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
                    'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe',
                    # Add the path if you know where Tesseract is installed
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        self.tesseract_installed = True
                        print(f"Found Tesseract at: {path}")
                        break
            # For macOS (if installed via Homebrew)
            elif sys.platform == 'darwin':
                if os.path.exists('/opt/homebrew/bin/tesseract'):
                    pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
                    self.tesseract_installed = True
            # For Linux/Ubuntu (Docker containers)
            else:
                possible_linux_paths = [
                    '/usr/bin/tesseract',
                    '/usr/local/bin/tesseract'
                ]
                for path in possible_linux_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        self.tesseract_installed = True
                        print(f"Found Tesseract at: {path}")
                        break
                    
            if not self.tesseract_installed:
                print("WARNING: Tesseract OCR is not installed or not found in common locations.")
                print("Please install Tesseract OCR and ensure it's in your PATH.")
                print("For Windows: https://github.com/UB-Mannheim/tesseract/wiki")
                print("For macOS: brew install tesseract")
                print("For Linux: apt-get install tesseract-ocr")
        except Exception as e:
            print(f"Error configuring Tesseract: {str(e)}")
            self.tesseract_installed = False
    
    def extract_text_from_image(self, image_data: bytes) -> str:
        """
        Extract text from image using Tesseract OCR
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Extracted text string
        """
        try:
            # Check if Tesseract is installed
            if not self.tesseract_installed:
                raise Exception("Tesseract OCR is not installed. Please install Tesseract to use OCR functionality.")
                
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Print debug info
            print(f"Image mode: {image.mode}, Size: {image.size}")
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image)
            
            # Check if text is None
            if text is None:
                text = ""
                
            # Clean up the text
            cleaned_text = self._clean_ocr_text(text)
            
            return cleaned_text
            
        except Exception as e:
            # Print detailed error
            import traceback
            print(f"OCR Error: {str(e)}")
            print(traceback.format_exc())
            raise Exception(f"OCR processing failed: {str(e)}")
    
    def _clean_ocr_text(self, text: str) -> str:
        """
        Clean and format OCR extracted text
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        # Handle None or empty text
        if text is None or not text:
            return ""
            
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
            # Check if base64_string is None
            if base64_string is None:
                print("Error: base64_string is None")
                return ""
                
            # Remove data URL prefix if present
            if isinstance(base64_string, str) and base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]
            
            # Decode base64 to bytes
            image_data = base64.b64decode(base64_string)
            
            return self.extract_text_from_image(image_data)
            
        except Exception as e:
            # Print detailed error
            import traceback
            print(f"Base64 Error: {str(e)}")
            print(traceback.format_exc())
            raise Exception(f"Base64 image processing failed: {str(e)}")

# Global OCR processor instance
ocr_processor = OCRProcessor()