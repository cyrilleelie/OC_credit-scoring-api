# src/main.py

import pandas as pd
import joblib
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict # Import de ConfigDict
import uvicorn
import os

# 1. Initialisation de l'API FastAPI
app = FastAPI(
    title="API de Scoring Crédit",
    description="Une API pour prédire la probabilité de défaut de paiement d'un client.",
    version="1.0.0"
)

# 2. Définition du modèle de données d'entrée (Syntaxe Pydantic V2)
class ClientFeatures(BaseModel):
    # Utilisation de ConfigDict pour la configuration
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "EXT_SOURCE_2": 0.262949,
                "EXT_SOURCE_3": 0.139376,
                "DAYS_BIRTH": -20775,
                "DAYS_EMPLOYED": -1676.0,
                "PAYMENT_RATE": 0.057470,
                "AMT_ANNUITY": 24700.5,
                "AMT_CREDIT": 406597.5,
                "DAYS_ID_PUBLISH": -2120
            }
        }
    )
    
    EXT_SOURCE_2: float = 0.262949
    EXT_SOURCE_3: float = 0.139376
    DAYS_BIRTH: int = -20775
    DAYS_EMPLOYED: float = -1676.0
    PAYMENT_RATE: float = 0.057470
    AMT_ANNUITY: float = 24700.5
    AMT_CREDIT: float = 406597.5
    DAYS_ID_PUBLISH: int = -2120

# 3. Chargement du modèle
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'model_artifacts', 'credit_scoring_model.joblib')
try:
    model = joblib.load(MODEL_PATH)
    print("Modèle chargé avec succès.")
except FileNotFoundError:
    print(f"Erreur: Le fichier du modèle n'a pas été trouvé à l'emplacement {MODEL_PATH}")
    model = None
except Exception as e:
    print(f"Une erreur est survenue lors du chargement du modèle : {e}")
    model = None


# 4. Définition des endpoints de l'API

@app.get("/")
def read_root():
    """Endpoint racine qui retourne un message de bienvenue."""
    return {"message": "Bienvenue sur l'API de Scoring Crédit. Utilisez l'endpoint /predict pour obtenir des prédictions."}

@app.post("/predict")
def predict(client_features: ClientFeatures):
    """
    Endpoint de prédiction.
    Reçoit les caractéristiques d'un client et retourne la probabilité de défaut de paiement.
    """
    if model is None:
        return {"error": "Modèle non chargé. Impossible de faire une prédiction."}

    # Conversion des données d'entrée en DataFrame pandas (avec model_dump)
    features_df = pd.DataFrame([client_features.model_dump()])
    
    try:
        model_features = model.named_steps['imputer'].feature_names_in_
    except AttributeError:
        return {"error": "Impossible de récupérer les noms des features du modèle."}

    data_for_prediction = pd.DataFrame(0, index=[0], columns=model_features)

    for col in features_df.columns:
        if col in data_for_prediction.columns:
            data_for_prediction[col] = features_df[col].values
        else:
            print(f"Attention : La colonne '{col}' fournie n'est pas utilisée par le modèle.")

    try:
        prediction_proba = model.predict_proba(data_for_prediction)[:, 1]
        score = prediction_proba[0]
    except Exception as e:
        return {"error": f"Erreur lors de la prédiction : {e}"}

    is_default = bool(score > 0.5) 
    
    return {
        "prediction_probability": score,
        "prediction_decision": "Défaut de paiement probable" if is_default else "Remboursement probable",
        "threshold": 0.5
    }

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
