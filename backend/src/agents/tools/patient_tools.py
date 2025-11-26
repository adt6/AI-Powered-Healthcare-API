"""
Patient-related tools for the clinical AI agent.
These tools allow the agent to interact with patient data from the FHIR API.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain.tools import tool

from .base_tools import (
    api_client,
    format_condition_summary,
    format_encounter_summary,
    format_list_summary,
    format_patient_summary,
)

# Configure logging for tool calls (logging already configured in base_tools)
logger = logging.getLogger(__name__)


@tool
def get_patient_info(patient_identifier: str) -> str:
    """
    Get detailed information about a specific patient by their ID or identifier.
    
    Use this tool when the user asks for patient information and provides a patient ID.
    This includes queries about patient details, demographics, or basic information.
    
    Always use this tool immediately when a patient ID is mentioned - do not ask for more information.

    Args:
        patient_identifier: The patient ID as a string (e.g., "2", "3", "123") or identifier (UUID/MRN)

    Returns:
        Formatted patient information including name, birth date, gender, and ID
    """
    logger.info(f"🔧 TOOL CALLED: get_patient_info(patient_identifier='{patient_identifier}')")
    try:
        # Clean the input - remove any parameter formatting
        clean_identifier = patient_identifier.strip()
        if "=" in clean_identifier:
            clean_identifier = clean_identifier.split("=")[1].strip()

        # Try to get by ID first (if it's a number)
        if clean_identifier.isdigit():
            response = api_client.get(f"/patients/{clean_identifier}")
        else:
            # Search by identifier (UUID/MRN) - should be unique
            response = api_client.get(
                "/patients", params={"identifier": clean_identifier}
            )
            if isinstance(response, list):
                if len(response) == 0:
                    return f"No patient found with identifier: {clean_identifier}"
                elif len(response) == 1:
                    response = response[0]  # Take the single result
                else:
                    # This should never happen for UUIDs, but handle gracefully
                    return f"Multiple patients found with identifier: {clean_identifier}. Please use a more specific identifier."

        if "error" in response:
            return f"Error retrieving patient {clean_identifier}: {response['error']}"

        return format_patient_summary(response)

    except Exception as e:
        return f"Unexpected error retrieving patient {patient_identifier}: {str(e)}"


@tool
def search_patients(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    birth_date: Optional[str] = None,
    gender: Optional[str] = None,
    limit: int = 20,
) -> str:
    """
    Search for patients based on various criteria such as name, birth date, or gender.

    Use this tool when the user wants to find patients by name or other demographic information.

    Args:
        first_name: Patient's first name (partial match) - pass only the name value
        last_name: Patient's last name (partial match) - pass only the name value
        birth_date: Patient's birth date in YYYY-MM-DD format
        gender: Patient's gender (male, female, other, unknown)
        limit: Maximum number of results to return (default: 20, max: 100)

    Returns:
        List of patients matching the search criteria
    """
    logger.info(f"🔧 TOOL CALLED: search_patients(first_name='{first_name}', last_name='{last_name}', birth_date='{birth_date}', gender='{gender}', limit={limit})")
    try:
        # Clean input parameters - remove any parameter formatting
        clean_first_name = first_name.strip() if first_name else None
        clean_last_name = last_name.strip() if last_name else None
        clean_birth_date = birth_date.strip() if birth_date else None
        clean_gender = gender.strip() if gender else None

        # Handle complex parameter formatting issues
        # Case: first_name="Robert854", last_name="Botsford977" (all in one string)
        if (
            clean_first_name
            and "," in clean_first_name
            and "last_name=" in clean_first_name
        ):
            # This is a combined string like: first_name="Robert854", last_name="Botsford977"
            parts = clean_first_name.split(",")
            for part in parts:
                part = part.strip()
                if "first_name=" in part:
                    clean_first_name = part.split("first_name=")[1].strip().strip('"')
                elif "last_name=" in part:
                    clean_last_name = part.split("last_name=")[1].strip().strip('"')

        # Case: Single parameter with quotes (e.g., first_name="Maxwell782")
        elif (
            clean_first_name
            and "=" in clean_first_name
            and "first_name=" in clean_first_name
        ):
            clean_first_name = (
                clean_first_name.split("first_name=")[1].strip().strip('"')
            )

        # Case: Single parameter with quotes (e.g., last_name="Smith123")
        elif (
            clean_last_name
            and "=" in clean_last_name
            and "last_name=" in clean_last_name
        ):
            clean_last_name = clean_last_name.split("last_name=")[1].strip().strip('"')

        # Build query parameters
        params = {}
        if clean_first_name:
            params["first_name"] = clean_first_name
        if clean_last_name:
            params["last_name"] = clean_last_name
        if clean_birth_date:
            params["birth_date"] = clean_birth_date
        if clean_gender:
            params["gender"] = clean_gender
        if limit:
            params["limit"] = min(limit, 100)  # Cap at 100

        # Debug logging (can be removed in production)
        # print(f"DEBUG: Original inputs - first_name='{first_name}', last_name='{last_name}'")
        # print(f"DEBUG: Cleaned inputs - first_name='{clean_first_name}', last_name='{clean_last_name}'")
        # print(f"DEBUG: Final params: {params}")

        response = api_client.get("/patients", params=params)

        if "error" in response:
            return f"Error searching patients: {response['error']}"

        patients = response if isinstance(response, list) else []

        if not patients:
            return "No patients found matching the search criteria."

        # Format the results
        result = f"Found {len(patients)} patient(s):\n\n"
        for i, patient in enumerate(patients[:10], 1):  # Show max 10
            result += f"{i}. **{patient.get('name', 'Unknown')}** (ID: {patient.get('id', 'Unknown')})\n"
            result += f"   Birth Date: {patient.get('birth_date', 'Unknown')}\n"
            result += f"   Gender: {patient.get('gender', 'Unknown')}\n"
            result += f"   Status: {patient.get('status', 'Unknown')}\n\n"

        if len(patients) > 10:
            result += f"... and {len(patients) - 10} more patients."

        return result

    except Exception as e:
        return f"Unexpected error searching patients: {str(e)}"


@tool
def get_patient_conditions(patient_identifier: str) -> str:
    """
    Get all medical conditions for a specific patient.
    
    Use this tool when the user asks about a patient's medical conditions, diagnoses, or health problems.
    Call immediately when a patient ID and "conditions" are mentioned together.

    Args:
        patient_identifier: The patient ID as a string (e.g., "2", "3", "123") or identifier (UUID/MRN)

    Returns:
        List of conditions associated with the patient
    """
    logger.info(f"🔧 TOOL CALLED: get_patient_conditions(patient_identifier='{patient_identifier}')")
    try:
        # Clean the input - remove any parameter formatting
        clean_identifier = patient_identifier.strip()
        if "=" in clean_identifier:
            clean_identifier = clean_identifier.split("=")[1].strip()

        # Remove quotes if present
        if clean_identifier.startswith('"') and clean_identifier.endswith('"'):
            clean_identifier = clean_identifier[1:-1]
        elif clean_identifier.startswith("'") and clean_identifier.endswith("'"):
            clean_identifier = clean_identifier[1:-1]

        # Get patient ID - use API directly, don't call other tools
        if clean_identifier.isdigit():
            patient_id = int(clean_identifier)
        else:
            # Search for patient by identifier to get the integer ID
            response = api_client.get(
                "/patients", params={"identifier": clean_identifier}
            )
            if isinstance(response, list) and len(response) > 0:
                patient_id = response[0].get("id")
            else:
                return f"No patient found with identifier: {clean_identifier}"

        response = api_client.get(f"/conditions", params={"patient_id": patient_id})

        if "error" in response:
            return f"Error retrieving conditions for patient {patient_identifier}: {response['error']}"

        conditions = response if isinstance(response, list) else []

        if not conditions:
            return f"No conditions found for patient {patient_identifier}."

        # Format the results
        result = f"Patient {patient_identifier} has {len(conditions)} condition(s):\n\n"
        for i, condition in enumerate(conditions, 1):
            result += f"{i}. {format_condition_summary(condition)}\n\n"

        return result

    except Exception as e:
        return f"Unexpected error retrieving conditions for patient {patient_identifier}: {str(e)}"


@tool
def get_patient_encounters(patient_identifier: str) -> str:
    """
    Get all medical encounters for a specific patient.
    
    Use this tool when the user asks about a patient's visits, appointments, hospital stays, or encounters.
    Call immediately when a patient ID and "encounters", "visits", or "appointments" are mentioned.

    Args:
        patient_identifier: The patient ID as a string (e.g., "2", "3", "123") or identifier (UUID/MRN)

    Returns:
        List of encounters associated with the patient
    """
    logger.info(f"🔧 TOOL CALLED: get_patient_encounters(patient_identifier='{patient_identifier}')")
    try:
        # Clean the input - remove any parameter formatting
        clean_identifier = patient_identifier.strip()
        if "=" in clean_identifier:
            clean_identifier = clean_identifier.split("=")[1].strip()

        # Get the patient's integer ID
        if clean_identifier.isdigit():
            patient_id = int(clean_identifier)
        else:
            # Search for patient by identifier to get the integer ID
            response = api_client.get(
                "/patients", params={"identifier": clean_identifier}
            )
            if isinstance(response, list) and len(response) > 0:
                patient_id = response[0].get("id")
            else:
                return f"No patient found with identifier: {clean_identifier}"

        response = api_client.get(f"/encounters", params={"patient_id": patient_id})

        if "error" in response:
            return f"Error retrieving encounters for patient {patient_identifier}: {response['error']}"

        encounters = response if isinstance(response, list) else []

        if not encounters:
            return f"No encounters found for patient {patient_identifier}."

        # Format the results
        result = f"Patient {patient_identifier} has {len(encounters)} encounter(s):\n\n"
        for i, encounter in enumerate(encounters, 1):
            result += f"{i}. {format_encounter_summary(encounter)}\n\n"

        return result

    except Exception as e:
        return f"Unexpected error retrieving encounters for patient {patient_identifier}: {str(e)}"


@tool
def get_patient_summary(patient_identifier: str) -> str:
    """
    Get a comprehensive summary of a patient including their basic info, conditions, and encounters.

    Args:
        patient_identifier: The patient ID (integer) or identifier (UUID/MRN)

    Returns:
        Complete patient summary with all related information
    """
    logger.info(f"🔧 TOOL CALLED: get_patient_summary(patient_identifier='{patient_identifier}')")
    try:
        # Clean the input - remove any parameter formatting
        clean_identifier = patient_identifier.strip()
        if "=" in clean_identifier:
            clean_identifier = clean_identifier.split("=")[1].strip()

        # Remove quotes if present
        if clean_identifier.startswith('"') and clean_identifier.endswith('"'):
            clean_identifier = clean_identifier[1:-1]
        elif clean_identifier.startswith("'") and clean_identifier.endswith("'"):
            clean_identifier = clean_identifier[1:-1]

        # Get patient ID - use API directly
        if clean_identifier.isdigit():
            patient_id = int(clean_identifier)
            patient_response = api_client.get(f"/patients/{clean_identifier}")
        else:
            # Search for patient by identifier
            patient_response = api_client.get(
                "/patients", params={"identifier": clean_identifier}
            )
            if isinstance(patient_response, list):
                if len(patient_response) == 0:
                    return f"No patient found with identifier: {clean_identifier}"
                patient_response = patient_response[0]
            patient_id = patient_response.get("id")

        if "error" in patient_response:
            return f"Error retrieving patient {clean_identifier}: {patient_response['error']}"

        # Get patient basic info (formatted)
        patient_info = format_patient_summary(patient_response)

        # Get conditions - use API directly
        conditions_response = api_client.get(f"/conditions", params={"patient_id": patient_id})
        if isinstance(conditions_response, dict) and "error" in conditions_response:
            conditions_info = f"Error retrieving conditions: {conditions_response['error']}"
        else:
            conditions = conditions_response if isinstance(conditions_response, list) else []
            if not conditions:
                conditions_info = f"No conditions found for patient {clean_identifier}."
            else:
                conditions_info = f"Patient {clean_identifier} has {len(conditions)} condition(s):\n\n"
                for i, condition in enumerate(conditions, 1):
                    conditions_info += f"{i}. {format_condition_summary(condition)}\n\n"

        # Get encounters - use API directly
        encounters_response = api_client.get(f"/encounters", params={"patient_id": patient_id})
        if isinstance(encounters_response, dict) and "error" in encounters_response:
            encounters_info = f"Error retrieving encounters: {encounters_response['error']}"
        else:
            encounters = encounters_response if isinstance(encounters_response, list) else []
            if not encounters:
                encounters_info = f"No encounters found for patient {clean_identifier}."
            else:
                encounters_info = f"Patient {clean_identifier} has {len(encounters)} encounter(s):\n\n"
                for i, encounter in enumerate(encounters, 1):
                    encounters_info += f"{i}. {format_encounter_summary(encounter)}\n\n"

        # Combine all information
        result = f"=== PATIENT SUMMARY ===\n\n"
        result += f"BASIC INFORMATION:\n{patient_info}\n\n"
        result += f"MEDICAL CONDITIONS:\n{conditions_info}\n\n"
        result += f"MEDICAL ENCOUNTERS:\n{encounters_info}\n"

        return result

    except Exception as e:
        return f"Unexpected error creating patient summary for {patient_identifier}: {str(e)}"


@tool
def get_patient_observations(patient_identifier: str) -> str:
    """
    Get all medical observations (lab results, vital signs, etc.) for a specific patient.

    Args:
        patient_identifier (str): The patient ID or medical record number

    Returns:
        str: Formatted list of patient observations
    """
    logger.info(f"🔧 TOOL CALLED: get_patient_observations(patient_identifier='{patient_identifier}')")
    try:
        # Clean the patient identifier
        clean_identifier = patient_identifier.strip()
        if "=" in clean_identifier:
            clean_identifier = clean_identifier.split("=")[1].strip()

        # Remove quotes if present
        if clean_identifier.startswith('"') and clean_identifier.endswith('"'):
            clean_identifier = clean_identifier[1:-1]
        elif clean_identifier.startswith("'") and clean_identifier.endswith("'"):
            clean_identifier = clean_identifier[1:-1]

        # Get patient observations from API
        observations_data = api_client.get(
            f"/observations?patient_id={clean_identifier}"
        )

        if not observations_data:
            return f"No observations found for patient {clean_identifier}"

        # Format observations
        formatted_observations = []
        for i, observation in enumerate(observations_data, 1):
            formatted_obs = format_observation_summary(observation)
            formatted_observations.append(f"{i}. {formatted_obs}")

        return (
            f"Patient {clean_identifier} has {len(observations_data)} observation(s):\n"
            + "\n".join(formatted_observations)
        )

    except Exception as e:
        return (
            f"Error retrieving observations for patient {patient_identifier}: {str(e)}"
        )


@tool
def get_patient_observation_by_type(
    patient_identifier: str,
    observation_type: str,
) -> str:
    """
    Get specific medical observations for a patient by observation type.
    
    Use this tool when the user asks for a specific measurement or observation type.
    Examples of when to use this:
    - "What is patient 3's hemoglobin level?" → observation_type="hemoglobin"
    - "Show me blood pressure readings for patient 3" → observation_type="blood pressure"
    - "What are the cholesterol values?" → observation_type="cholesterol"
    - "Get patient 3's glucose levels" → observation_type="glucose"
    - "Show me BMI measurements" → observation_type="BMI" or "body mass index"
    
    This tool filters observations to show only the requested type, making it much more useful
    than listing all observations when clinicians need specific information.
    
    Args:
        patient_identifier: The patient ID as a string (e.g., "3", "123") or identifier (UUID/MRN)
        observation_type: The type of observation to filter (e.g., "hemoglobin", "blood pressure", 
                         "cholesterol", "glucose", "BMI", "weight", "temperature"). 
                         Use common clinical terms - the system will match partial names.
    
    Returns:
        Formatted list of matching observations with values, dates, and status
    """
    logger.info(
        f"🔧 TOOL CALLED: get_patient_observation_by_type(patient_identifier='{patient_identifier}', observation_type='{observation_type}')"
    )
    try:
        # Clean the patient identifier
        clean_identifier = patient_identifier.strip()
        if "=" in clean_identifier:
            clean_identifier = clean_identifier.split("=")[1].strip()

        # Remove quotes if present
        if clean_identifier.startswith('"') and clean_identifier.endswith('"'):
            clean_identifier = clean_identifier[1:-1]
        elif clean_identifier.startswith("'") and clean_identifier.endswith("'"):
            clean_identifier = clean_identifier[1:-1]

        # Clean observation type
        clean_observation_type = observation_type.strip()
        if clean_observation_type.startswith('"') and clean_observation_type.endswith('"'):
            clean_observation_type = clean_observation_type[1:-1]
        elif clean_observation_type.startswith("'") and clean_observation_type.endswith("'"):
            clean_observation_type = clean_observation_type[1:-1]

        # Get patient ID if identifier is not numeric
        if clean_identifier.isdigit():
            patient_id = int(clean_identifier)
        else:
            # Search for patient by identifier to get the integer ID
            patient_response = api_client.get(
                "/patients", params={"identifier": clean_identifier}
            )
            if isinstance(patient_response, list) and len(patient_response) > 0:
                patient_id = patient_response[0].get("id")
            else:
                return f"No patient found with identifier: {clean_identifier}"

        # Get filtered observations from API using code_display filter
        observations_data = api_client.get(
            "/observations",
            params={
                "patient_id": patient_id,
                "code_display": clean_observation_type,
            },
        )

        if not observations_data:
            return (
                f"No observations of type '{clean_observation_type}' found for patient {clean_identifier}. "
                f"Try using more general terms like 'hemoglobin', 'blood pressure', 'cholesterol', etc."
            )

        # Format observations
        formatted_observations = []
        for i, observation in enumerate(observations_data, 1):
            formatted_obs = format_observation_summary(observation)
            formatted_observations.append(f"{i}. {formatted_obs}")

        result = (
            f"Patient {clean_identifier} has {len(observations_data)} {clean_observation_type} observation(s):\n\n"
            + "\n".join(formatted_observations)
        )

        return result

    except Exception as e:
        return (
            f"Error retrieving {observation_type} observations for patient {patient_identifier}: {str(e)}"
        )


# Helper function for observation formatting
def format_observation_summary(observation_data: Dict[str, Any]) -> str:
    """Format observation data into a human-readable summary."""
    if "error" in observation_data:
        return f"Error retrieving observation: {observation_data['error']}"

    # Use correct field names from API
    code_display = observation_data.get("code_display", "Unknown")
    code = observation_data.get("code", "")
    status = observation_data.get("status", "Unknown")
    
    # Handle both numeric and string values
    value_quantity = observation_data.get("value_quantity")
    value_string = observation_data.get("value_string")
    value_unit = observation_data.get("value_unit", "")
    
    # Determine the value to display
    if value_quantity is not None:
        value_str = f"{value_quantity} {value_unit}".strip()
    elif value_string:
        value_str = value_string
    else:
        value_str = "No value recorded"
    
    # Format date
    effective_time = observation_data.get("effective_time")
    if effective_time:
        if isinstance(effective_time, str):
            date_str = effective_time
        else:
            # Handle datetime object
            from datetime import datetime
            if isinstance(effective_time, datetime):
                date_str = effective_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                date_str = str(effective_time)
    else:
        date_str = "Date not available"
    
    # Format with code if available
    code_info = f" ({code})" if code else ""
    
    return f"{code_display}{code_info}: {value_str} | {date_str} | {status}"
