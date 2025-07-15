# API de Scoring Crédit pour "Prêt à Dépenser"

Ce projet a pour objectif de déployer un modèle de Machine Learning de scoring crédit, développé en amont, via une API robuste et conteneurisée. L'API doit permettre d'évaluer en temps réel les nouvelles demandes de crédit en fournissant une probabilité de défaut de paiement.

Ce projet s'inscrit dans un cycle MLOps complet, incluant la création de l'API, les tests automatisés, le déploiement via une pipeline CI/CD, et le monitoring du modèle en production.

---

## 🚀 Workflow du Projet

Le projet se déroule en plusieurs étapes séquentielles :

1.  **Préparation des données :** Un script exécute toute l'ingénierie des caractéristiques (feature engineering) à partir des données brutes.
2.  **Entraînement du modèle :** Un second script utilise les données préparées pour entraîner le modèle de scoring final (un pipeline LightGBM) et le sauvegarde.
3.  **Exposition via une API :** Le modèle entraîné est chargé par une API (FastAPI/Gradio) pour servir des prédictions.
4.  **Déploiement et Monitoring :** L'API est conteneurisée avec Docker et déployée via une pipeline CI/CD sur GitHub Actions.

---

## 🛠️ Installation et Configuration

Suivez ces étapes pour mettre en place l'environnement de développement local.

### 1. Prérequis

-   [Git](https://git-scm.com/)
-   [Python 3.10+](https://www.python.org/)
-   [Poetry](https://python-poetry.org/) pour la gestion des dépendances.

### 2. Cloner le Dépôt

```bash
git clone https://github.com/cyrilleelie/OC_credit-scoring-api.git
cd OC_credit-scoring-api
```

### 3. Téléchargement des Données

Les données pour ce projet proviennent de la compétition Kaggle **"Home Credit Default Risk"**. Elles ne sont pas incluses dans ce dépôt en raison de leur taille.

**Action requise :**
-   Créez un dossier `data/` à la racine du projet.
-   Téléchargez les fichiers de données depuis [cette page Kaggle](https://www.kaggle.com/c/home-credit-default-risk/data).
-   Placez les fichiers `.csv` suivants dans le dossier `data/` :
    -   `application_train.csv`
    -   `application_test.csv`
    -   `bureau.csv`
    -   `bureau_balance.csv`
    -   `previous_application.csv`
    -   `POS_CASH_balance.csv`
    -   `installments_payments.csv`
    -   `credit_card_balance.csv`

### 4. Installer les Dépendances

Ce projet utilise Poetry pour gérer ses dépendances. Exécutez la commande suivante pour installer les librairies nécessaires listées dans `pyproject.toml` :

```bash
poetry install
```

---

## ⚙️ Usage

Une fois l'installation terminée, suivez ces étapes pour générer l'artefact du modèle.

### Étape 1 : Lancer la Préparation des Données

Ce script va traiter les données brutes du dossier `data/` et générer les fichiers `application_train_rdy.csv` et `application_test_rdy.csv`.

```bash
poetry run python src/data_processing.py
```

### Étape 2 : Lancer l'Entraînement du Modèle

Ce script utilise `application_train_rdy.csv` pour entraîner le modèle final et le sauvegarde dans `model_artifacts/credit_scoring_model.joblib`.

```bash
poetry run python src/train.py
```

### Étape 3 : Lancer l'API (à venir)

*Les instructions pour lancer l'API via Docker ou localement seront ajoutées ici lors de l'Étape 2 du projet.*

---

## 📂 Structure du Projet

```
.
├── .github/workflows/  # Fichiers de configuration CI/CD (GitHub Actions)
├── data/               # Données brutes et traitées (ignoré par Git)
├── model_artifacts/    # Modèles entraînés et sauvegardés (ignoré par Git)
├── src/                # Code source du projet
│   ├── data_processing.py  # Script de feature engineering
│   ├── train.py            # Script d'entraînement du modèle
│   ├── main.py             # Point d'entrée de l'API (à créer)
│   └── tests/              # Tests unitaires et d'intégration (à créer)
├── .gitignore          # Fichiers et dossiers à ignorer par Git
├── Dockerfile          # Instructions pour construire l'image Docker (à créer)
├── pyproject.toml      # Dépendances et configuration du projet (Poetry)
└── README.md           # Ce fichier
