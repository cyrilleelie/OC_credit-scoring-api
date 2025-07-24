# src/scripts/init_db.py

import pandas as pd
import numpy as np
import argparse
import os
import traceback

from src.database.database import engine, SessionLocal
from src.database import models
from src.config import settings
from src.api.security import get_password_hash

def init_db(train_file_path, test_file_path):
    """
    Crée toutes les tables et charge les données initiales.
    """
    print("Création des tables via les modèles SQLAlchemy...")
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    print("Tables créées avec succès.")

    db = SessionLocal()
    try:
        # --- Création de l'utilisateur de test ---
        if not db.query(models.User).filter(models.User.username == settings.api_user).first():
            hashed_password = get_password_hash(settings.api_password)
            db.add(models.User(username=settings.api_user, hashed_password=hashed_password))
            db.commit()
            print(f"Utilisateur de test '{settings.api_user}' créé.")

        # --- Chargement des données d'entraînement ---
        if db.query(models.TrainingData).count() == 0:
            print(f"Chargement du fichier {os.path.basename(train_file_path)}...")
            chunk_size = 5000
            for chunk in pd.read_csv(train_file_path, chunksize=chunk_size):
                chunk.replace([np.inf, -np.inf], np.nan, inplace=True)
                
                records_to_insert = []
                for index, row in chunk.iterrows():
                    # Sépare les colonnes de features des autres
                    features = row.drop(['SK_ID_CURR', 'TARGET']).where(pd.notna(row), None).to_dict()
                    
                    record = {
                        "sk_id_curr": row['SK_ID_CURR'],
                        "target": row['TARGET'],
                        "data": features
                    }
                    records_to_insert.append(record)
                
                db.bulk_insert_mappings(models.TrainingData, records_to_insert)
                db.commit()
            print("Données d'entraînement chargées.")

        # --- Chargement des données de test ---
        if db.query(models.ClientDataForTest).count() == 0:
            print(f"Chargement du fichier {os.path.basename(test_file_path)}...")
            chunk_size = 5000
            for chunk in pd.read_csv(test_file_path, chunksize=chunk_size):
                chunk.replace([np.inf, -np.inf], np.nan, inplace=True)

                records_to_insert = []
                for index, row in chunk.iterrows():
                    # Sépare les colonnes de features des autres
                    features = row.drop(['SK_ID_CURR']).where(pd.notna(row), None).to_dict()
                    
                    record = {
                        "sk_id_curr": row['SK_ID_CURR'],
                        "data": features
                    }
                    records_to_insert.append(record)
                
                db.bulk_insert_mappings(models.ClientDataForTest, records_to_insert)
                db.commit()
            print("Données de test chargées.")
    finally:
        db.close()

if __name__ == "__main__":
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