# tests/test_data_processing.py

import pytest
import pandas as pd
from unittest.mock import patch

# On importe la fonction à tester
from src.data_processing import application_train_test

def test_application_train_test():
    """
    Teste la fonction de prétraitement 'application_train_test'.
    
    Ce test vérifie que la fonction :
    1. Lit correctement les données d'entrée (simulées).
    2. Crée les nouvelles features attendues.
    3. Retourne un DataFrame avec le bon nombre de lignes.
    """
    # 1. Préparation (Arrange)
    # On crée de faux DataFrames directement en mémoire
    train_df = pd.DataFrame({
        'SK_ID_CURR': [1, 2], 'TARGET': [0, 1], 'CODE_GENDER': ['M', 'F'],
        'FLAG_OWN_CAR': ['N', 'Y'], 'FLAG_OWN_REALTY': ['Y', 'Y'], # Colonnes ajoutées
        'DAYS_BIRTH': [-10000, -12000], 'DAYS_EMPLOYED': [-1000, -1500],
        'AMT_INCOME_TOTAL': [100000, 150000], 'AMT_CREDIT': [200000, 300000],
        'CNT_FAM_MEMBERS': [2, 3], 'AMT_ANNUITY': [20000, 30000]
    })
    test_df = pd.DataFrame({
        'SK_ID_CURR': [3], 'CODE_GENDER': ['M'],
        'FLAG_OWN_CAR': ['Y'], 'FLAG_OWN_REALTY': ['N'], # Colonnes ajoutées
        'DAYS_BIRTH': [-11000], 'DAYS_EMPLOYED': [-1200], 
        'AMT_INCOME_TOTAL': [120000], 'AMT_CREDIT': [250000], 
        'CNT_FAM_MEMBERS': [1], 'AMT_ANNUITY': [25000]
    })

    # Notre mock retourne directement les DataFrames au lieu de lire un fichier
    def mock_read_csv(filepath, nrows=None):
        if "train" in str(filepath):
            return train_df
        elif "test" in str(filepath):
            return test_df
        return pd.DataFrame()

    # 2. Action (Act)
    # On remplace 'pd.read_csv' DANS LE MODULE 'data_processing' par notre mock
    with patch('src.data_processing.pd.read_csv', side_effect=mock_read_csv):
        processed_df = application_train_test()

    # 3. Vérification (Assert)
    assert isinstance(processed_df, pd.DataFrame)
    assert len(processed_df) == 3  # 2 lignes du train + 1 ligne du test
    
    # On vérifie la présence des nouvelles colonnes créées par la fonction
    expected_new_cols = [
        'DAYS_EMPLOYED_PERC', 'INCOME_CREDIT_PERC', 'INCOME_PER_PERSON',
        'ANNUITY_INCOME_PERC', 'PAYMENT_RATE'
    ]
    for col in expected_new_cols:
        assert col in processed_df.columns

