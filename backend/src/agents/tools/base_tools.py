"""
Base tools and HTTP client for API interactions.
This provides the foundation for all API calling tools.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG to INFO to reduce verbose output
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class FHIRAPIClient:
    """
    HTTP client for interacting with the FHIR API.
    Handles authentication, error handling, and response formatting.
    """

    def __init__(self, base_url: str = "http://localhost:8000/api/v2"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a GET request to the API.

        Args:
            endpoint: API endpoint (e.g., '/patients', '/conditions')
            params: Query parameters

        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, allow_redirects=True)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GET request failed for {url}: {e}")
            return {
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None),
            }

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request to the API.

        Args:
            endpoint: API endpoint
            data: Request body data

        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"POST request failed for {url}: {e}")
            return {
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None),
            }

    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a PUT request to the API.

        Args:
            endpoint: API endpoint
            data: Request body data

        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.put(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"PUT request failed for {url}: {e}")
            return {
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None),
            }

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a DELETE request to the API.

        Args:
            endpoint: API endpoint

        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            return {"success": True, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            logger.error(f"DELETE request failed for {url}: {e}")
            return {
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None),
            }


# Global API client instance
api_client = FHIRAPIClient()


def format_patient_summary(patient_data: Dict[str, Any]) -> str:
    """
    Format patient data into a human-readable summary.

    Args:
        patient_data: Patient data from API

    Returns:
        Formatted patient summary
    """
    logger.debug(f"📝 INTERNAL FUNCTION CALLED: format_patient_summary()")
    if "error" in patient_data:
        return f"Error retrieving patient: {patient_data['error']}"

    # Basic Information
    name = f"{patient_data.get('first_name', 'Unknown')} {patient_data.get('last_name', 'Unknown')}"
    birth_date = patient_data.get("birth_date", "Unknown")
    gender = patient_data.get("gender", "Unknown")
    patient_id = patient_data.get("id", "Unknown")
    identifier = patient_data.get("identifier", "Not assigned")

    # Contact Information
    phone = patient_data.get("phone", "Not provided")
    email = patient_data.get("email", "Not provided")

    # Address Information
    address_line = patient_data.get("address_line", "Not provided")
    city = patient_data.get("city", "Not provided")
    state = patient_data.get("state", "Not provided")
    postal_code = patient_data.get("postal_code", "Not provided")

    # Demographics
    marital_status = patient_data.get("marital_status", "Not specified")
    language = patient_data.get("language", "Not specified")
    race = patient_data.get("race", "Not specified")
    ethnicity = patient_data.get("ethnicity", "Not specified")

    # Medical Information
    deceased_date = patient_data.get("deceased_date", "N/A")
    active = patient_data.get("active", True)
    managing_org = patient_data.get("managing_organization_identifier", "Not assigned")

    # Format the complete summary with better spacing
    # Handle deceased date conditionally (can't use backslash in nested f-string)
    deceased_line = (
        f"**Deceased Date:** {deceased_date}\n" if deceased_date != "N/A" else ""
    )

    return f"""**PATIENT INFORMATION**

**Name:** {name}
**ID:** {patient_id}
**Medical Record Number:** {identifier}
**Birth Date:** {birth_date}
**Gender:** {gender}
**Status:** {'Active' if active else 'Inactive'}
{deceased_line}**CONTACT INFORMATION**

**Phone:** {phone}
**Email:** {email}

**ADDRESS**

**Address:** {address_line}
**City:** {city}
**State:** {state}
**Postal Code:** {postal_code}

**DEMOGRAPHICS**

**Marital Status:** {marital_status}
**Language:** {language}
**Race:** {race}
**Ethnicity:** {ethnicity}

**ORGANIZATIONAL**

**Managing Organization:** {managing_org}
"""


def format_condition_summary(condition_data: Dict[str, Any]) -> str:
    """
    Format condition data into a human-readable summary.

    Args:
        condition_data: Condition data from API

    Returns:
        Formatted condition summary
    """
    logger.debug(f"📝 INTERNAL FUNCTION CALLED: format_condition_summary()")
    if "error" in condition_data:
        return f"Error retrieving condition: {condition_data['error']}"

    code = condition_data.get("code", "Unknown")
    display = condition_data.get("display", "Unknown")
    status = condition_data.get("status", "Unknown")
    onset_date = condition_data.get("onset_date", "Unknown")

    return f"Condition: {display} ({code})\nStatus: {status}\nOnset Date: {onset_date}"


def format_encounter_summary(encounter_data: Dict[str, Any]) -> str:
    """
    Format encounter data into a human-readable summary.

    Args:
        encounter_data: Encounter data from API

    Returns:
        Formatted encounter summary
    """
    logger.debug(f"📝 INTERNAL FUNCTION CALLED: format_encounter_summary()")
    if "error" in encounter_data:
        return f"Error retrieving encounter: {encounter_data['error']}"

    status = encounter_data.get("status", "Unknown")
    start_time = encounter_data.get("start_time", "Unknown")
    class_code = encounter_data.get("class_code", "Unknown")

    return f"Encounter: {class_code}\nStatus: {status}\nStart Time: {start_time}"


def format_list_summary(items: List[Dict[str, Any]], item_type: str) -> str:
    """
    Format a list of items into a human-readable summary.

    Args:
        items: List of items from API
        item_type: Type of items (e.g., 'patients', 'conditions')

    Returns:
        Formatted list summary
    """
    if not items:
        return f"No {item_type} found."

    if len(items) == 1:
        return f"Found 1 {item_type[:-1]}: {items[0].get('id', 'Unknown')}"

    return f"Found {len(items)} {item_type}. IDs: {', '.join([str(item.get('id', 'Unknown')) for item in items[:5]])}{'...' if len(items) > 5 else ''}"
