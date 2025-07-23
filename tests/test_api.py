# src/tests/test_api.py

from fastapi.testclient import TestClient
import pytest

# pytest-cov et pytest sont nécessaires, assurez-vous qu'ils sont dans pyproject.toml (dev-dependencies)
# poetry add pytest pytest-cov --group dev

from src.api.main import app

# Crée un client de test pour notre application FastAPI
client = TestClient(app)

# --- Fixture Pytest pour gérer l'authentification ---

@pytest.fixture(scope="module")
def auth_headers():
    """
    Fixture qui s'authentifie une fois pour tous les tests du module
    et retourne les en-têtes d'autorisation nécessaires.
    """
    response = client.post(
        "/auth",
        data={"username": "user_test", "password": "pass123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Tests ---

def test_read_root():
    """
    Teste l'endpoint racine ('/').
    Il doit retourner un code de statut 200 et le message de bienvenue.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bienvenue sur l'API de Scoring Crédit"}

def test_predict_unauthorized():
    """
    Teste que l'endpoint de prédiction est bien protégé.
    Un appel sans token doit retourner une erreur 401.
    """
    response = client.post("/predict/100001")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.filterwarnings("ignore:X does not have valid feature names, but LGBMClassifier was fitted with feature names")
def test_predict_success(auth_headers):
    """
    Teste l'endpoint de prédiction avec un ID client valide et une authentification correcte.
    Il doit retourner un code de statut 200 et une prédiction valide.
    """
    valid_client_id = 100001
    
    response = client.post(f"/predict/{valid_client_id}", headers=auth_headers)
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["client_id"] == valid_client_id
    assert "prediction_probability" in data
    assert "prediction_decision" in data
    assert isinstance(data["prediction_probability"], float)
    assert 0.0 <= data["prediction_probability"] <= 1.0

def test_predict_client_not_found(auth_headers):
    """
    Teste l'endpoint de prédiction avec un ID client qui n'existe pas, en étant authentifié.
    L'API doit retourner une erreur HTTP 404.
    """
    invalid_client_id = 9999999
    
    response = client.post(f"/predict/{invalid_client_id}", headers=auth_headers)
    
    assert response.status_code == 404
    assert response.json()["detail"] == f"Client ID {invalid_client_id} non trouvé."

