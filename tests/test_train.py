# tests/test_train.py

import pytest
import pandas as pd
import joblib
from unittest.mock import patch
from sklearn.pipeline import Pipeline

# On importe la fonction à tester
from src.train import train_final_model

def test_train_final_model(tmp_path):
    """
    Teste le script d'entraînement de bout en bout.

    Ce test vérifie que le script :
    1. S'exécute sans erreur avec un jeu de données de test.
    2. Crée bien un fichier de modèle à l'emplacement attendu.
    3. Le fichier sauvegardé contient un objet Pipeline Scikit-learn valide.
    """
    # 1. Préparation (Arrange)
    # On crée un faux jeu de données d'entraînement
    train_data = {
        'SK_ID_CURR': range(20),
        'TARGET': [0, 1] * 10,
        'feature_1': [i for i in range(20)],
        'feature_2': [i * 2 for i in range(20)],
    }
    train_df = pd.DataFrame(train_data)
    
    # On définit des chemins temporaires pour les données et le modèle
    fake_data_path = tmp_path / "fake_train_data.csv"
    fake_model_path = tmp_path / "fake_model.joblib"
    
    train_df.to_csv(fake_data_path, index=False)

    # On "patch" (remplace) les constantes de chemin dans le script train.py
    # pour utiliser nos fichiers temporaires
    with patch('src.train.DATA_PATH', fake_data_path), \
         patch('src.train.MODEL_PATH', fake_model_path):
        
        # 2. Action (Act)
        # On exécute la fonction d'entraînement
        train_final_model()

    # 3. Vérification (Assert)
    # On vérifie que le fichier du modèle a bien été créé
    assert fake_model_path.exists()

    # On charge le modèle sauvegardé et on vérifie son type
    loaded_model = joblib.load(fake_model_path)
    assert isinstance(loaded_model, Pipeline)
    
    # On vérifie que le pipeline contient bien un classifieur
    assert 'classifier' in loaded_model.named_steps
