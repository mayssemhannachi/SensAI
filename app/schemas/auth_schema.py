from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str | None = None


class ActivateRequest(BaseModel):
    code: str
    email: EmailStr
    password: str


class UserRegistrationResponse(BaseModel):
    message: str
    user_id: int


class CurrentUserResponse(BaseModel):
    user_id: int
    sub: EmailStr
    role: str
    full_name: str | None = None
    patient_id: int | None = None