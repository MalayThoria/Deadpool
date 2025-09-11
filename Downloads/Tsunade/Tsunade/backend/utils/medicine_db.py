import requests
import json
from typing import Dict, List, Optional

class MedicineDatabase:
    def __init__(self):
        # FDA API endpoint for drug information
        self.fda_api_base = "https://api.fda.gov/drug"
        self.rxnav_api_base = "https://rxnav.nlm.nih.gov/REST"
    
    def get_fda_drug_info(self, drug_name: str) -> Optional[Dict]:
        """
        Get FDA drug information
        """
        try:
            # Search for drug in FDA database
            response = requests.get(
                f"{self.fda_api_base}/label.json",
                params={
                    "search": f"openfda.generic_name:\"{drug_name}\" OR openfda.brand_name:\"{drug_name}\"",
                    "limit": 1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    return data['results'][0]
            
            return None
            
        except Exception as e:
            print(f"FDA API error: {e}")
            return None
    
    def get_rxnav_drug_info(self, drug_name: str) -> Optional[Dict]:
        """
        Get RxNav drug information
        """
        try:
            # Search for drug in RxNav
            response = requests.get(
                f"{self.rxnav_api_base}/drugs.json",
                params={"name": drug_name},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('drugGroup', {}).get('conceptGroup'):
                    return data['drugGroup']
            
            return None
            
        except Exception as e:
            print(f"RxNav API error: {e}")
            return None
    
    def cross_verify_medicine(self, medicine_name: str, gpt_info: Dict) -> Dict:
        """
        Cross-verify medicine information with FDA and RxNav databases
        """
        verified_info = gpt_info.copy()
        
        # Try FDA database
        fda_info = self.get_fda_drug_info(medicine_name)
        if fda_info:
            verified_info['fda_verified'] = True
            verified_info['fda_source'] = 'FDA Database'
            
            # Extract FDA information
            if 'openfda' in fda_info:
                openfda = fda_info['openfda']
                if 'generic_name' in openfda:
                    verified_info['generic_name'] = openfda['generic_name'][0]
                if 'brand_name' in openfda:
                    verified_info['brand_names'] = openfda['brand_name']
        
        # Try RxNav database
        rxnav_info = self.get_rxnav_drug_info(medicine_name)
        if rxnav_info:
            verified_info['rxnav_verified'] = True
            verified_info['rxnav_source'] = 'RxNav Database'
        
        # Add verification status
        verified_info['verified'] = bool(fda_info or rxnav_info)
        verified_info['verification_sources'] = []
        
        if fda_info:
            verified_info['verification_sources'].append('FDA')
        if rxnav_info:
            verified_info['verification_sources'].append('RxNav')
        
        return verified_info
    
    def get_medicine_interactions(self, medicine_name: str) -> List[str]:
        """
        Get drug interactions from FDA database
        """
        try:
            response = requests.get(
                f"{self.fda_api_base}/label.json",
                params={
                    "search": f"openfda.generic_name:\"{medicine_name}\"",
                    "limit": 1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    label = data['results'][0]
                    
                    # Extract drug interactions
                    interactions = []
                    if 'drug_interactions' in label:
                        interactions.append(label['drug_interactions'][0])
                    if 'drug_interactions_table' in label:
                        interactions.append(label['drug_interactions_table'][0])
                    
                    return interactions
            
            return []
            
        except Exception as e:
            print(f"Interaction lookup error: {e}")
            return []

# Global medicine database instance
medicine_db = MedicineDatabase() 