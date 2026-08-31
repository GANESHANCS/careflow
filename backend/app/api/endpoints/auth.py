from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.core.security import verify_password, create_access_token
from backend.app.core.rate_limit import login_rate_limiter
from backend.app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from backend.app.api.deps import get_current_active_user

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user via username/email and password. Returns signed JWT access token.
    Protected by rate limiting against brute force attempts.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"login:{client_ip}:{login_data.username}"

    if not login_rate_limiter.is_allowed(rate_limit_key, max_requests=5, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    # Allow login via username or email
    user = db.query(User).filter(
        (User.username == login_data.username) | (User.email == login_data.username)
    ).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated"
        )

    access_token = create_access_token(subject=user.id, role=user.role)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get profile information of currently authenticated user.
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_active_user)):
    """
    Stateless logout endpoint. Client removes stored token upon calling this endpoint.
    """
    return {"message": f"User {current_user.username} logged out successfully"}
