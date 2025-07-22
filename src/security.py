# src/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Importer la configuration centralisée
from config import settings

# --- Utilitaires ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")

# --- Base de données d'utilisateurs (simulation) ---
FAKE_USERS_DB = {
    "user_test": {
        "username": "user_test",
        "hashed_password": "$2b$12$eefAN9sSotQjW364tiaPM.dj9RV52vilKmHMx3zlvIu5UygZpGpJi",
        "disabled": False,
    }
}

# --- Fonctions ---

def verify_password(plain_password, hashed_password):
    """Vérifie si un mot de passe en clair correspond à un mot de passe hashé."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    """Récupère un utilisateur depuis notre fausse base de données."""
    if username in FAKE_USERS_DB:
        return FAKE_USERS_DB[username]
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un nouveau token d'accès JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_active_user(token: str = Depends(oauth2_scheme)):
    """
    Décode et valide le token JWT pour récupérer l'utilisateur actuel.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user(username)
    if user is None or user.get("disabled"):
        raise credentials_exception
    
    return user
