from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import secrets
from datetime import datetime, timedelta, timezone
from app.services.email_service import send_reset_password_email

from app.core.config import FRONTEND_URL, GOOGLE_REDIRECT_URI, ENVIRONMENT, ADMIN_EMAIL
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    get_current_user,
)
from app.db.database import get_db
from app.models.utilisateur import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.google_oauth import oauth, get_or_create_user, generate_unique_username

router = APIRouter(prefix="/auth", tags=["auth"])


def set_auth_cookie(response: Response, user_id: int) -> None:
    access_token = create_access_token(user_id)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=ENVIRONMENT == "production",
        samesite="lax",
        max_age=60 * 60 * 24,
        path="/",
    )


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cette adresse e-mail.",
        )

    base_username = payload.email.split("@")[0]
    username = generate_unique_username(db, base_username)
    full_name = f"{payload.firstName} {payload.lastName}".strip()

    new_user = User(
        username=username,
        email=payload.email,
        full_name=full_name,
        password_hash=hash_password(payload.password),
        role="admin" if ADMIN_EMAIL and payload.email == ADMIN_EMAIL else "user",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    set_auth_cookie(response, new_user.id)
    return {"user": new_user}


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou mot de passe incorrect.",
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou mot de passe incorrect.",
        )

    set_auth_cookie(response, user.id)
    return {"user": user}


@router.get("/google")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")

    if not userinfo:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=google_auth_failed")

    user = get_or_create_user(
        db,
        google_id=userinfo["sub"],
        email=userinfo["email"],
        full_name=userinfo.get("name", ""),
    )

    response = RedirectResponse(FRONTEND_URL)
    set_auth_cookie(response, user.id)
    return response


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(minutes=5)
        db.commit()

        reset_link = f"{FRONTEND_URL}/reinitialiser-mot-de-passe/{token}"
        send_reset_password_email(user.email, reset_link)

    return {"message": "Si cet e-mail existe, un lien de réinitialisation a été envoyé."}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"message": "Déconnecté avec succès."}


@router.post("/reset-password/{token}")
async def reset_password(token: str, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == token).first()

    if not user or not user.reset_token_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lien de réinitialisation invalide ou expiré.",
        )

    if user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lien de réinitialisation invalide ou expiré.",
        )

    user.password_hash = hash_password(payload.password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Mot de passe réinitialisé avec succès."}