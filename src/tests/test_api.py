# src/tests/test_api.py

from fastapi.testclient import TestClient
import sys
import os
import pytest # Importer pytest

# Ajouter le répertoire src au path pour que l'import fonctionne
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

# Créer un client de test pour notre application FastAPI
client = TestClient(app)

def test_read_root():
    """
    Teste l'endpoint racine ('/').
    Il doit retourner un status code 200 et un message de bienvenue.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bienvenue sur l'API de Scoring Crédit. Utilisez l'endpoint /predict pour obtenir des prédictions."}


# --- CORRECTION APPLIQUÉE ICI ---
# On utilise un marqueur pytest pour dire au test d'ignorer ce warning spécifique.
@pytest.mark.filterwarnings("ignore:X does not have valid feature names, but LGBMClassifier was fitted with feature names")
def test_predict_success():
    """
    Teste l'endpoint de prédiction ('/predict') avec des données valides.
    Il doit retourner un status code 200 et une prédiction valide.
    """
    # Données d'exemple pour un client
    client_data = {
        "EXT_SOURCE_2": 0.262949,
        "EXT_SOURCE_3": 0.139376,
        "DAYS_BIRTH": -20775,
        "DAYS_EMPLOYED": -1676.0,
        "PAYMENT_RATE": 0.057470,
        "AMT_ANNUITY": 24700.5,
        "AMT_CREDIT": 406597.5,
        "DAYS_ID_PUBLISH": -2120
    }
    
    response = client.post("/predict", json=client_data)
    
    # Vérifier le status code
    assert response.status_code == 200
    
    # Vérifier le contenu de la réponse
    data = response.json()
    assert "prediction_probability" in data
    assert "prediction_decision" in data
    assert "threshold" in data
    
    # Vérifier que la probabilité est un flottant entre 0 et 1
    assert isinstance(data["prediction_probability"], float)
    assert 0.0 <= data["prediction_probability"] <= 1.0

def test_predict_invalid_data():
    """
    Teste l'endpoint de prédiction avec des données invalides (un type incorrect).
    FastAPI doit automatiquement retourner un status code 422 (Unprocessable Entity).
    """
    invalid_client_data = {
        "EXT_SOURCE_2": "ceci n'est pas un float", # Donnée invalide
        "EXT_SOURCE_3": 0.139376,
        "DAYS_BIRTH": -20775,
        "DAYS_EMPLOYED": -1676.0,
        "PAYMENT_RATE": 0.057470,
        "AMT_ANNUITY": 24700.5,
        "AMT_CREDIT": 406597.5,
        "DAYS_ID_PUBLISH": -2120
    }
    
    response = client.post("/predict", json=invalid_client_data)
    
    # FastAPI gère la validation et doit retourner une erreur 422
    assert response.status_code == 422
