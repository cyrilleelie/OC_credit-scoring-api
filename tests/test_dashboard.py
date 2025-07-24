# tests/test_dashboard.py

import pytest
from unittest.mock import MagicMock, patch
import streamlit as st

# On importe la fonction à tester
from src.dashboard.app_dashboard import get_client_ids

# --- Fixture pour nettoyer le cache avant chaque test ---
@pytest.fixture(autouse=True)
def clear_streamlit_cache():
    """
    Fixture qui s'exécute automatiquement avant chaque test de ce module
    pour nettoyer le cache de Streamlit et garantir l'isolation des tests.
    """
    st.cache_data.clear()
    st.cache_resource.clear()
    yield  # Le test s'exécute ici

def test_get_client_ids_success():
    """
    Teste que la fonction get_client_ids retourne une liste d'entiers
    quand la base de données répond correctement.
    """
    # 1. Préparation (Arrange)
    # On crée un faux résultat de base de données
    mock_db_result = [(100001,), (100002,), (100003,)]
    
    # On crée un "mock" pour simuler l'engine de la base de données
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value.execute.return_value = mock_db_result

    # 2. Action (Act)
    # On utilise "patch" pour remplacer temporairement get_db_engine par notre mock
    with patch('src.dashboard.app_dashboard.get_db_engine', return_value=mock_engine):
        client_ids = get_client_ids()

    # 3. Vérification (Assert)
    assert client_ids == [100001, 100002, 100003]
    # On vérifie que la fonction de connexion a bien été appelée
    mock_engine.connect.assert_called_once()

def test_get_client_ids_db_error():
    """
    Teste que la fonction retourne une liste vide en cas d'erreur de la BDD.
    """
    # 1. Préparation (Arrange)
    # On configure le mock pour qu'il lève une exception
    mock_engine = MagicMock()
    mock_engine.connect.side_effect = Exception("Erreur de connexion BDD")
    
    # 2. Action (Act)
    with patch('src.dashboard.app_dashboard.get_db_engine', return_value=mock_engine):
        client_ids = get_client_ids()
        
    # 3. Vérification (Assert)
    # La fonction doit retourner une liste vide et ne pas planter
    assert client_ids == []
