import openai
import os
from typing import List, Dict, Any
import json

class GPTProcessor:
    def __init__(self):
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = openai.OpenAI(api_key=api_key)
    
    def extract_medicines(self, prescription_text: str) -> List[str]:
        """
        Extract medicine names from prescription text using GPT-4
        
        Args:
            prescription_text: OCR extracted text from prescription
            
        Returns:
            List of medicine names
        """
        try:
            prompt = f"""
            Extract only the medicine names from this prescription text. 
            Return ONLY a JSON array of medicine names, nothing else.
            
            Prescription text:
            {prescription_text}
            
            Example output format:
            ["Medicine Name 1", "Medicine Name 2"]
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a medical assistant that extracts medicine names from prescriptions. Return only valid JSON arrays."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Extract and parse JSON response
            content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                medicines = json.loads(content)
                if isinstance(medicines, list):
                    return [med.strip() for med in medicines if med.strip()]
                else:
                    return []
            except json.JSONDecodeError:
                # Fallback: extract medicine names manually
                return self._fallback_medicine_extraction(content)
                
        except Exception as e:
            raise Exception(f"Medicine extraction failed: {str(e)}")
    
    def get_medicine_info(self, medicine_names: List[str]) -> List[Dict[str, Any]]:
        """
        Get detailed information about medicines using GPT-4 with cross-verification
        
        Args:
            medicine_names: List of medicine names
            
        Returns:
            List of medicine information dictionaries
        """
        try:
            medicines_str = ", ".join(medicine_names)
            
            prompt = f"""
            You are a certified healthcare assistant with access to medical databases. For the following medicines, provide detailed, accurate information in JSON format.
            
            Medicines: {medicines_str}
            
            For each medicine, provide comprehensive information:
            - name: Exact medicine name
            - description: What condition/disease it treats
            - dosage: Standard adult dosage with frequency
            - precautions: Important safety warnings and contraindications
            - side_effects: Common and serious side effects
            - category: Medicine category (antibiotic, pain reliever, etc.)
            - interactions: Common drug interactions
            - pregnancy_safety: Safety during pregnancy/breastfeeding
            - storage: How to store the medicine
            - missed_dose: What to do if a dose is missed
            
            IMPORTANT: 
            - Be extremely accurate and medical-appropriate
            - Include FDA-approved information when possible
            - Mention if information is limited and suggest consulting healthcare provider
            - Include both generic and brand names if applicable
            
            Return a JSON array of objects with these fields.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a certified healthcare assistant. Provide accurate, helpful medical information in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                medicine_info = json.loads(content)
                if isinstance(medicine_info, list):
                    return medicine_info
                else:
                    return []
            except json.JSONDecodeError:
                # Fallback: create basic info structure
                return self._create_fallback_medicine_info(medicine_names)
                
        except Exception as e:
            raise Exception(f"Medicine information retrieval failed: {str(e)}")
    
    def _fallback_medicine_extraction(self, text: str) -> List[str]:
        """
        Fallback method for medicine extraction if JSON parsing fails
        """
        # Simple keyword-based extraction
        medicine_keywords = [
            'tablet', 'capsule', 'pill', 'mg', 'ml', 'mg/ml', 'injection',
            'suspension', 'syrup', 'drops', 'cream', 'ointment', 'gel'
        ]
        
        words = text.split()
        medicines = []
        
        for i, word in enumerate(words):
            if any(keyword in word.lower() for keyword in medicine_keywords):
                # Try to get the medicine name (usually 1-3 words before the keyword)
                start = max(0, i-3)
                medicine_name = " ".join(words[start:i+1])
                medicines.append(medicine_name)
        
        return list(set(medicines))  # Remove duplicates
    
    def _create_fallback_medicine_info(self, medicine_names: List[str]) -> List[Dict[str, Any]]:
        """
        Create basic medicine information structure as fallback
        """
        info_list = []
        
        for medicine in medicine_names:
            info_list.append({
                "name": medicine,
                "description": "Medicine information not available",
                "dosage": "Consult your healthcare provider for dosage information",
                "precautions": "Always consult with a healthcare professional before taking any medication",
                "side_effects": "Side effects may vary. Consult your doctor for specific information.",
                "category": "General medication"
            })
        
        return info_list

    def verify_and_correct_medicine_names(self, extracted_medicines: List[str], prescription_context: str = "") -> Dict:
        """
        Use GPT-4 to verify and correct medicine names from OCR text
        
        Args:
            extracted_medicines: List of medicine names from OCR
            prescription_context: Original prescription text for context
            
        Returns:
            Dictionary with corrected medicines and verification details
        """
        try:
            medicines_str = ", ".join(extracted_medicines)
            
            prompt = f"""
            You are a medical expert specializing in prescription verification. I have extracted medicine names from a prescription using OCR, but some names may be misspelled or unclear due to poor handwriting or OCR errors.

            Extracted medicine names: {medicines_str}
            Prescription context: {prescription_context}

            Your task:
            1. **Verify and correct** each medicine name to its proper generic name
            2. **Identify** if any are not actual medicines (mark as invalid)
            3. **Provide confidence level** for each correction (0-100)
            4. **Explain** what you changed and why
            5. **Cross-verify** with common medical knowledge

            Return a JSON response with this structure:
            {{
                "corrected_medicines": [
                    {{
                        "original": "original_name",
                        "corrected": "corrected_name", 
                        "confidence": 95,
                        "method": "spelling_correction|brand_to_generic|context_inference|no_change|invalid_medicine",
                        "explanation": "Brief explanation of the correction",
                        "is_valid": true
                    }}
                ],
                "summary": "Overall summary of corrections made",
                "total_corrected": 3,
                "total_invalid": 0
            }}

            Be very careful and accurate. If you're unsure about a medicine name, mark confidence as low and explain why.
            Only return valid JSON.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a medical expert specializing in prescription verification and medicine name correction. Provide accurate, detailed responses in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # Fallback: return original medicines with low confidence
                fallback_result = {
                    "corrected_medicines": [
                        {
                            "original": med,
                            "corrected": med,
                            "confidence": 30,
                            "method": "no_correction",
                            "explanation": "Could not verify due to parsing error",
                            "is_valid": True
                        } for med in extracted_medicines
                    ],
                    "summary": "Could not verify medicines due to parsing error",
                    "total_corrected": 0,
                    "total_invalid": 0
                }
                return fallback_result
                
        except Exception as e:
            raise Exception(f"Medicine verification failed: {str(e)}")

# Global GPT processor instance
gpt_processor = GPTProcessor() 