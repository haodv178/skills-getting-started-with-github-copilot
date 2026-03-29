import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)

INITIAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state before each test."""
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))
    yield


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(INITIAL_ACTIVITIES)
    assert "Chess Club" in data


def test_get_activities_structure():
    response = client.get("/activities")
    activity = response.json()["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    response = client.post("/activities/Chess Club/signup?email=new@mergington.edu")
    assert response.status_code == 200
    assert "new@mergington.edu" in response.json()["message"]
    assert "new@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_unknown_activity():
    response = client.post("/activities/Unknown Activity/signup?email=new@mergington.edu")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_duplicate_participant():
    existing_email = activities["Chess Club"]["participants"][0]
    response = client.post(f"/activities/Chess Club/signup?email={existing_email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_activity_full():
    activity = activities["Chess Club"]
    activity["participants"] = [
        f"student{i}@mergington.edu" for i in range(activity["max_participants"])
    ]
    response = client.post("/activities/Chess Club/signup?email=overflow@mergington.edu")
    assert response.status_code == 400
    assert "full" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success():
    existing_email = activities["Chess Club"]["participants"][0]
    response = client.delete(f"/activities/Chess Club/signup?email={existing_email}")
    assert response.status_code == 200
    assert existing_email not in activities["Chess Club"]["participants"]


def test_unregister_unknown_activity():
    response = client.delete("/activities/Unknown Activity/signup?email=any@mergington.edu")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_participant_not_signed_up():
    response = client.delete("/activities/Chess Club/signup?email=nobody@mergington.edu")
    assert response.status_code == 404
    assert "not signed up" in response.json()["detail"].lower()
