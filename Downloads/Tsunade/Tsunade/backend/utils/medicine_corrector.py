import re
import difflib
from typing import List, Dict, Tuple, Optional
import requests
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

class MedicineNameCorrector:
    def __init__(self):
        # Common medicine name patterns and corrections
        self.common_medicines = {
            # Antibiotics
            'amoxicillin': ['amoxicillin', 'amoxil', 'trimox'],
            'azithromycin': ['azithromycin', 'zithromax', 'z-pak'],
            'doxycycline': ['doxycycline', 'vibramycin', 'doryx'],
            'ciprofloxacin': ['ciprofloxacin', 'cipro'],
            'metronidazole': ['metronidazole', 'flagyl'],
            
            # Pain relievers
            'ibuprofen': ['ibuprofen', 'advil', 'motrin', 'brufen'],
            'acetaminophen': ['acetaminophen', 'tylenol', 'paracetamol'],
            'aspirin': ['aspirin', 'bayer', 'ecotrin'],
            'naproxen': ['naproxen', 'aleve', 'naprosyn'],
            
            # Anti-inflammatory
            'prednisone': ['prednisone', 'deltasone', 'sterapred'],
            'methylprednisolone': ['methylprednisolone', 'medrol', 'depo-medrol'],
            
            # Antihistamines
            'diphenhydramine': ['diphenhydramine', 'benadryl'],
            'loratadine': ['loratadine', 'claritin'],
            'cetirizine': ['cetirizine', 'zyrtec'],
            
            # Antacids
            'omeprazole': ['omeprazole', 'prilosec'],
            'pantoprazole': ['pantoprazole', 'protonix'],
            'ranitidine': ['ranitidine', 'zantac'],
            'famotidine': ['famotidine', 'pepcid'],
            
            # Blood pressure
            'amlodipine': ['amlodipine', 'norvasc'],
            'lisinopril': ['lisinopril', 'zestril', 'prinivil'],
            'metoprolol': ['metoprolol', 'lopressor', 'toprol'],
            'atenolol': ['atenolol', 'tenormin'],
            
            # Diabetes
            'metformin': ['metformin', 'glucophage'],
            'glipizide': ['glipizide', 'glucotrol'],
            
            # Cholesterol
            'atorvastatin': ['atorvastatin', 'lipitor'],
            'simvastatin': ['simvastatin', 'zocor'],
            'rosuvastatin': ['rosuvastatin', 'crestor'],
            
            # Antidepressants
            'sertraline': ['sertraline', 'zoloft'],
            'fluoxetine': ['fluoxetine', 'prozac'],
            'escitalopram': ['escitalopram', 'lexapro'],
            
                }
        
        # Common misspellings and corrections
        self.misspellings = {
            'amoxcillin': 'amoxicillin',
            'amoxacillin': 'amoxicillin',
            'amoxcillan': 'amoxicillin',
            'amoxcillen': 'amoxicillin',
            'ibuprofin': 'ibuprofen',
            'ibupropen': 'ibuprofen',
            'ibuprophin': 'ibuprofen',
            'omeprazol': 'omeprazole',
            'omeprazol': 'omeprazole',
            'prednisolone': 'prednisone',
        }
        
        # Common misspellings and corrections
        self.misspellings = {
            'amoxcillin': 'amoxicillin',
            'amoxacillin': 'amoxicillin',
            'amoxcillan': 'amoxicillin',
            'amoxcillen': 'amoxicillin',
            'ibuprofin': 'ibuprofen',
            'ibupropen': 'ibuprofen',
            'ibuprophin': 'ibuprofen',
            'omeprazol': 'omeprazole',
            'omeprazol': 'omeprazole',
            'prednisolone': 'prednisone',
        }
        
        # Common medicine suffixes and patterns
        self.medicine_suffixes = [
            'cin', 'mycin', 'cillin', 'cycline', 'floxacin', 'azole',
            'pril', 'sartan', 'olol', 'pine', 'statin', 'formin',
            'pam', 'ine', 'ate', 'ide', 'one', 'ine'
        ]
        
        # Medicine strength patterns
        self.strength_patterns = [
            r'\d+\s*mg', r'\d+\s*mcg', r'\d+\s*g', r'\d+\s*ml',
            r'\d+\s*%', r'\d+\s*units'
        ]
    
    def clean_medicine_name(self, name: str) -> str:
        """
        Clean and normalize medicine name
        """
        # Remove extra spaces and convert to lowercase
        name = re.sub(r'\s+', ' ', name.strip().lower())
        
        # Remove common words that aren't part of medicine names
        common_words = ['tablet', 'capsule', 'pill', 'medicine', 'drug', 'medication']
        for word in common_words:
            name = name.replace(word, '').strip()
        
        # Remove strength information
        for pattern in self.strength_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        return name.strip()
    
    def find_similar_medicines(self, medicine_name: str, threshold: int = 80) -> List[Tuple[str, int]]:
        """
        Find similar medicine names using fuzzy matching
        """
        cleaned_name = self.clean_medicine_name(medicine_name)
        
        # Get all possible medicine names
        all_medicines = []
        for generic, brands in self.common_medicines.items():
            all_medicines.extend(brands)
        
        # Use fuzzy matching to find similar names
        matches = process.extract(cleaned_name, all_medicines, limit=10)
        
        # Filter by threshold
        return [(name, score) for name, score in matches if score >= threshold]
    
    def correct_medicine_name(self, medicine_name: str) -> Tuple[str, float, str]:
        """
        Correct medicine name and return (corrected_name, confidence, method)
        """
        cleaned_name = self.clean_medicine_name(medicine_name)
        
        # Direct match in common medicines
        for generic, brands in self.common_medicines.items():
            if cleaned_name in brands or cleaned_name == generic:
                return generic, 100.0, "exact_match"
        
        # Check for common misspellings
        if cleaned_name in self.misspellings:
            return self.misspellings[cleaned_name], 95.0, "misspelling_correction"
        
        # Fuzzy matching
        similar_medicines = self.find_similar_medicines(cleaned_name, threshold=70)
        
        if similar_medicines:
            best_match, confidence = similar_medicines[0]
            
            # Find the generic name for the best match
            for generic, brands in self.common_medicines.items():
                if best_match in brands or best_match == generic:
                    return generic, confidence, "fuzzy_match"
        
        # If no good match found, return original with low confidence
        return medicine_name, 30.0, "no_correction"
    
    def extract_medicine_context(self, text: str) -> List[str]:
        """
        Extract medicine names from text using context clues
        """
        medicines = []
        
        # Look for medicine patterns in text
        medicine_patterns = [
            r'\b([A-Z][a-z]+(?:[a-z]+)*)\s*(?:tablet|capsule|pill|mg|mcg|g)\b',
            r'\b([A-Z][a-z]+(?:[a-z]+)*)\s*(?:cin|mycin|cillin|cycline|floxacin|azole)\b',
            r'\b([A-Z][a-z]+(?:[a-z]+)*)\s*(?:pril|sartan|olol|pine|statin|formin)\b',
        ]
        
        for pattern in medicine_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            medicines.extend(matches)
        
        return list(set(medicines))
    
    def verify_medicine_with_api(self, medicine_name: str) -> Dict:
        """
        Verify medicine name using external APIs
        """
        try:
            # Try FDA API
            fda_response = requests.get(
                "https://api.fda.gov/drug/label.json",
                params={
                    "search": f"openfda.generic_name:\"{medicine_name}\" OR openfda.brand_name:\"{medicine_name}\"",
                    "limit": 1
                },
                timeout=5
            )
            
            if fda_response.status_code == 200:
                data = fda_response.json()
                if data.get('results'):
                    return {
                        'verified': True,
                        'source': 'FDA',
                        'name': medicine_name,
                        'confidence': 90
                    }
            
            # Try RxNav API
            rxnav_response = requests.get(
                f"https://rxnav.nlm.nih.gov/REST/drugs.json",
                params={"name": medicine_name},
                timeout=5
            )
            
            if rxnav_response.status_code == 200:
                data = rxnav_response.json()
                if data.get('drugGroup', {}).get('conceptGroup'):
                    return {
                        'verified': True,
                        'source': 'RxNav',
                        'name': medicine_name,
                        'confidence': 85
                    }
            
            return {
                'verified': False,
                'source': 'none',
                'name': medicine_name,
                'confidence': 0
            }
            
        except Exception as e:
            return {
                'verified': False,
                'source': 'error',
                'name': medicine_name,
                'confidence': 0,
                'error': str(e)
            }
    
    def correct_and_verify_medicines(self, extracted_medicines: List[str], context_text: str = "") -> List[Dict]:
        """
        Correct and verify a list of medicine names
        """
        corrected_medicines = []
        
        for medicine in extracted_medicines:
            # Correct the medicine name
            corrected_name, confidence, method = self.correct_medicine_name(medicine)
            
            # Verify with external APIs
            verification = self.verify_medicine_with_api(corrected_name)
            
            # Combine correction and verification
            result = {
                'original': medicine,
                'corrected': corrected_name,
                'correction_confidence': confidence,
                'correction_method': method,
                'verified': verification['verified'],
                'verification_source': verification['source'],
                'verification_confidence': verification['confidence'],
                'final_confidence': (confidence + verification['confidence']) / 2
            }
            
            corrected_medicines.append(result)
        
        # Sort by confidence
        corrected_medicines.sort(key=lambda x: x['final_confidence'], reverse=True)
        
        return corrected_medicines

# Global medicine corrector instance
medicine_corrector = MedicineNameCorrector() 