import os
from typing import List, Dict, Any
import openai
import json

class GPTProcessor:
    def __init__(self):
        # Initialize OpenAI API
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI API with error handling
        try:
            self.client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def extract_medicines(self, prescription_text: str) -> List[str]:
        """
        Extract medicine names from prescription text using GPT-4
        
        Args:
            prescription_text: OCR extracted text from prescription
            
        Returns:
            List of medicine names
        """
        try:
            if self.client is None:
                raise Exception("OpenAI client not initialized")
            prompt = f"""
            Extract only the medicine names from this prescription text. 
            Return ONLY a JSON array of medicine names, nothing else.
            
            Prescription text:
            {prescription_text}
            
            Example output format:
            ["Medicine Name 1", "Medicine Name 2"]
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a medical assistant that extracts disease names from prescriptions. Return only valid JSON arrays."},
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
    
    def extract_diseases(self, prescription_text: str) -> List[str]:
        """
        Extract disease/condition names from prescription text using GPT-4
        
        Args:
            prescription_text: OCR extracted text from prescription
            
        Returns:
            List of disease/condition names
        """
        try:
            if self.client is None:
                raise Exception("OpenAI client not initialized")
                
            prompt = f"""
            Extract only the disease names, medical conditions, or diagnoses from this prescription text.
            Focus on identifying:
            - Primary diseases or conditions
            - Chronic conditions
            - Acute conditions
            - Symptoms that indicate specific conditions
            
            Return ONLY a JSON array of disease/condition names, nothing else.
            Example: ["Hypertension", "Diabetes Type 2", "Arthritis"]
            
            Prescription text:
            {prescription_text}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a medical expert that extracts disease information from prescriptions. Return only valid JSON arrays."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Extract and parse JSON response
            content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                diseases = json.loads(content)
                if isinstance(diseases, list):
                    return [disease.strip() for disease in diseases if disease.strip()]
                else:
                    return []
            except json.JSONDecodeError:
                # Fallback: extract from text
                lines = content.split('\n')
                diseases = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('-'):
                        # Remove common prefixes and clean up
                        import re
                        line = re.sub(r'^[\d\-\*\+\.\s]+', '', line)
                        line = re.sub(r'[\[\]"\']', '', line)
                        if line:
                            diseases.append(line)
                return diseases[:10]  # Limit to 10 diseases
                
        except Exception as e:
            print(f"Error extracting diseases: {e}")
            return []
    
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
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a medical information assistant. Provide accurate, helpful information about medicines."},
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
    
    def get_exercise_recommendations(self, diseases: List[str], user_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate personalized exercise recommendations based on diseases and user profile
        
        Args:
            diseases: List of identified diseases/conditions
            user_profile: Optional user profile with age, fitness level, preferences
            
        Returns:
            Dictionary containing exercise recommendations
        """
        try:
            if self.client is None:
                raise Exception("OpenAI client not initialized")
            
            # Default user profile if not provided
            if user_profile is None:
                user_profile = {
                    "age": "adult",
                    "fitness_level": "beginner",
                    "preferences": "general wellness"
                }
            
            diseases_text = ", ".join(diseases) if diseases else "general health maintenance"
            
            prompt = f"""
            Create personalized daily exercise recommendations for someone with the following conditions: {diseases_text}
            
            User Profile:
            - Age: {user_profile.get('age', 'adult')}
            - Fitness Level: {user_profile.get('fitness_level', 'beginner')}
            - Preferences: {user_profile.get('preferences', 'general wellness')}
            
            Provide recommendations in the following JSON format:
            {{
                "daily_exercises": [
                    {{
                        "name": "Exercise Name",
                        "duration": "10-15 minutes",
                        "description": "Brief description",
                        "benefits": "How it helps with the condition",
                        "precautions": "Any safety notes",
                        "time_of_day": "morning/afternoon/evening"
                    }}
                ],
                "weekly_plan": {{
                    "monday": ["Exercise 1", "Exercise 2"],
                    "tuesday": ["Exercise 1", "Exercise 3"],
                    "wednesday": ["Exercise 2", "Exercise 4"],
                    "thursday": ["Exercise 1", "Exercise 3"],
                    "friday": ["Exercise 2", "Exercise 4"],
                    "saturday": ["Exercise 5"],
                    "sunday": ["Rest or light stretching"]
                }},
                "general_advice": "Overall fitness advice for the conditions",
                "contraindications": ["Activities to avoid"]
            }}
            
            Focus on:
            - Safe exercises appropriate for the medical conditions
            - Gradual progression
            - Low-impact options when necessary
            - Exercises that can be done at home
            - Specific benefits for each condition
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a certified fitness expert and physical therapist who creates safe, personalized exercise plans for people with medical conditions. Always prioritize safety and provide evidence-based recommendations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                recommendations = json.loads(content)
                return recommendations
            except json.JSONDecodeError:
                # Fallback response
                return {
                    "daily_exercises": [
                        {
                            "name": "Light Walking",
                            "duration": "15-20 minutes",
                            "description": "Gentle walking at a comfortable pace",
                            "benefits": "Improves cardiovascular health and general wellness",
                            "precautions": "Start slowly and listen to your body",
                            "time_of_day": "morning"
                        },
                        {
                            "name": "Basic Stretching",
                            "duration": "10 minutes",
                            "description": "Simple stretching routine for flexibility",
                            "benefits": "Maintains joint mobility and reduces stiffness",
                            "precautions": "Don't force stretches, hold gently",
                            "time_of_day": "evening"
                        }
                    ],
                    "weekly_plan": {
                        "monday": ["Light Walking"],
                        "tuesday": ["Basic Stretching"],
                        "wednesday": ["Light Walking"],
                        "thursday": ["Basic Stretching"],
                        "friday": ["Light Walking"],
                        "saturday": ["Basic Stretching"],
                        "sunday": ["Rest"]
                    },
                    "general_advice": "Start with gentle exercises and gradually increase intensity. Always consult with your healthcare provider before starting any new exercise program.",
                    "contraindications": ["High-intensity exercises without medical clearance"]
                }
                
        except Exception as e:
            print(f"Error generating exercise recommendations: {e}")
            return {
                "error": "Unable to generate recommendations",
                "daily_exercises": [],
                "weekly_plan": {},
                "general_advice": "Please consult with a healthcare provider for exercise recommendations.",
                "contraindications": []
            }
    
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
                model="gpt-3.5-turbo",
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

    async def generate_health_recommendations(self, prompt: str) -> str:
        """
        Generate health recommendations using GPT-4
        
        Args:
            prompt: The health recommendation prompt
            
        Returns:
            Generated health recommendations
        """
        try:
            if self.client is None:
                raise Exception("OpenAI client not initialized")
                
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a certified healthcare AI assistant specializing in evidence-based health recommendations. Always emphasize the importance of consulting healthcare providers and provide safe, appropriate guidance."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Health recommendation generation failed: {str(e)}")
    
    async def generate_exercise_plan(self, user_profile: dict, medical_conditions: list) -> str:
        """
        Generate personalized exercise plan
        
        Args:
            user_profile: User profile information
            medical_conditions: List of medical conditions
            
        Returns:
            Personalized exercise plan
        """
        try:
            if self.client is None:
                raise Exception("OpenAI client not initialized")
                
            prompt = f"""
            Create a personalized exercise plan for a patient with the following profile:
            
            Profile: {user_profile}
            Medical Conditions: {medical_conditions}
            
            Provide:
            1. Safe exercise recommendations
            2. Frequency and duration guidelines
            3. Precautions and modifications
            4. Progress tracking suggestions
            
            Ensure all recommendations are medically appropriate and safe.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a certified fitness and health specialist creating safe, evidence-based exercise plans for patients with medical conditions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Exercise plan generation failed: {str(e)}")
    
    async def generate_dietary_recommendations(self, user_profile: dict, medical_conditions: list) -> str:
        """
        Generate personalized dietary recommendations
        
        Args:
            user_profile: User profile information
            medical_conditions: List of medical conditions
            
        Returns:
            Personalized dietary recommendations
        """
        try:
            if self.client is None:
                raise Exception("OpenAI client not initialized")
                
            prompt = f"""
            Create personalized dietary recommendations for a patient with:
            
            Profile: {user_profile}
            Medical Conditions: {medical_conditions}
            
            Provide:
            1. Recommended foods and nutrients
            2. Foods to limit or avoid
            3. Portion guidelines
            4. Meal planning tips
            5. Special considerations for their conditions
            
            Ensure recommendations are nutritionally sound and medically appropriate.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a certified nutritionist and dietitian specializing in medical nutrition therapy for various health conditions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Dietary recommendation generation failed: {str(e)}")

# Global GPT processor instance
gpt_processor = GPTProcessor()