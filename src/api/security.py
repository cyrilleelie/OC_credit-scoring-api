# src/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

# On importe les modèles et la configuration
from ..database import models, schemas
from ..config import settings

# Configuration du hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth")

# --- Fonctions de Hachage ---
def verify_password(plain_password, hashed_password):
    """Vérifie si un mot de passe en clair correspond à un mot de passe haché."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Génère le hachage d'un mot de passe."""
    return pwd_context.hash(password)

# --- Logique d'Authentification Basée sur la BDD ---
def get_user(db: Session, username: str):
    """Récupère un utilisateur depuis la BDD par son nom d'utilisateur."""
    return db.query(models.User).filter(models.User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    """Vérifie si un utilisateur existe et si le mot de passe est correct."""
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password) or user.disabled:
        return None
    return user

# --- Fonctions de Gestion du Token JWT ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un nouveau token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt