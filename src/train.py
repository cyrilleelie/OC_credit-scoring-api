# src/train.py

import pandas as pd
import numpy as np
import os
import re
import joblib
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import lightgbm as lgb

# Définir les chemins
DATA_PATH = './data/application_train_rdy.csv'
MODEL_DIR = 'model_artifacts'
MODEL_PATH = os.path.join(MODEL_DIR, 'credit_scoring_model.joblib')

def train_final_model():
    """
    Charge les données prétraitées, entraîne le modèle LightGBM final avec les 
    meilleurs hyperparamètres et le sauvegarde.
    """
    print("--- 1. Chargement des données d'entraînement ---")
    df = pd.read_csv(DATA_PATH)
    print(f"Données chargées. Shape: {df.shape}")

    # --- 2. Préparation finale des données ---
    print("--- 2. Préparation finale des données ---")
    # Remplacer les valeurs infinies qui peuvent apparaître après les calculs
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Assurer la compatibilité des noms de colonnes (comme dans le notebook)
    df.columns = [re.sub(r'[^A-Za-z0-9_]+', '_', col) for col in df.columns]
    
    TARGET = 'TARGET'
    y = df[TARGET]
    X = df.drop(columns=[TARGET, 'SK_ID_CURR'])

    print(f"Données prêtes avec {X.shape[1]} features.")

    # --- 3. Définition et Entraînement du Modèle ---
    print("--- 3. Définition et Entraînement du Modèle ---")
    
    # Hyperparamètres optimaux trouvés avec Optuna dans votre notebook
    best_params = {
        'objective': 'binary',
        'metric': 'auc',
        'verbose': -1,
        'n_jobs': -1,
        'seed': 42,
        'boosting_type': 'gbdt',
        'n_estimators': 1000, # Nombre d'arbres
        'learning_rate': 0.010241101044512771,
        'num_leaves': 204,
        'max_depth': 12,
        'min_child_samples': 200,
        'subsample': 0.8843947846459445,
        'colsample_bytree': 0.7174115065647507,
    }

    # Création du pipeline final
    final_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('classifier', lgb.LGBMClassifier(**best_params))
    ])

    print("Entraînement du pipeline final sur toutes les données...")
    final_pipeline.fit(X, y)
    print("Entraînement terminé.")

    # --- 4. Sauvegarde du modèle ---
    print("--- 4. Sauvegarde du modèle ---")
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(final_pipeline, MODEL_PATH)
    print(f"Modèle sauvegardé avec succès dans : {MODEL_PATH}")


if __name__ == '__main__':
    train_final_model()