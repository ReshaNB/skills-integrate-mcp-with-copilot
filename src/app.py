"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
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
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

# Simple authentication + role-based access control (RBAC)
#
# This is a minimal, self-contained implementation suitable for a small
# demo project. It uses HTTP Basic auth and an in-memory user store with
# roles. For production use, replace with a proper password-hashing
# strategy and persistent user storage.
security = HTTPBasic()
import hashlib
import secrets

# In-memory user store: username -> {password_hash, role}
# Passwords are stored as SHA-256 hex digests of the password string.
# Default seeded users (demo):
#  - admin / adminpass (role: admin)
#  - teacher / teacherpass (role: teacher)
users = {
    "admin": {
        "password_hash": hashlib.sha256(b"adminpass").hexdigest(),
        "role": "admin"
    },
    "teacher": {
        "password_hash": hashlib.sha256(b"teacherpass").hexdigest(),
        "role": "teacher"
    }
}


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored SHA-256 hex digest."""
    candidate_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return secrets.compare_digest(candidate_hash, password_hash)


def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Dependency to get the current authenticated user.

    Raises 401 if authentication fails.
    Returns a dict with keys `username` and `role` on success.
    """
    username = credentials.username
    password = credentials.password

    if username not in users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid authentication credentials",
                            headers={"WWW-Authenticate": "Basic"})

    user = users[username]
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid authentication credentials",
                            headers={"WWW-Authenticate": "Basic"})

    return {"username": username, "role": user["role"]}


def require_role(required_role: str):
    """Return a dependency that enforces the given role.

    Users with role 'admin' are allowed to perform any action.
    """
    def role_dependency(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role == "admin":
            return current_user
        if user_role != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Insufficient permissions")
        return current_user

    return role_dependency



@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


# Admin/teacher endpoints to manage activities (require authentication)


@app.post("/activities")
def create_activity(activity_name: str,
                    description: str,
                    schedule: str,
                    max_participants: int,
                    user: dict = Depends(require_role("teacher"))):
    """Create a new activity. Requires `teacher` role or `admin`."""
    if activity_name in activities:
        raise HTTPException(status_code=400, detail="Activity already exists")

    activities[activity_name] = {
        "description": description,
        "schedule": schedule,
        "max_participants": max_participants,
        "participants": []
    }
    return {"message": f"Created activity {activity_name}", "created_by": user["username"]}


@app.delete("/activities/{activity_name}")
def delete_activity(activity_name: str, user: dict = Depends(require_role("teacher"))):
    """Delete an activity. Requires `teacher` role or `admin`."""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    del activities[activity_name]
    return {"message": f"Deleted activity {activity_name}", "deleted_by": user["username"]}

