# src/main.py

from jose import JWTError, jwt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import joblib
import pandas as pd

# On importe tous les composants nécessaires depuis nos modules locaux
from ..database import models, schemas
from . import security
from ..database.database import get_db
from ..config import settings

# --- Initialisation ---
app = FastAPI(title="API de Scoring Crédit", version="1.0")

# Charger le modèle au démarrage de l'API
model = joblib.load(settings.model_path)

# --- Dépendances ---
async def get_current_active_user(
    token: str = Depends(security.oauth2_scheme), 
    db: Session = Depends(get_db)
) -> models.User:
    """
    Dépendance pour obtenir l'utilisateur actuel à partir du token JWT.
    Injecte la session de base de données pour vérifier l'utilisateur.
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
        token_data = schemas.TokenData(username=username)
    except jwt.JWTError:
        raise credentials_exception
    
    user = security.get_user(db, username=token_data.username)
    if user is None or user.disabled:
        raise credentials_exception
    return user


# --- Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Credit Scoring API"}

@app.post("/auth", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint pour s'authentifier et recevoir un token JWT.
    """
    user = security.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/predict/{client_id}", response_model=schemas.PredictionResponse)
def predict(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Endpoint pour obtenir une prédiction de score pour un client donné.
    Protégé par authentification.
    """
    db_client = db.query(models.TestData).filter(models.TestData.sk_id_curr == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client ID not found")
        
    client_data = pd.DataFrame([db_client.data])
    
    # S'assurer que les colonnes du modèle sont présentes
    client_data = client_data.reindex(columns=model.feature_names_in_, fill_value=0)
    
    prediction_proba = model.predict_proba(client_data)[:, 1][0]
    
    decision = "Crédit Accordé" if prediction_proba < settings.decision_threshold else "Crédit Refusé"
    
    return {
        "client_id": client_id,
        "prediction_probability": prediction_proba,
        "prediction_decision": decision
    }