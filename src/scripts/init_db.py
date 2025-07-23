# src/init_db.py

import pandas as pd
import numpy as np
from sqlalchemy.dialects.postgresql import JSONB
import traceback
import os
import argparse

# On importe les objets et fonctions depuis nos fichiers centralisés
from ..database.database import engine, SessionLocal
from ..database import models
from ..config import settings
from ..api.security import get_password_hash

def init_db(train_file_path, test_file_path):
    """
    Crée toutes les tables définies dans models.py et charge les données initiales.
    """
    # Crée toutes les tables en se basant sur les modèles SQLAlchemy
    print("Création des tables via les modèles SQLAlchemy...")
    # La ligne suivante supprime toutes les tables existantes. Commentez-la si vous ne voulez pas perdre vos données à chaque exécution.
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    print("Tables créées avec succès.")

    # Utilise une session pour les opérations sur la base de données
    db = SessionLocal()
    try:
        # --- Création de l'utilisateur de test ---
        db_user = db.query(models.User).filter(models.User.username == settings.api_user).first()
        if not db_user:
            hashed_password = get_password_hash(settings.api_password)
            new_user = models.User(
                username=settings.api_user,
                email="test@example.com",
                hashed_password=hashed_password
            )
            db.add(new_user)
            db.commit()
            print(f"Utilisateur de test '{settings.api_user}' créé.")
        else:
            print("Utilisateur de test déjà existant.")

        # --- Chargement des données d'entraînement ---
        if db.query(models.TrainingData).first() is None:
            print(f"Chargement du fichier {os.path.basename(train_file_path)}...")
            chunk_size = 10000
            for chunk in pd.read_csv(train_file_path, chunksize=chunk_size):
                chunk.replace([np.inf, -np.inf], np.nan, inplace=True)
                data_to_load = chunk.to_dict(orient='records')
                db.bulk_insert_mappings(models.TrainingData, data_to_load)
                db.commit()
            print("Données d'entraînement chargées.")
        else:
            print("Données d'entraînement déjà présentes.")

        # --- Chargement des données de test ---
        if db.query(models.TestData).first() is None:
            print(f"Chargement du fichier {os.path.basename(test_file_path)}...")
            chunk_size = 10000
            for chunk in pd.read_csv(test_file_path, chunksize=chunk_size):
                chunk.replace([np.inf, -np.inf], np.nan, inplace=True)
                # Renommer SK_ID_CURR pour correspondre au modèle
                chunk.rename(columns={'SK_ID_CURR': 'sk_id_curr'}, inplace=True)
                data_to_load = chunk.to_dict(orient='records')
                db.bulk_insert_mappings(models.TestData, data_to_load)
                db.commit()
            print("Données de test chargées.")
        else:
            print("Données de test déjà présentes.")

    finally:
        db.close()

if __name__ == "__main__":
    # On ajoute la gestion des arguments de la ligne de commande
    parser = argparse.ArgumentParser(description="Initialize the database.")
    parser.add_argument("--train-file", default=settings.train_data_file, help="Path to the training data CSV.")
    parser.add_argument("--test-file", default=settings.test_data_file, help="Path to the test data CSV.")
    args = parser.parse_args()
    
    print("Initialisation de la base de données...")
    try:
        init_db(args.train_file, args.test_file)
        print("Initialisation terminée avec succès.")
    except Exception as e:
        print(f"\nUNE ERREUR CRITIQUE EST SURVENUE.")
        print(f"Erreur : {e}")
        traceback.print_exc()