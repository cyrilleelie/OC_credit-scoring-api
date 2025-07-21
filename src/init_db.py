# src/init_db.py

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import JSONB
import time
import os
import json
import traceback

# --- Configuration de la base de données ---
DB_USER = "user"
DB_PASSWORD = "password"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "credit_scoring"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Chemins vers les fichiers de données ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'data')
# --- MODIFICATION: On pointe vers le fichier de données déjà traité ---
PROCESSED_TEST_DATA_FILE = os.path.join(DATA_PATH, 'application_test_rdy.csv')


def create_db_engine():
    """Crée et retourne un moteur de connexion SQLAlchemy."""
    return create_engine(DATABASE_URL)

def create_tables(engine):
    """Crée les tables si elles n'existent pas déjà."""
    with engine.connect() as connection:
        print("Création des tables...")
        
        # On supprime les anciennes tables pour garantir un état propre
        connection.execute(text("DROP TABLE IF EXISTS test_data CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS api_logs CASCADE;"))

        # Table pour les données de test (feature store)
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS test_data (
                sk_id_curr INT PRIMARY KEY,
                data JSONB
            );
        """))

        # Table pour les logs de l'API
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS api_logs (
                id SERIAL PRIMARY KEY,
                request_timestamp TIMESTAMP WITH TIME ZONE,
                client_id INT,
                input_data JSONB,
                prediction_proba FLOAT,
                prediction_decision BOOLEAN,
                response_timestamp TIMESTAMP WITH TIME ZONE,
                inference_time_ms FLOAT,
                http_status_code INT
            );
        """))
        connection.commit()
        print("Tables créées avec succès.")


def load_data_to_db(engine, file_path, table_name):
    """Charge les données d'un CSV dans la base de données par morceaux (chunks) pour optimiser la mémoire."""
    print(f"Chargement du fichier {os.path.basename(file_path)} dans la table {table_name}...")
    
    chunk_size = 10000
    total_rows = 0
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # Les noms de colonnes peuvent contenir des caractères non supportés, on les nettoie
        chunk.columns = ["".join (c if c.isalnum() else '_' for c in str(x)) for x in chunk.columns]

        df_to_load = pd.DataFrame()
        df_to_load['sk_id_curr'] = chunk['SK_ID_CURR']
        
        # On enlève les colonnes inutiles ou redondantes avant de créer le JSON
        cols_to_drop = [col for col in ['SK_ID_CURR', 'TARGET', 'Unnamed_0'] if col in chunk.columns]
        data_cols = chunk.drop(columns=cols_to_drop)
        
        data_cols = data_cols.astype(object).where(pd.notna(data_cols), None)
        df_to_load['data'] = data_cols.to_dict(orient='records')

        df_to_load.to_sql(
            table_name, 
            engine, 
            if_exists='append', 
            index=False, 
            method='multi',
            dtype={'data': JSONB} 
        )
        total_rows += len(df_to_load)
        print(f"  {total_rows} lignes chargées...")
    
    print(f"Chargement de {total_rows} lignes dans {table_name} terminé.")


if __name__ == "__main__":
    engine = None
    try:
        retries = 5
        while retries > 0:
            try:
                engine = create_db_engine()
                with engine.connect():
                    print("Connexion à la base de données réussie.")
                    break
            except Exception:
                print(f"Échec de la connexion à la base de données. Nouvel essai dans 5 secondes...")
                retries -= 1
                time.sleep(5)
        
        if not engine or retries == 0:
            print("Impossible de se connecter à la base de données après plusieurs tentatives.")
            exit()

        create_tables(engine)
        load_data_to_db(engine, PROCESSED_TEST_DATA_FILE, 'test_data')

    except FileNotFoundError:
        print(f"\nERREUR: Le fichier de données traitées '{os.path.basename(PROCESSED_TEST_DATA_FILE)}' est introuvable.")
        print("Veuillez vous assurer d'avoir exécuté le script de feature engineering au préalable.")
    except Exception:
        error_trace = traceback.format_exc()
        error_log_path = 'db_load_error.log'
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write(error_trace)
        print(f"\nUNE ERREUR CRITIQUE EST SURVENUE.")
        print(f"Le détail complet a été sauvegardé dans le fichier : {error_log_path}")

