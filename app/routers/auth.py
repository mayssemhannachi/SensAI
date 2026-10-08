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
from app.core.security import decode_token
from app.schemas.auth_schema import ActivateRequest
from app.services.activation_code_service import activate_patient_account

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

        payload = decode_token(token) or {}
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": payload.get("role"),
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
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.user import User

    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    return {**current_user, "full_name": user.full_name if user else None}



@router.post(
    "/activate",
    response_model=TokenResponse,
    status_code=201,
    summary="Activer un compte patient",
    description=(
        "Crée les identifiants du patient (ou de son parent) à partir du code d’activation "
        "fourni par le thérapeute, puis renvoie directement un jeton de connexion."
    ),
    responses={
        404: {"description": "Code non reconnu."},
        409: {"description": "Code déjà utilisé ou e-mail déjà pris."},
        410: {"description": "Code expiré."},
    },
)
def activate(request: ActivateRequest, db: Session = Depends(get_db)):
    token = activate_patient_account(db, request.code, request.email, request.password)
    return {"access_token": token, "token_type": "bearer", "role": "patient"}
