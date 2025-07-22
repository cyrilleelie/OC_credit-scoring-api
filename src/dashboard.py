# src/dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import requests
from sqlalchemy import create_engine, text
import os
import tempfile
import warnings
from datetime import datetime, time

# Imports pour Evidently
from evidently import Report
from evidently.presets import DataDriftPreset

# Ignorer les warnings pour une interface plus propre
warnings.filterwarnings("ignore", category=UserWarning, module='sklearn')

# --- Configuration ---
API_URL = "http://127.0.0.1:8000" # URL de votre API FastAPI locale

# Configuration de la base de données
DB_USER = "user"
DB_PASSWORD = "password"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "credit_scoring"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Fonctions de connexion et de récupération de données ---

@st.cache_resource
def get_db_engine():
    """Crée et met en cache une connexion à la base de données."""
    try:
        engine = create_engine(DATABASE_URL)
        print("Connexion à la base de données établie pour le dashboard.")
        return engine
    except Exception as e:
        st.error(f"Erreur de connexion à la base de données : {e}")
        return None

@st.cache_data
def get_client_ids():
    """Récupère et met en cache la liste des ID clients."""
    engine = get_db_engine()
    if engine:
        try:
            with engine.connect() as connection:
                query = text("SELECT sk_id_curr FROM test_data ORDER BY sk_id_curr;")
                result = connection.execute(query)
                return [row[0] for row in result]
        except Exception as e:
            st.error(f"Erreur lors de la récupération des ID clients : {e}")
    return []

def generate_and_save_drift_report():
    """Génère le rapport de dérive et le sauvegarde dans la base de données."""
    engine = get_db_engine()
    if not engine:
        st.error("Connexion à la base de données non disponible.")
        return

    with st.spinner("Génération du rapport en cours..."):
        try:
            with engine.connect() as connection:
                ref_query = text("SELECT data, target FROM training_data ORDER BY random() LIMIT 10000;")
                reference_df_db = pd.read_sql_query(ref_query, connection)
                
                current_data_logs = pd.read_sql_query(text("SELECT input_data FROM api_logs;"), connection)
            
            if current_data_logs.empty:
                st.warning("Aucun log de production trouvé. Impossible de générer le rapport.")
                return

            reference_data = pd.DataFrame(list(reference_df_db['data']))
            reference_data['TARGET'] = reference_df_db['target']
            current_data = pd.DataFrame([row[0] for row in current_data_logs.itertuples(index=False)])
            
            common_columns = list(set(reference_data.columns) & set(current_data.columns))
            reference_data = reference_data[common_columns]
            current_data = current_data[common_columns]
            
            reference_data.replace([np.inf, -np.inf], np.nan, inplace=True)
            current_data.replace([np.inf, -np.inf], np.nan, inplace=True)

            data_drift_report = Report(metrics=[DataDriftPreset()])
            data_drift_report_run = data_drift_report.run(reference_data=reference_data, current_data=current_data)
            
            # Créer un fichier temporaire, fermer le descripteur, puis lire
            fd, tmp_path = tempfile.mkstemp(suffix='.html')
            os.close(fd)                     # <- ferme le descripteur
            data_drift_report_run.save_html(tmp_path)       # Evidently écrit dedans

            with open(tmp_path, encoding='utf-8') as f:
                html_content = f.read()

            os.unlink(tmp_path)              # suppression immédiate
            
            with engine.connect() as connection:
                query = text("INSERT INTO drift_reports (report_timestamp, report_html) VALUES (:ts, :html);")
                connection.execute(query, {"ts": datetime.now(), "html": html_content})
                connection.commit()

            st.success("Rapport de dérive généré et sauvegardé avec succès !")
            # Vider le cache pour forcer le rechargement de la liste des rapports
            st.cache_data.clear()

        except Exception as e:
            st.error(f"Erreur lors de la génération du rapport : {e}")


# --- Interface Principale ---

st.set_page_config(layout="wide", page_title="Dashboard de Scoring Crédit")
st.title("Dashboard de Scoring Crédit - Prêt à Dépenser")

# --- Onglets ---
tab1, tab2, tab3 = st.tabs(["Prédiction de Score", "Performance de l'API", "Analyse de Dérive"])

