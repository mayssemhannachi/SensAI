from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.auth_schema import (
    CurrentUserResponse,
    RegisterRequest,
    TokenResponse,
    UserRegistrationResponse,
)

from app.services.auth_service import (
    register_user
)

from app.schemas.auth_schema import LoginRequest

from app.services.auth_service import (
    login_user
)
from app.services.auth_service import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    status_code=201,
    summary="Créer un compte thérapeute",
    description="Crée un compte thérapeute à partir du nom, de l’adresse e-mail et du mot de passe.",
    response_description="Confirmation de création du compte.",
    responses={400: {"description": "Cette adresse e-mail est déjà utilisée."}},
)
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

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Se connecter",
    description="Échange les identifiants du thérapeute contre un jeton d’accès Bearer.",
    response_description="Le jeton d’accès et son type.",
    responses={401: {"description": "Identifiants invalides."}},
)
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
@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Afficher le compte connecté",
    description="Retourne les informations d’identité présentes dans le jeton d’accès.",
    response_description="L’identité du compte authentifié.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}},
)
def get_me(
    current_user=Depends(get_current_user)
):
    return current_user
