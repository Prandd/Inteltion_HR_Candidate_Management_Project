from fastapi import APIRouter, HTTPException

from ..auth import authenticate, create_access_token
from ..schemas import LoginRequest

router = APIRouter(tags=["auth"])


@router.post("/auth/login")
def login(payload: LoginRequest):
    """Single Admin/HR account. Returns a bearer token for /api/candidates/*."""
    if not authenticate(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(payload.username)
    return {
        "data": {"access_token": token, "token_type": "bearer"},
        "error": None,
    }
