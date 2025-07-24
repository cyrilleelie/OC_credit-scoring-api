# tests/test_api.py

import pytest
import requests # On utilise la bibliothèque standard pour les requêtes HTTP

# On importe uniquement la configuration pour connaître l'URL de l'API
from src.config import settings

# --- Fixtures Pytest ---

@pytest.fixture(scope="module")
def auth_headers():
    """
    Fixture qui s'authentifie en faisant une vraie requête HTTP à l'API
    et retourne les en-têtes d'autorisation.
    """
    response = requests.post(
        f"{settings.api_url}/auth",
        data={"username": settings.api_user, "password": settings.api_password}
    )
    if response.status_code != 200:
        pytest.fail(f"L'authentification a échoué. Assurez-vous que l'API est démarrée. Status: {response.status_code}, Réponse: {response.text}")
        
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Tests ---

def test_read_root():
    """
    Teste l'endpoint racine ('/').
    """
    response = requests.get(f"{settings.api_url}/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bienvenue sur l'API de Scoring Crédit"}

def test_predict_unauthorized():
    """
    Teste que l'endpoint de prédiction est bien protégé.
    """
    response = requests.post(f"{settings.api_url}/predict/100001")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.filterwarnings("ignore:X does not have valid feature names, but LGBMClassifier was fitted with feature names")
def test_predict_success(auth_headers: dict):
    """
    Teste l'endpoint de prédiction avec un ID client valide.
    """
    valid_client_id = 100001
    
    response = requests.post(f"{settings.api_url}/predict/{valid_client_id}", headers=auth_headers)
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["client_id"] == valid_client_id
    assert "prediction_probability" in data
    assert "prediction_decision" in data
    assert isinstance(data["prediction_probability"], float)
    assert 0.0 <= data["prediction_probability"] <= 1.0

def test_predict_client_not_found(auth_headers: dict):
    """
    Teste l'endpoint de prédiction avec un ID client qui n'existe pas.
    """
    invalid_client_id = 9999999
    
    response = requests.post(f"{settings.api_url}/predict/{invalid_client_id}", headers=auth_headers)
    
    assert response.status_code == 404
    assert response.json()["detail"] == f"Client ID {invalid_client_id} non trouvé."
