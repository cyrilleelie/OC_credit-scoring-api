# src/app.py

import gradio as gr
import pandas as pd
import joblib
from sqlalchemy import create_engine, text
import os
import json
from datetime import datetime
import time

# --- Configuration et chargement des ressources ---

# 1. Configuration de la base de données
DB_USER = "user"
DB_PASSWORD = "password"
DB_HOST = "localhost" # Docker's host, accessible from the local machine
DB_PORT = "5432"
DB_NAME = "credit_scoring"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 2. Chargement du modèle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, '..', 'model_artifacts', 'credit_scoring_model.joblib')
model = joblib.load(MODEL_PATH)
print("Modèle chargé avec succès.")

# 3. Connexion à la base de données
engine = create_engine(DATABASE_URL)
print("Connexion à la base de données établie.")


# --- Fonctions de l'application ---

def get_client_ids():
    """Récupère la liste des ID clients depuis la base de données."""
    try:
        with engine.connect() as connection:
            query = text("SELECT sk_id_curr FROM test_data ORDER BY sk_id_curr;")
            result = connection.execute(query)
            client_ids = [row[0] for row in result]
            return client_ids
    except Exception as e:
        print(f"Erreur lors de la récupération des ID clients : {e}")
        return []

def predict_score(client_id):
    """
    Récupère les données d'un client, prédit le score de crédit,
    enregistre le log, et retourne le résultat.
    """
    if not client_id:
        return "Veuillez sélectionner un ID client.", "N/A", "N/A"

    start_time = time.time()
    request_timestamp = datetime.now().isoformat()
    
    try:
        # 1. Récupérer les données du client depuis la BDD
        with engine.connect() as connection:
            query = text("SELECT data FROM test_data WHERE sk_id_curr = :client_id")
            result = connection.execute(query, {"client_id": int(client_id)}).fetchone()
        
        if not result:
            return f"Client ID {client_id} non trouvé.", "Erreur", "Erreur"
            
        client_data_json = result[0]
        
        # 2. Préparer les données pour le modèle
        features_df = pd.DataFrame([client_data_json])
        
        # Récupérer la liste des features attendues par le modèle DANS LE BON ORDRE
        model_features = model.named_steps['imputer'].feature_names_in_
        
        # S'assurer que le DataFrame a toutes les colonnes attendues et dans le bon ordre
        features_df = features_df.reindex(columns=model_features)
        
        # 3. Faire la prédiction
        prediction_proba = model.predict_proba(features_df)[:, 1]
        score = prediction_proba[0]
        
        # 4. Préparer et enregistrer le log
        decision = bool(score > 0.5) # Seuil de décision simple
        end_time = time.time()
        inference_time_ms = (end_time - start_time) * 1000
        response_timestamp = datetime.now().isoformat()

        log_entry = {
            "request_timestamp": request_timestamp,
            "client_id": int(client_id),
            "input_data": json.dumps(client_data_json),
            "prediction_proba": float(score),
            "prediction_decision": decision,
            "response_timestamp": response_timestamp,
            "inference_time_ms": inference_time_ms,
            "http_status_code": 200
        }
        
        with engine.connect() as connection:
            # --- CORRECTION APPLIQUÉE ICI ---
            # On retire le cast '::jsonb' car la colonne est déjà du bon type.
            # SQLAlchemy et le driver de la base de données géreront la conversion.
            query = text("""
                INSERT INTO api_logs (request_timestamp, client_id, input_data, prediction_proba, prediction_decision, response_timestamp, inference_time_ms, http_status_code)
                VALUES (:request_timestamp, :client_id, :input_data, :prediction_proba, :prediction_decision, :response_timestamp, :inference_time_ms, :http_status_code);
            """)
            connection.execute(query, log_entry)
            connection.commit()

        # 5. Formater la sortie pour l'interface
        decision_text = "Défaut de paiement probable" if decision else "Remboursement probable"
        score_formatted = f"{score:.2%}" # Formate en pourcentage
        
        return f"Le client {client_id} a un score de risque de :", score_formatted, decision_text

    except Exception as e:
        print(f"Erreur lors de la prédiction pour le client {client_id}: {e}")
        return "Une erreur est survenue.", "Erreur", str(e)


# --- Création de l'interface Gradio ---

with gr.Blocks(theme=gr.themes.Soft(), title="Dashboard de Scoring Crédit") as demo:
    gr.Markdown("# Dashboard de Scoring Crédit - Prêt à Dépenser")
    
    with gr.Row():
        client_id_dropdown = gr.Dropdown(
            label="Sélectionnez un ID Client",
            choices=get_client_ids(),
            value=get_client_ids()[0] if get_client_ids() else None
        )
        predict_button = gr.Button("Calculer le Score", variant="primary")

    with gr.Row():
        output_text = gr.Textbox(label="Résultat", interactive=False)
        output_score = gr.Textbox(label="Score de Risque", interactive=False)
        output_decision = gr.Textbox(label="Décision Suggérée", interactive=False)
        
    predict_button.click(
        fn=predict_score,
        inputs=[client_id_dropdown],
        outputs=[output_text, output_score, output_decision]
    )

# --- Lancement de l'application ---
if __name__ == "__main__":
    demo.launch()
