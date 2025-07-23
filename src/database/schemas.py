# src/schemas.py

from pydantic import BaseModel
from typing import Optional

# --- Schéma pour les données dans le token JWT ---
class TokenData(BaseModel):
    username: Optional[str] = None

# --- Schéma pour la réponse du token d'authentification ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- Schéma pour la réponse de l'endpoint de prédiction ---
class PredictionResponse(BaseModel):
    client_id: int
    prediction_probability: float
    prediction_decision: str