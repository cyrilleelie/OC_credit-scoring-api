# src/api/main.py

from jose import JWTError, jwt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import time
import joblib
import pandas as pd

# On importe tous les composants nécessaires depuis nos modules locaux
from src.database import models, schemas
from src.api import security
from src.database.database import get_db
from src.config import settings

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
    except JWTError:
        raise credentials_exception
    
    user = security.get_user(db, username=token_data.username)
    if user is None or user.disabled:
        raise credentials_exception
    return user


# --- Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de Scoring Crédit"}

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
    Protégé par authentification et logue chaque appel.
    """
    request_time = datetime.now()
    
    db_client = db.query(models.ClientDataForTest).filter(models.ClientDataForTest.sk_id_curr == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail=f"Client ID {client_id} non trouvé.")
        
    client_data_dict = db_client.data
    client_data_df = pd.DataFrame([client_data_dict])
    
    # S'assurer que les colonnes du modèle sont présentes
    client_data_df = client_data_df.reindex(columns=model.feature_names_in_, fill_value=0)
    
    # --- Début de la mesure du temps d'inférence ---
    start_time = time.time()
    
    # La sortie de predict_proba est un type numpy.float64
    prediction_proba_numpy = model.predict_proba(client_data_df)[:, 1][0]
    # On le convertit en float Python standard pour la BDD
    prediction_proba = float(prediction_proba_numpy)
    
    end_time = time.time()
    # --- Fin de la mesure ---
    inference_time_ms = (end_time - start_time) * 1000
    
    decision = "Crédit Accordé" if prediction_proba < settings.decision_threshold else "Crédit Refusé"
    
    # --- Logique de Logging ---
    try:
        log_entry = models.ApiLog(
            request_timestamp=request_time,
            client_id=client_id,
            input_data=client_data_dict,
            prediction_proba=prediction_proba,
            prediction_decision=decision,
            inference_time_ms=inference_time_ms,
            http_status_code=200
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"ERREUR lors de l'enregistrement du log : {e}")
        db.rollback()
    # --- Fin de la logique de Logging ---
    
    return {
        "client_id": client_id,
        "prediction_probability": prediction_proba,
        "prediction_decision": decision
    }
