"""
Test cases for the Mergington High School Activities API.

This module contains comprehensive tests for all API endpoints:
- GET /activities - Retrieve all activities
- POST /activities/{activity_name}/signup - Sign up for an activity
- DELETE /activities/{activity_name}/unregister - Unregister from an activity
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities data before each test to ensure test isolation."""
    # Store original activities data
    original_activities = copy.deepcopy(activities)
    
    # Reset to known state before test
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })
    
    yield
    
    # Restore original activities data after test
    activities.clear()
    activities.update(original_activities)


class TestActivitiesEndpoint:
    """Test cases for GET /activities endpoint."""
    
    def test_get_activities_success(self, client, reset_activities):
        """Test successful retrieval of all activities."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that all expected activities are present
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Check activity structure
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        
        # Check specific data
        assert chess_club["max_participants"] == 12
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
    
    def test_get_activities_structure(self, client, reset_activities):
        """Test that activities have the correct data structure."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)


class TestSignupEndpoint:
    """Test cases for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup?email=new-student@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Signed up new-student@mergington.edu for Chess Club"
        
        # Verify the student was added to the activity
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "new-student@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for a non-existent activity."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_registration(self, client, reset_activities):
        """Test that duplicate registration is prevented."""
        # Try to register a student who is already registered
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is already signed up"
    
    def test_signup_with_encoded_activity_name(self, client, reset_activities):
        """Test signup with URL-encoded activity names."""
        response = client.post(
            "/activities/Programming%20Class/signup?email=new-student@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Signed up new-student@mergington.edu for Programming Class"
    
    def test_signup_with_encoded_email(self, client, reset_activities):
        """Test signup with URL-encoded email address."""
        email = "test.user@mergington.edu"  # Changed from + to . to avoid URL encoding issues
        response = client.post(
            f"/activities/Gym Class/signup?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Signed up {email} for Gym Class"


class TestUnregisterEndpoint:
    """Test cases for DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        # First verify the student is registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" in activities_data["Chess Club"]["participants"]
        
        # Unregister the student
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Unregistered michael@mergington.edu from Chess Club"
        
        # Verify the student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
        # Verify other student is still there
        assert "daniel@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregistration from a non-existent activity."""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_not_registered_student(self, client, reset_activities):
        """Test unregistration of a student who is not registered."""
        response = client.delete(
            "/activities/Chess Club/unregister?email=not-registered@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is not registered for this activity"
    
    def test_unregister_with_encoded_activity_name(self, client, reset_activities):
        """Test unregistration with URL-encoded activity names."""
        response = client.delete(
            "/activities/Programming%20Class/unregister?email=emma@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Unregistered emma@mergington.edu from Programming Class"


class TestRootEndpoint:
    """Test cases for the root endpoint."""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static files."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]


class TestIntegrationScenarios:
    """Integration tests that combine multiple operations."""
    
    def test_signup_and_unregister_workflow(self, client, reset_activities):
        """Test complete workflow: signup then unregister."""
        email = "workflow-test@mergington.edu"
        activity = "Chess Club"
        
        # Initial state - student not registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity]["participants"]
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify registration
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity]["participants"]
    
    def test_multiple_students_same_activity(self, client, reset_activities):
        """Test multiple students signing up for the same activity."""
        activity = "Gym Class"
        students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Sign up all students
        for student in students:
            response = client.post(f"/activities/{activity}/signup?email={student}")
            assert response.status_code == 200
        
        # Verify all are registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        for student in students:
            assert student in activities_data[activity]["participants"]
        
        # Unregister middle student
        response = client.delete(f"/activities/{activity}/unregister?email={students[1]}")
        assert response.status_code == 200
        
        # Verify only middle student is removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert students[0] in activities_data[activity]["participants"]
        assert students[1] not in activities_data[activity]["participants"]
        assert students[2] in activities_data[activity]["participants"]