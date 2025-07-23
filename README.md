# API de Scoring Crédit & Dashboard de Monitoring

Ce projet a pour objectif de déployer un modèle de Machine Learning de scoring crédit via une API robuste (FastAPI) et de fournir un dashboard interactif (Streamlit) pour l'analyse et le monitoring en temps réel. L'ensemble de l'application est conçu pour être conteneurisable avec Docker et est supporté par une base de données PostgreSQL.

## 🏛️ Architecture

L'application est composée de trois services principaux conçus pour fonctionner ensemble :

1.  **Base de Données PostgreSQL** : Conteneurisée avec Docker, elle stocke les données des clients, les utilisateurs de l'application, les logs d'API et les rapports de dérive.
2.  **API FastAPI** : Sert le modèle de scoring. Elle expose des endpoints sécurisés pour l'authentification et la prédiction, et enregistre chaque appel dans la base de données.
3.  **Dashboard Streamlit** : Fournit une interface utilisateur pour interagir avec l'API, visualiser les performances et analyser la dérive des données.

## 📂 Structure du Projet

Le code est organisé en modules fonctionnels pour une meilleure clarté et maintenabilité.

```
credit-scoring-api/
├── .github/workflows/    # Workflows d'Intégration Continue (CI)
├── model_artifacts/      # Modèles entraînés (ignoré par Git)
├── src/                  # Code source de l'application
│   ├── api/              # Logique de l'API FastAPI
│   ├── config/           # Configuration de l'application
│   ├── dashboard/        # Logique du Dashboard Streamlit
│   ├── database/         # Modèles de données et connexion BDD
│   └── scripts/          # Scripts utilitaires (init_db, profiling, etc.)
├── tests/                # Tests automatisés
│   ├── fixtures/         # Petits jeux de données pour les tests
│   └── test_api.py
├── .env.example          # Fichier d'exemple pour la configuration
├── .gitignore
├── app.py                # Point d'entrée pour le dashboard Streamlit
├── docker-compose.yml    # Configuration pour lancer la BDD avec Docker
└── pyproject.toml        # Dépendances et configuration du projet (Poetry)
```

## 🚀 Installation et Lancement

Suivez ces étapes pour lancer l'application en environnement de développement local.

### 1. Prérequis

* [Git](https://git-scm.com/)
* [Python 3.11+](https://www.python.org/)
* [Poetry](https://python-poetry.org/)
* [Docker](https://www.docker.com/) et Docker Compose

### 2. Cloner le Dépôt

```bash
git clone [URL_DE_VOTRE_DEPOT]
cd credit-scoring-api
```

### 3. Fichier de Configuration

Créez votre fichier de configuration local à partir de l'exemple fourni.

```bash
cp .env.example .env
```
**Action requise :** Ouvrez le fichier `.env` et remplissez les valeurs, notamment les identifiants de la base de données.

### 4. Installer les Dépendances

Ce projet utilise Poetry. Installez toutes les dépendances nécessaires :

```bash
poetry install
```

### 5. Démarrer la Base de Données

Lancez le conteneur PostgreSQL en arrière-plan avec Docker Compose :

```bash
docker-compose up -d
```

### 6. Initialiser la Base de Données

Exécutez ce script une seule fois pour créer les tables et charger les données initiales.

```bash
poetry run python -m src.scripts.init_db
```

### 7. Lancer l'API FastAPI

Dans un premier terminal :

```bash
poetry run uvicorn src.api.main:app --reload
```
L'API sera accessible à l'adresse `http://127.0.0.1:8000`.

### 8. Lancer le Dashboard Streamlit

Dans un second terminal :

```bash
poetry run streamlit run app.py
```
Le dashboard sera accessible à l'adresse `http://localhost:8501`.

## ✅ Tests

Pour lancer la suite de tests automatisés, exécutez la commande suivante depuis la racine du projet :

```bash
poetry run pytest
