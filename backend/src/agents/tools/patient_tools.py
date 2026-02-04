"""
Patient-related tools for the clinical AI agent.
These tools allow the agent to interact with patient data from the FHIR API.
"""

import logging
from datetime import datetime
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
    logger.info(
        f"🔧 TOOL CALLED: get_patient_info(patient_identifier='{patient_identifier}')"
    )
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
    logger.info(
        f"🔧 TOOL CALLED: search_patients(first_name='{first_name}', last_name='{last_name}', birth_date='{birth_date}', gender='{gender}', limit={limit})"
    )
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
    logger.info(
        f"🔧 TOOL CALLED: get_patient_conditions(patient_identifier='{patient_identifier}')"
    )
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
    logger.info(
        f"🔧 TOOL CALLED: get_patient_encounters(patient_identifier='{patient_identifier}')"
    )
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
    logger.info(
        f"🔧 TOOL CALLED: get_patient_summary(patient_identifier='{patient_identifier}')"
    )
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
        conditions_response = api_client.get(
            f"/conditions", params={"patient_id": patient_id}
        )
        if isinstance(conditions_response, dict) and "error" in conditions_response:
            conditions_info = (
                f"Error retrieving conditions: {conditions_response['error']}"
            )
        else:
            conditions = (
                conditions_response if isinstance(conditions_response, list) else []
            )
            if not conditions:
                conditions_info = f"No conditions found for patient {clean_identifier}."
            else:
                conditions_info = f"Patient {clean_identifier} has {len(conditions)} condition(s):\n\n"
                for i, condition in enumerate(conditions, 1):
                    conditions_info += f"{i}. {format_condition_summary(condition)}\n\n"

        # Get encounters - use API directly
        encounters_response = api_client.get(
            f"/encounters", params={"patient_id": patient_id}
        )
        if isinstance(encounters_response, dict) and "error" in encounters_response:
            encounters_info = (
                f"Error retrieving encounters: {encounters_response['error']}"
            )
        else:
            encounters = (
                encounters_response if isinstance(encounters_response, list) else []
            )
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
    logger.info(
        f"🔧 TOOL CALLED: get_patient_observations(patient_identifier='{patient_identifier}')"
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

        # Get patient observations from API
        observations_data = api_client.get(
            f"/observations?patient_id={clean_identifier}"
        )

        if not observations_data:
            return f"No observations found for patient {clean_identifier}"

        # Deduplicate and limit display for large result sets
        deduplicated = deduplicate_observations(observations_data)
        display_count = min(len(deduplicated), 20)  # Show max 20 for all observations

        # Format observations with improved formatting
        formatted_observations = []
        for i, observation in enumerate(deduplicated[:display_count], 1):
            # Extract observation type for better rounding
            obs_type = observation.get("code_display", "")
            formatted_obs = format_observation_summary(observation, obs_type)
            formatted_observations.append(f"{i}. {formatted_obs}")

        result = (
            f"Patient {clean_identifier} has {len(deduplicated)} observation(s)"
            + (
                f" (showing {display_count} most recent):"
                if len(deduplicated) > display_count
                else ":"
            )
            + "\n\n"
            + "\n".join(formatted_observations)
        )

        if len(deduplicated) > display_count:
            result += (
                f"\n\n... and {len(deduplicated) - display_count} more observation(s)"
            )

        return result

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
        if clean_observation_type.startswith('"') and clean_observation_type.endswith(
            '"'
        ):
            clean_observation_type = clean_observation_type[1:-1]
        elif clean_observation_type.startswith("'") and clean_observation_type.endswith(
            "'"
        ):
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

        # Format observations with summary statistics
        return format_observations_with_summary(
            observations_data,
            clean_observation_type,
            clean_identifier,
            max_display=15,
        )

    except Exception as e:
        return f"Error retrieving {observation_type} observations for patient {patient_identifier}: {str(e)}"


# ============================================================================
# Modular Helper Functions for Observation Formatting
# ============================================================================


def round_clinical_value(value: float, observation_type: Optional[str] = None) -> float:
    """
    Round clinical values to appropriate precision based on observation type.

    Args:
        value: The numeric value to round
        observation_type: Optional observation type name for type-specific rounding

    Returns:
        Rounded value with appropriate decimal places
    """
    if value is None:
        return value

    # Type-specific rounding rules
    if observation_type:
        obs_lower = observation_type.lower()

        # Integer values (no decimals needed)
        if any(term in obs_lower for term in ["count", "number", "score", "index"]):
            return round(value)

        # One decimal place (most clinical measurements)
        if any(
            term in obs_lower
            for term in [
                "glucose",
                "cholesterol",
                "hemoglobin",
                "pressure",
                "bmi",
                "weight",
                "height",
            ]
        ):
            return round(value, 1)

        # Two decimal places (very precise measurements)
        if any(term in obs_lower for term in ["ratio", "percentage", "concentration"]):
            return round(value, 2)

    # Default: 1 decimal place for most clinical values
    return round(value, 1)


def format_clinical_date(date_value: Any, include_time: bool = False) -> str:
    """
    Format dates in a more readable clinical format.

    Args:
        date_value: Date string, datetime object, or None
        include_time: Whether to include time in the output

    Returns:
        Formatted date string
    """
    if not date_value:
        return "Date not available"

    try:
        # Parse string date
        if isinstance(date_value, str):
            # Try parsing ISO format with time
            if "T" in date_value or " " in date_value:
                dt = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            else:
                # Date only
                dt = datetime.strptime(date_value, "%Y-%m-%d")
        elif isinstance(date_value, datetime):
            dt = date_value
        else:
            return str(date_value)

        # Format based on how recent it is
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        days_diff = (
            (now - dt.replace(tzinfo=None)).days if dt.tzinfo else (now - dt).days
        )

        # Recent dates (within last year): "Sep 6, 2019"
        if days_diff < 365:
            if include_time and dt.hour != 0 and dt.minute != 0:
                return dt.strftime("%b %d, %Y %I:%M %p")
            return dt.strftime("%b %d, %Y")
        else:
            # Older dates: "2019-09-06"
            if include_time and dt.hour != 0 and dt.minute != 0:
                return dt.strftime("%Y-%m-%d %H:%M")
            return dt.strftime("%Y-%m-%d")

    except (ValueError, TypeError):
        return str(date_value)


def calculate_observation_stats(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics for a list of observations.

    Args:
        observations: List of observation dictionaries

    Returns:
        Dictionary with stats: latest, min, max, average, count, unit
    """
    if not observations:
        return {}

    numeric_values = []
    latest_value = None
    latest_date = None
    unit = None

    for obs in observations:
        value_quantity = obs.get("value_quantity")
        effective_time = obs.get("effective_time")

        if value_quantity is not None:
            try:
                numeric_values.append(float(value_quantity))
                unit = obs.get("value_unit", unit)

                # Track latest value
                if effective_time:
                    if latest_date is None:
                        latest_value = value_quantity
                        latest_date = effective_time
                    else:
                        # Compare dates to find latest
                        try:
                            if isinstance(effective_time, str):
                                obs_date = datetime.fromisoformat(
                                    effective_time.replace("Z", "+00:00")
                                )
                            else:
                                obs_date = effective_time

                            if isinstance(latest_date, str):
                                latest_date_obj = datetime.fromisoformat(
                                    latest_date.replace("Z", "+00:00")
                                )
                            else:
                                latest_date_obj = latest_date

                            if obs_date > latest_date_obj:
                                latest_value = value_quantity
                                latest_date = effective_time
                        except (ValueError, TypeError):
                            pass
            except (ValueError, TypeError):
                continue

    if not numeric_values:
        return {"count": len(observations)}

    stats = {
        "count": len(observations),
        "latest": (
            round_clinical_value(latest_value) if latest_value is not None else None
        ),
        "latest_date": format_clinical_date(latest_date) if latest_date else None,
        "min": round_clinical_value(min(numeric_values)),
        "max": round_clinical_value(max(numeric_values)),
        "average": round_clinical_value(sum(numeric_values) / len(numeric_values)),
        "unit": unit or "",
    }

    return stats


def deduplicate_observations(
    observations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Remove duplicate observations based on value, date, and type.

    Args:
        observations: List of observation dictionaries

    Returns:
        Deduplicated list of observations
    """
    seen = set()
    deduplicated = []

    for obs in observations:
        # Create a key from value, date, and code
        value = obs.get("value_quantity") or obs.get("value_string", "")
        date = obs.get("effective_time", "")
        code = obs.get("code", "")

        key = (value, date, code)

        if key not in seen:
            seen.add(key)
            deduplicated.append(obs)

    return deduplicated


def format_observation_summary(
    observation_data: Dict[str, Any], observation_type: Optional[str] = None
) -> str:
    """
    Format observation data into a human-readable summary.

    Args:
        observation_data: Dictionary containing observation data
        observation_type: Optional observation type for value rounding

    Returns:
        Formatted observation string
    """
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

    # Determine the value to display with proper rounding
    if value_quantity is not None:
        rounded_value = round_clinical_value(
            float(value_quantity), observation_type or code_display
        )
        value_str = f"{rounded_value} {value_unit}".strip()
    elif value_string:
        value_str = value_string
    else:
        value_str = "No value recorded"

    # Format date using improved date formatter
    effective_time = observation_data.get("effective_time")
    date_str = format_clinical_date(effective_time, include_time=False)

    # Format with code if available
    code_info = f" ({code})" if code else ""

    return f"{code_display}{code_info}: {value_str} | {date_str} | {status}"


def format_observations_with_summary(
    observations: List[Dict[str, Any]],
    observation_type: str,
    patient_identifier: str,
    max_display: int = 15,
) -> str:
    """
    Format observations with summary statistics and limited display.

    Args:
        observations: List of observation dictionaries
        observation_type: Type of observation (e.g., "glucose", "hemoglobin")
        patient_identifier: Patient ID or identifier
        max_display: Maximum number of observations to display (default: 15)

    Returns:
        Formatted string with summary and observations
    """
    if not observations:
        return f"No {observation_type} observations found for patient {patient_identifier}."

    # Deduplicate observations
    deduplicated = deduplicate_observations(observations)

    # Calculate statistics
    stats = calculate_observation_stats(deduplicated)

    # Build result string
    result_parts = []

    # Header
    result_parts.append(
        f"Patient {patient_identifier} has {stats.get('count', len(deduplicated))} {observation_type} observation(s):"
    )

    # Summary statistics (if we have numeric values)
    if stats.get("latest") is not None:
        result_parts.append("\n📊 Summary:")
        result_parts.append(
            f"   Latest: {stats['latest']} {stats.get('unit', '')} ({stats.get('latest_date', 'N/A')})"
        )

        if stats.get("min") is not None and stats.get("max") is not None:
            result_parts.append(
                f"   Range: {stats['min']} - {stats['max']} {stats.get('unit', '')}"
            )

        if stats.get("average") is not None:
            result_parts.append(
                f"   Average: {stats['average']} {stats.get('unit', '')}"
            )

    # Format observations (limited display)
    display_count = min(len(deduplicated), max_display)
    result_parts.append(
        f"\n📋 Recent readings (showing {display_count} of {len(deduplicated)}):"
    )

    for i, observation in enumerate(deduplicated[:display_count], 1):
        formatted_obs = format_observation_summary(observation, observation_type)
        result_parts.append(f"{i}. {formatted_obs}")

    if len(deduplicated) > display_count:
        result_parts.append(
            f"\n... and {len(deduplicated) - display_count} more observation(s)"
        )

    return "\n".join(result_parts)
