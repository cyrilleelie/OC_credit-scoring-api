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
git clone https://github.com/cyrilleelie/OC_credit-scoring-api
cd credit-scoring-api
```

### 3. Fichier de Configuration

Créez votre fichier de configuration local à partir de l'exemple fourni.

```bash
cp .env.example .env
```
**Action requise :** Ouvrez le fichier `.env` et remplissez les valeurs, notamment les identifiants de la base de données et les chemins vers les fichiers de données si vous les utilisez localement.

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

Ce script crée le schéma de la base de données et y charge les données des clients.

**Important :** Les fichiers de données CSV complets ne sont pas inclus dans ce dépôt. Vous avez deux options pour exécuter ce script :

**Option A : Développement Local (avec les données complètes)**

1.  Assurez-vous d'avoir téléchargé les fichiers `application_train_rdy.csv` et `application_test_rdy.csv`.
2.  Vérifiez que les chemins vers ces fichiers sont correctement configurés dans votre fichier `.env` (`TRAIN_DATA_FILE` et `TEST_DATA_FILE`).
3.  Exécutez la commande sans arguments.

```bash
poetry run python -m src.scripts.init_db
```

**Option B : Utilisation de Données Alternatives (ex: pour les tests)**

Vous pouvez spécifier le chemin vers d'autres fichiers de données (comme les petits fichiers de test `fixtures`) en utilisant des arguments. C'est la méthode utilisée en intégration continue.

```bash
poetry run python -m src.scripts.init_db \
  --train-file tests/fixtures/sample.train.csv \
  --test-file tests/fixtures/sample_test.csv
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
```

## 🔬 Analyse de Performance

Cette section décrit les outils utilisés pour mesurer et analyser la performance de l'API. **Assurez-vous que le serveur de l'API est en cours d'exécution** avant de lancer ces scripts.

### Profiling de l'API (`cProfile`)

Le script `profile_api.py` utilise `cProfile` pour analyser les goulots d'étranglement de l'API. Il effectue plusieurs appels à l'endpoint de prédiction et mesure le temps passé dans chaque fonction.

**Exécution :**
```bash
poetry run python -m src.scripts.profile_api
```

### Test de Charge (`Locust`)

Le script `locustfile.py` utilise Locust pour simuler une montée en charge et tester la robustesse de l'API sous la pression de plusieurs utilisateurs virtuels.

**Exécution :**
1.  **Lancez Locust :**
    ```bash
    poetry run python -m locust -f src/scripts/locustfile.py --host="http://127.0.0.1:8000"
    ```
2.  **Ouvrez l'interface web de Locust** dans votre navigateur à l'adresse `http://localhost:8089`.
3.  **Configurez et démarrez un test** en spécifiant le nombre d'utilisateurs et le taux d'apparition.