# --- Onglet 1: Prédiction de Score ---
with tab1:
    st.header("Calculer le score d'un client")
    
    client_ids = get_client_ids()
    if not client_ids:
        st.warning("Aucun ID client trouvé dans la base de données.")
    else:
        selected_client_id = st.selectbox("Sélectionnez un ID Client", options=client_ids)
        
        if st.button("Obtenir le Score", type="primary"):
            if selected_client_id:
                with st.spinner("Appel de l'API en cours..."):
                    try:
                        response = requests.post(f"{API_URL}/predict/{selected_client_id}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success("Prédiction reçue avec succès !")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric(label="Score de Risque", value=f"{data['prediction_probability']:.2%}")
                            with col2:
                                st.metric(label="Décision Suggérée", value=data['prediction_decision'])
                        else:
                            st.error(f"Erreur de l'API : {response.status_code} - {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Impossible de se connecter à l'API. Assurez-vous qu'elle est bien en cours d'exécution.")
                    except Exception as e:
                        st.error(f"Une erreur inattendue est survenue : {e}")

# --- Onglet 2: Performance de l'API ---
with tab2:
    st.header("Monitoring de Performance de l'API")
    
    engine = get_db_engine()
    if engine:
        try:
            with engine.connect() as connection:
                logs_df = pd.read_sql_query(text("SELECT * FROM api_logs;"), connection)

            if not logs_df.empty:
                logs_df['request_timestamp'] = pd.to_datetime(logs_df['request_timestamp']).dt.tz_localize(None)

                st.subheader("Filtres de performance")
                col_filter1, col_filter2 = st.columns(2)
                min_date = logs_df['request_timestamp'].min().date()
                max_date = logs_df['request_timestamp'].max().date()
                
                with col_filter1:
                    start_date = st.date_input("Date de début", min_date, min_value=min_date, max_value=max_date)
                with col_filter2:
                    end_date = st.date_input("Date de fin", max_date, min_value=min_date, max_value=max_date)

                start_datetime = datetime.combine(start_date, time.min)
                end_datetime = datetime.combine(end_date, time.max)

                filtered_logs = logs_df[(logs_df['request_timestamp'] >= start_datetime) & (logs_df['request_timestamp'] <= end_datetime)]

                st.divider()
                st.subheader("Statistiques sur la période sélectionnée")
                if not filtered_logs.empty:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Nombre de requêtes", f"{len(filtered_logs)}")
                    col2.metric("Temps d'inférence moyen", f"{filtered_logs['inference_time_ms'].mean():.2f} ms")
                    col3.metric("Taux de succès", f"{(filtered_logs['http_status_code'] == 200).mean():.2%}")

                    st.subheader("Évolution des temps d'inférence")
                    st.line_chart(filtered_logs.set_index('request_timestamp')['inference_time_ms'])
                    
                    st.subheader("Détail des appels sur la période")
                    # --- CORRECTION APPLIQUÉE ICI ---
                    # On ajoute une hauteur fixe pour rendre le tableau scrollable
                    st.dataframe(filtered_logs, height=400)
                else:
                    st.info("Aucune donnée disponible pour la période sélectionnée.")
            else:
                st.info("Aucun log de performance disponible pour le moment.")
        except Exception as e:
            st.error(f"Erreur lors du chargement des données de monitoring : {e}")

# --- Onglet 3: Analyse de Dérive ---
with tab3:
    st.header("Analyse de la Dérive des Données (Data Drift)")
    
    if st.button("Générer un nouveau Rapport de Dérive", type="secondary"):
        generate_and_save_drift_report()

    st.divider()
    
    engine = get_db_engine()
    if engine:
        try:
            with engine.connect() as connection:
                reports_df = pd.read_sql_query(text("SELECT id, report_timestamp FROM drift_reports ORDER BY report_timestamp DESC;"), connection)

            if not reports_df.empty:
                report_options = {f"Rapport #{row['id']} - {row['report_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}": row['id'] for index, row in reports_df.iterrows()}
                selected_report_display = st.selectbox("Sélectionnez un rapport à afficher", options=list(report_options.keys()))
                
                if selected_report_display:
                    report_id = report_options[selected_report_display]
                    with engine.connect() as connection:
                        query = text("SELECT report_html FROM drift_reports WHERE id = :report_id;")
                        result = connection.execute(query, {"report_id": report_id}).fetchone()
                    
                    if result:
                        st.components.v1.html(result[0], height=600, scrolling=True)
                    else:
                        st.error("Rapport non trouvé.")
            else:
                st.info("Aucun rapport de dérive n'a été généré pour le moment.")
        except Exception as e:
            st.error(f"Erreur lors du chargement des rapports de dérive : {e}")
