# src/init_db.py

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import JSONB
import time
import os
import traceback

# Importer la configuration centralisée
from config import settings

def create_db_engine():
    """Crée et retourne un moteur de connexion SQLAlchemy en utilisant la config."""
    return create_engine(settings.database_url)

def create_tables(engine):
    """Crée les tables si elles n'existent pas déjà."""
    with engine.connect() as connection:
        print("Création des tables...")
        
        connection.execute(text("DROP TABLE IF EXISTS training_data CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS test_data CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS api_logs CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS drift_reports CASCADE;"))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS training_data (
                sk_id_curr INT PRIMARY KEY,
                target INT,
                data JSONB
            );
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS test_data (
                sk_id_curr INT PRIMARY KEY,
                data JSONB
            );
        """))

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
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS drift_reports (
                id SERIAL PRIMARY KEY,
                report_timestamp TIMESTAMP WITH TIME ZONE,
                report_html TEXT
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
        chunk.replace([np.inf, -np.inf], np.nan, inplace=True)

        df_to_load = pd.DataFrame()
        df_to_load['sk_id_curr'] = chunk['SK_ID_CURR']
        
        cols_to_drop = ['SK_ID_CURR', 'Unnamed: 0']
        
        if table_name == 'training_data' and 'TARGET' in chunk.columns:
            df_to_load['target'] = chunk['TARGET']
            cols_to_drop.append('TARGET')

        data_cols = chunk.drop(columns=[col for col in cols_to_drop if col in chunk.columns])
        
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
                print(f"Échec de la connexion. Nouvel essai dans 5 secondes...")
                retries -= 1
                time.sleep(5)
        
        if not engine or retries == 0:
            print("Impossible de se connecter à la base de données.")
            exit()

        create_tables(engine)
        load_data_to_db(engine, settings.train_data_file, 'training_data')
        load_data_to_db(engine, settings.test_data_file, 'test_data')

    except Exception:
        error_trace = traceback.format_exc()
        error_log_path = 'db_load_error.log'
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write(error_trace)
        print(f"\nUNE ERREUR CRITIQUE EST SURVENUE.")
        print(f"Le détail a été sauvegardé dans : {error_log_path}")
