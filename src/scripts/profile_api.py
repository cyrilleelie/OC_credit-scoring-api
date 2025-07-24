# src/scripts/profile_api.py

import cProfile
import pstats
import requests
import os
import sys

# --- Bloc d'initialisation du chemin ---
# Ajoute la racine du projet au chemin de recherche pour que les imports fonctionnent
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
# --- Fin du bloc ---

from src.config import settings

# --- Configuration du Test ---
API_URL = settings.api_url
TEST_USER = settings.api_user
TEST_PASSWORD = settings.api_password
# Assurez-vous que cet ID client existe bien dans votre table test_data
CLIENT_ID_TO_TEST = 100002 

def get_token():
    """S'authentifie auprès de l'API et récupère un token JWT."""
    print("Authentification pour obtenir le token...")
    try:
        response = requests.post(
            f"{API_URL}/auth",
            data={"username": TEST_USER, "password": TEST_PASSWORD}
        )
        # Lève une exception si le statut est une erreur (4xx ou 5xx)
        response.raise_for_status() 
        print("Token obtenu avec succès.")
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"ERREUR: Impossible de s'authentifier. L'API est-elle en cours d'exécution ? Détail : {e}")
        sys.exit(1)


def make_prediction_request(token):
    """Lance une requête de prédiction unique."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(f"{API_URL}/predict/{CLIENT_ID_TO_TEST}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERREUR lors de l'appel de prédiction : {e}")
        return None

def profile_requests():
    """Fonction principale qui exécute les appels à profiler."""
    token = get_token()
    if not token:
        return

    print("Lancement des requêtes de prédiction pour le profiling...")
    # On fait 10 appels pour avoir une mesure plus stable
    for i in range(10): 
        print(f"  Appel {i+1}/10...")
        make_prediction_request(token)
    print("Profiling terminé.")

if __name__ == "__main__":
    # Initialise le profiler
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Lance la fonction à analyser
    profile_requests()
    
    # Arrête le profiler et prépare les statistiques
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumtime') # tri par temps cumulé
    
    # Affiche les résultats
    print("\n--- RÉSULTATS DU PROFILING (TOP 15 FONCTIONS PAR TEMPS CUMULÉ) ---")
    stats.print_stats(15)
