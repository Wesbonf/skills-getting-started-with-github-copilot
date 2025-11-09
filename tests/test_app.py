import copy

from fastapi.testclient import TestClient
import pytest

from src.app import app, activities


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    # Preserve original in-memory activities and restore after each test
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # some known activities from the seed data
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_signup_and_reflected_in_get():
    email = "tester@example.com"
    activity = "Chess Club"

    # ensure clean state
    assert email not in activities[activity]["participants"]

    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body["message"]

    # GET should reflect the new participant
    resp2 = client.get("/activities")
    data = resp2.json()
    assert email in data[activity]["participants"]


def test_signup_duplicate_fails():
    email = "dup@example.com"
    activity = "Programming Class"

    r1 = client.post(f"/activities/{activity}/signup?email={email}")
    assert r1.status_code == 200

    r2 = client.post(f"/activities/{activity}/signup?email={email}")
    assert r2.status_code == 400


def test_capacity_enforced():
    activity = "Temp Capacity"
    activities[activity] = {
        "description": "temp",
        "schedule": "now",
        "max_participants": 1,
        "participants": [],
    }

    r1 = client.post(f"/activities/{activity}/signup?email=one@example.com")
    assert r1.status_code == 200

    r2 = client.post(f"/activities/{activity}/signup?email=two@example.com")
    assert r2.status_code == 400


def test_unregister_removes_participant():
    email = "remove_me@example.com"
    activity = "Soccer Team"

    # ensure the participant is signed up
    if email not in activities[activity]["participants"]:
        r = client.post(f"/activities/{activity}/signup?email={email}")
        assert r.status_code == 200

    # unregister
    r2 = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert r2.status_code == 200
    assert email not in activities[activity]["participants"]


def test_unregister_missing_returns_404():
    r = client.delete("/activities/Chess%20Club/unregister?email=notfound@example.com")
    assert r.status_code == 404
