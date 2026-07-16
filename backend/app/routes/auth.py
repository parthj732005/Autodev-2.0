# backend/app/routes/auth.py

from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
def login():
    # TEMP: fake login
    return {
        "user": {
            "id": 1,
            "name": "Demo User"
        }
    }

@router.post("/logout")
def logout():
    return {"status": "logged out"}
