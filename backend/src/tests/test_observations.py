from datetime import datetime


def ensure_patient(client) -> int:
    """Helper to ensure a patient exists for testing."""
    # Try to get existing patient
    r = client.get("/api/v2/patients?limit=1")
    if r.status_code == 200 and r.json():
        return r.json()[0]["id"]
    # Create one if needed
    payload = {
        "first_name": "Test",
        "last_name": "Patient",
        "birth_date": "1990-01-01",
    }
    r = client.post("/api/v2/patients", json=payload)
    if r.status_code == 201:
        return r.json()["id"]
    # Fallback: return first patient ID
    r2 = client.get("/api/v2/patients?limit=1")
    return r2.json()[0]["id"]


def test_list_observations_ok(client):
    """Test listing observations returns 200 and list."""
    r = client.get("/api/v2/observations?limit=5")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_filter_observations_by_patient_id(client):
    """Test filtering observations by patient_id."""
    patient_id = ensure_patient(client)
    r = client.get(f"/api/v2/observations?patient_id={patient_id}&limit=10")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    for item in items:
        assert item["patient_id"] == patient_id


def test_filter_observations_by_code_display(client):
    """Test filtering observations by code_display (observation type)."""
    patient_id = ensure_patient(client)
    r = client.get(f"/api/v2/observations?patient_id={patient_id}&code_display=glucose")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    # Verify all results contain "glucose" in code_display (case-insensitive)
    for item in items:
        code_display = item.get("code_display", "").lower()
        assert (
            "glucose" in code_display
        ), f"Expected 'glucose' in code_display, got: {code_display}"


def test_filter_observations_by_code(client):
    """Test filtering observations by LOINC code."""
    patient_id = ensure_patient(client)
    # Use a common LOINC code (glucose: 2339-0)
    r = client.get(f"/api/v2/observations?patient_id={patient_id}&code=2339-0")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    # Verify all results contain the code
    for item in items:
        code = item.get("code", "")
        assert "2339-0" in code, f"Expected '2339-0' in code, got: {code}"


def test_observations_sorted_by_date(client):
    """Test that observations are sorted by effective_time (most recent first)."""
    patient_id = ensure_patient(client)
    r = client.get(
        f"/api/v2/observations?patient_id={patient_id}&code_display=glucose&limit=10"
    )
    assert r.status_code == 200
    items = r.json()

    if len(items) > 1:
        # Extract dates (skip None values)
        dates = []
        for item in items:
            effective_time = item.get("effective_time")
            if effective_time:
                # Handle both string and datetime formats
                if isinstance(effective_time, str):
                    # Remove 'Z' and handle timezone
                    dt_str = effective_time.replace("Z", "+00:00")
                    dates.append(datetime.fromisoformat(dt_str))
                else:
                    dates.append(effective_time)

        if len(dates) > 1:
            # Verify descending order (most recent first)
            for i in range(len(dates) - 1):
                assert dates[i] >= dates[i + 1], (
                    f"Observations should be sorted by date (most recent first). "
                    f"Date {i}: {dates[i]}, Date {i+1}: {dates[i+1]}"
                )


def test_observation_response_format(client):
    """Test that observation response includes all required fields."""
    r = client.get("/api/v2/observations?limit=1")
    assert r.status_code == 200
    items = r.json()

    if items:
        obs = items[0]
        # Verify required fields exist
        assert "id" in obs, "Observation should have 'id' field"
        assert "patient_id" in obs, "Observation should have 'patient_id' field"
        assert "code" in obs, "Observation should have 'code' field"
        assert "status" in obs, "Observation should have 'status' field"
        # Verify optional but important fields are present (even if None)
        assert "code_display" in obs, "Observation should have 'code_display' field"
        assert (
            "value_quantity" in obs or "value_string" in obs
        ), "Observation should have either 'value_quantity' or 'value_string'"
        assert "effective_time" in obs, "Observation should have 'effective_time' field"


def test_get_observation_by_id(client):
    """Test getting a single observation by ID."""
    # First get a list to find an ID
    r = client.get("/api/v2/observations?limit=1")
    assert r.status_code == 200
    items = r.json()

    if items:
        obs_id = items[0]["id"]
        r2 = client.get(f"/api/v2/observations/{obs_id}")
        assert r2.status_code == 200
        body = r2.json()
        assert body["id"] == obs_id
        # Verify it has the same structure
        assert "patient_id" in body
        assert "code" in body
        assert "status" in body
    else:
        # Skip if no observations exist (test passes)
        pass


def test_filter_observations_combined_filters(client):
    """Test combining multiple filters (patient_id + code_display)."""
    patient_id = ensure_patient(client)
    r = client.get(
        f"/api/v2/observations?patient_id={patient_id}&code_display=hemoglobin&limit=5"
    )
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    # Verify all results match both filters
    for item in items:
        assert item["patient_id"] == patient_id
        code_display = item.get("code_display", "").lower()
        assert "hemoglobin" in code_display


def test_filter_observations_case_insensitive(client):
    """Test that code_display filter is case-insensitive."""
    patient_id = ensure_patient(client)
    # Test with different cases
    r1 = client.get(
        f"/api/v2/observations?patient_id={patient_id}&code_display=GLUCOSE"
    )
    r2 = client.get(
        f"/api/v2/observations?patient_id={patient_id}&code_display=glucose"
    )
    r3 = client.get(
        f"/api/v2/observations?patient_id={patient_id}&code_display=Glucose"
    )

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 200

    # All should return the same results (case-insensitive)
    items1 = r1.json()
    items2 = r2.json()
    items3 = r3.json()

    # Compare counts (should be same)
    assert (
        len(items1) == len(items2) == len(items3)
    ), "Case-insensitive filtering should return same results"
