import requests
import os
from dotenv import load_dotenv
import json
from typing import Dict, List, Optional, Union, Any

# Load environment variables from .env file
load_dotenv()

class OpenCorporatesAgent:
    """
    AI agent to interact with the OpenCorporates API to retrieve company information.
    """
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize the OpenCorporates agent with API credentials.
        
        Args:
            api_token: OpenCorporates API token. If None, tries to get from environment.
        """
        self.base_url = "https://api.opencorporates.com/v0.4"
        self.api_token = api_token or os.getenv("OPENCORPORATES_API_TOKEN")
        
        if not self.api_token:
            print("Warning: No API token provided. Some functions may be limited.")
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the OpenCorporates API.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters for the request
            
        Returns:
            JSON response as dictionary
        """
        if params is None:
            params = {}
            
        if self.api_token:
            params["api_token"] = self.api_token
            
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response content: {e.response.text}")
            return {"error": str(e)}
    
    def search_companies(self, query: str, jurisdiction_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for companies by name.
        
        Args:
            query: Company name to search for
            jurisdiction_code: Optional jurisdiction code (e.g., "us_ca" for California)
            
        Returns:
            List of matching companies
        """
        params = {"q": query}
        if jurisdiction_code:
            params["jurisdiction_code"] = jurisdiction_code
            
        response = self._make_request("companies/search", params)
        
        if "error" in response:
            return []
            
        try:
            return response.get("results", {}).get("companies", [])
        except (KeyError, AttributeError):
            return []
    
    def get_company_details(self, jurisdiction_code: str, company_number: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific company.
        
        Args:
            jurisdiction_code: Jurisdiction code (e.g., "us_ca" for California)
            company_number: Company registration number
            
        Returns:
            Company details
        """
        endpoint = f"companies/{jurisdiction_code}/{company_number}"
        response = self._make_request(endpoint)
        
        if "error" in response:
            return {}
            
        try:
            return response.get("results", {}).get("company", {})
        except (KeyError, AttributeError):
            return {}
    
    def get_company_officers(self, jurisdiction_code: str, company_number: str) -> List[Dict[str, Any]]:
        """
        Get officers/directors of a specific company.
        
        Args:
            jurisdiction_code: Jurisdiction code (e.g., "us_ca" for California)
            company_number: Company registration number
            
        Returns:
            List of company officers/directors
        """
        endpoint = f"companies/{jurisdiction_code}/{company_number}/officers"
        response = self._make_request(endpoint)
        
        if "error" in response:
            return []
            
        try:
            return response.get("results", {}).get("officers", [])
        except (KeyError, AttributeError):
            return []
    
    def find_company_controllers(self, company_name: str, jurisdiction_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Find controlling members of a company by name.
        This is a higher-level function that combines multiple API calls.
        
        Args:
            company_name: Name of the company to search
            jurisdiction_hint: Optional jurisdiction hint (e.g., "California" or "CA")
            
        Returns:
            Dictionary with company details and officers
        """
        # Convert jurisdiction hint to code if provided
        jurisdiction_code = None
        if jurisdiction_hint:
            # Very simplified mapping - in a real implementation you'd have a complete mapping
            state_codes = {
                "california": "us_ca",
                "ca": "us_ca",
                "illinois": "us_il",
                "il": "us_il",
                # Add more as needed
            }
            jurisdiction_code = state_codes.get(jurisdiction_hint.lower())
        
        # Search for the company
        companies = self.search_companies(company_name, jurisdiction_code)
        
        if not companies:
            return {
                "status": "not_found",
                "message": f"No companies found matching '{company_name}'",
                "results": []
            }
        
        results = []
        
        # Get details for each potential match (limiting to top 3 for performance)
        for company_data in companies[:3]:
            try:
                company = company_data.get("company", {})
                jurisdiction = company.get("jurisdiction_code")
                company_number = company.get("company_number")
                
                if jurisdiction and company_number:
                    # Get officers
                    officers = self.get_company_officers(jurisdiction, company_number)
                    
                    # Add to results
                    results.append({
                        "company_name": company.get("name"),
                        "jurisdiction": jurisdiction,
                        "company_number": company_number,
                        "incorporation_date": company.get("incorporation_date"),
                        "company_type": company.get("company_type"),
                        "current_status": company.get("current_status"),
                        "officers": officers
                    })
            except Exception as e:
                print(f"Error processing company: {e}")
        
        return {
            "status": "success" if results else "partial_results",
            "message": f"Found {len(results)} potential matches for '{company_name}'",
            "results": results
        }


# Example usage
if __name__ == "__main__":
    # Create the agent
    agent = OpenCorporatesAgent()
    
    # Example: Look up a company and its controllers
    company_name = "HOMECOMERS RCC INC"
    jurisdiction_hint = "CA"  # From the property in San Jose, CA
    
    print(f"Looking up information for: {company_name} in {jurisdiction_hint}")
    result = agent.find_company_controllers(company_name, jurisdiction_hint)
    
    # Pretty print the results
    print(json.dumps(result, indent=2))
    
    # Example of looking up another company
    company_name = "CTJ ESTATE LLC"
    result = agent.find_company_controllers(company_name, jurisdiction_hint)
    
    print(f"\nLooking up information for: {company_name} in {jurisdiction_hint}")
    print(json.dumps(result, indent=2))
