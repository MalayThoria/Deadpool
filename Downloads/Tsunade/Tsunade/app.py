from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from PIL import Image
import io
import os
from werkzeug.utils import secure_filename
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure upload settings
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"message": "Rx Assistant API is running!", "status": "healthy"}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "tesseract_available": True}), 200

@app.route('/api/v1/health', methods=['GET'])
def api_health():
    return jsonify({"status": "healthy", "tesseract_available": True}), 200

@app.route('/api/v1/ocr', methods=['POST'])
def extract_text():
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400
        
        # Read image from memory
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract text using Tesseract
        extracted_text = pytesseract.image_to_string(image, lang='eng')
        
        # Clean up the extracted text
        cleaned_text = extracted_text.strip()
        
        if not cleaned_text:
            return jsonify({
                "error": "No text could be extracted from the image",
                "suggestion": "Please ensure the image is clear and contains readable text"
            }), 422
        
        return jsonify({
            "success": True,
            "extracted_text": cleaned_text,
            "message": "Text extracted successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to process image",
            "details": str(e)
        }), 500

@app.route('/api/v1/chat', methods=['POST'])
def chat_with_ai():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400
        
        user_message = data['message']
        extracted_text = data.get('extracted_text', '')
        
        # Create context for the AI based on extracted text
        if extracted_text:
            system_prompt = f"You are a helpful medical assistant. The user has uploaded a prescription with the following text: {extracted_text}. Please help them understand their medication, dosage, side effects, and answer any questions they have."
        else:
            system_prompt = "You are a helpful medical assistant. Please help the user with their health and medication questions."
        
        # Make request to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            "success": True,
            "response": ai_response,
            "message": "Chat response generated successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to generate chat response",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)