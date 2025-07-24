# src/scripts/load_test.py

import os
import sys
import random
from locust import HttpUser, task, between, events

# --- Bloc d'initialisation du chemin ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
# --- Fin du bloc ---

# Imports nécessaires pour la connexion à la BDD
from src.config import settings
from src.database.database import SessionLocal
from src.database.models import ClientDataForTest

# --- Variable globale pour stocker les ID clients ---
# Cette liste sera partagée par tous les utilisateurs virtuels.
CLIENT_IDS = []

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Cette fonction est exécutée une seule fois au tout début du test de charge.
    Elle se connecte à la BDD pour récupérer la liste de tous les ID clients.
    """
    print("Initialisation du test de charge : récupération des ID clients depuis la BDD...")
    db = SessionLocal()
    try:
        # Récupère tous les sk_id_curr de la table de test
        results = db.query(ClientDataForTest.sk_id_curr).all()
        # Stocke les ID dans la liste globale
        global CLIENT_IDS
        CLIENT_IDS = [row[0] for row in results]
        
        if not CLIENT_IDS:
            print("ERREUR: Aucun ID client n'a été trouvé dans la base de données. Le test ne peut pas continuer.")
            # Arrête le test si aucun client n'est trouvé
            environment.runner.quit()
        else:
            print(f"{len(CLIENT_IDS)} ID clients chargés avec succès. Le test peut commencer.")
            
    except Exception as e:
        print(f"ERREUR critique lors de la récupération des ID clients : {e}")
        environment.runner.quit()
    finally:
        db.close()


class APIUser(HttpUser):
    """
    Classe représentant un utilisateur virtuel pour le test de charge.
    """
    wait_time = between(1, 3) 
    token = None

    def on_start(self):
        """
        Appelé une fois au démarrage de chaque utilisateur virtuel pour s'authentifier.
        """
        if not settings.api_user or not settings.api_password:
            print("ERREUR: API_USER et API_PASSWORD doivent être définis.")
            self.environment.runner.quit()
            return
            
        try:
            response = self.client.post(
                "/auth", 
                data={"username": settings.api_user, "password": settings.api_password}
            )
            response.raise_for_status()
            self.token = response.json()["access_token"]
        except Exception as e:
            print(f"Échec de l'authentification pour un utilisateur Locust: {e}")
            self.environment.runner.quit()

    @task
    def get_prediction(self):
        """
        Tâche principale : choisir un ID client au hasard et appeler l'endpoint de prédiction.
        """
        # S'assure que le token et la liste d'ID sont bien disponibles
        if self.token and CLIENT_IDS:
            # Choisit un ID client au hasard dans la liste
            random_client_id = random.choice(CLIENT_IDS)
            
            headers = {"Authorization": f"Bearer {self.token}"}
            
            self.client.post(
                f"/predict/{random_client_id}", 
                headers=headers, 
                name="/predict/[client_id]"
            )
