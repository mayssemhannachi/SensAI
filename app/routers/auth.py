from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.auth_schema import (
    RegisterRequest
)

from app.services.auth_service import (
    register_user
)

from app.schemas.auth_schema import (
    LoginRequest
)

from app.services.auth_service import (
    login_user
)
from app.services.auth_service import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
def register(
        request: RegisterRequest,
        db: Session = Depends(get_db)
):
    try:

        user = register_user(
            db,
            request.full_name,
            request.email,
            request.password
        )

        return {
            "message": "User registered",
            "user_id": user.id
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    try:

        token = login_user(
            db,
            request.email,
            request.password
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except ValueError as e:

        raise HTTPException(
            status_code=401,
            detail=str(e)
        )

#Route protégée
@router.get("/me")
def get_me(
    current_user=Depends(get_current_user)
):
    return current_user
