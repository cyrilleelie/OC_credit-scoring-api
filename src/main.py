# src/main.py

import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import time
import json
import warnings

# Importer les modules locaux
from src import security
from config import settings

warnings.filterwarnings("ignore", category=UserWarning, module='sklearn')

# --- Chargement des ressources ---
model = joblib.load(settings.model_artifacts_path)
engine = create_engine(settings.database_url)

app = FastAPI(
    title="API de Scoring Crédit",
    description="API sécurisée pour prédire la probabilité de défaut de paiement.",
    version="2.2.0"
)

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de Scoring Crédit v2.2."}

@app.post("/auth")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint pour s'authentifier et recevoir un token JWT."""
    user = security.get_user(form_data.username)
    if not user or not security.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = security.create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/predict/{client_id}")
def predict(client_id: int, current_user: dict = Depends(security.get_current_active_user)):
    """Prédit le score pour un client. Endpoint protégé."""
    start_time = time.time()
    request_timestamp = datetime.now()

    with engine.connect() as connection:
        query = text("SELECT data FROM test_data WHERE sk_id_curr = :client_id")
        result = connection.execute(query, {"client_id": client_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Client ID {client_id} non trouvé.")
    
    client_data_json = result[0]
    
    try:
        features_df = pd.DataFrame([client_data_json])
        model_features = model.named_steps['imputer'].feature_names_in_
        features_df = features_df.reindex(columns=model_features)
        
        prediction_proba = model.predict_proba(features_df)[:, 1]
        score = prediction_proba[0]
        
        decision = bool(score > 0.5)
        end_time = time.time()
        inference_time_ms = (end_time - start_time) * 1000
        response_timestamp = datetime.now()

        log_entry = {
            "request_timestamp": request_timestamp, "client_id": client_id,
            "input_data": json.dumps(client_data_json), "prediction_proba": float(score),
            "prediction_decision": decision, "response_timestamp": response_timestamp,
            "inference_time_ms": inference_time_ms, "http_status_code": 200
        }
        
        with engine.connect() as connection:
            query = text("""
                INSERT INTO api_logs (request_timestamp, client_id, input_data, prediction_proba, prediction_decision, response_timestamp, inference_time_ms, http_status_code)
                VALUES (:request_timestamp, :client_id, :input_data, :prediction_proba, :prediction_decision, :response_timestamp, :inference_time_ms, :http_status_code);
            """)
            connection.execute(query, log_entry)
            connection.commit()

        return {
            "client_id": client_id,
            "prediction_probability": float(score),
            "prediction_decision": "Défaut de paiement probable" if decision else "Remboursement probable",
            "threshold": 0.5
        }

    except Exception as e:
        print(f"Erreur interne du serveur pour le client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur lors de la prédiction.")
