# src/main.py

import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
import os
import json
from datetime import datetime
import time
import warnings

# Ignorer les warnings de scikit-learn pour une sortie plus propre
warnings.filterwarnings("ignore", category=UserWarning, module='sklearn')

# --- Configuration et chargement des ressources ---

# 1. Configuration de la base de données
DB_USER = "user"
DB_PASSWORD = "password"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "credit_scoring"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 2. Chargement du modèle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, '..', 'model_artifacts', 'credit_scoring_model.joblib')
try:
    model = joblib.load(MODEL_PATH)
    print("Modèle chargé avec succès.")
except Exception as e:
    print(f"Erreur critique lors du chargement du modèle : {e}")
    model = None

# 3. Connexion à la base de données
try:
    engine = create_engine(DATABASE_URL)
    print("Connexion à la base de données établie.")
except Exception as e:
    print(f"Erreur critique de connexion à la base de données : {e}")
    engine = None

# 4. Initialisation de l'API FastAPI
app = FastAPI(
    title="API de Scoring Crédit",
    description="API pour prédire la probabilité de défaut de paiement à partir d'un ID client.",
    version="2.0.0"
)

# --- Endpoints de l'API ---

@app.get("/")
def read_root():
    """Endpoint racine qui retourne un message de bienvenue."""
    return {"message": "Bienvenue sur l'API de Scoring Crédit v2."}

@app.post("/predict/{client_id}")
def predict(client_id: int):
    """
    Prédit le score pour un client donné à partir de son ID.
    """
    if model is None or engine is None:
        raise HTTPException(status_code=503, detail="Service non disponible: Modèle ou base de données non initialisé.")

    start_time = time.time()
    request_timestamp = datetime.now()

    try:
        # 1. Récupérer les données du client depuis la BDD
        with engine.connect() as connection:
            query = text("SELECT data FROM test_data WHERE sk_id_curr = :client_id")
            result = connection.execute(query, {"client_id": client_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Client ID {client_id} non trouvé.")
            
        client_data_json = result[0]
        
        # 2. Préparer les données pour le modèle
        features_df = pd.DataFrame([client_data_json])
        model_features = model.named_steps['imputer'].feature_names_in_
        features_df = features_df.reindex(columns=model_features)
        
        # 3. Faire la prédiction
        prediction_proba = model.predict_proba(features_df)[:, 1]
        score = prediction_proba[0]
        
        # 4. Préparer et enregistrer le log
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

        # 5. Retourner le résultat
        return {
            "client_id": client_id,
            "prediction_probability": float(score),
            "prediction_decision": "Défaut de paiement probable" if decision else "Remboursement probable",
            "threshold": 0.5
        }

    except Exception as e:
        # Log de l'erreur interne
        print(f"Erreur interne du serveur pour le client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur lors de la prédiction.")

