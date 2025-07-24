# Dockerfile

# Étape 1: Utiliser une image Python de base
# On choisit une version qui correspond à notre projet (ex: 3.11)
FROM python:3.11-slim

# Étape 2: Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Étape 3: Copier les fichiers de dépendances
# On copie uniquement ce qui est nécessaire pour installer les dépendances d'abord
# pour profiter du cache de Docker.
COPY pyproject.toml poetry.lock ./

# Étape 4: Installer Poetry et les dépendances du projet
# On installe Poetry, puis on l'utilise pour installer les bibliothèques
# listées dans poetry.lock, sans créer d'environnement virtuel.
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --no-dev

# Étape 5: Copier le reste du code de l'application
# On copie tout le code source (le dossier src, etc.)
COPY . .

# Étape 6: Exposer les ports
# On indique que notre application écoutera sur les ports 8000 (pour l'API)
# et 8501 (pour le dashboard).
EXPOSE 8000
EXPOSE 8501

# Étape 7: Commande de démarrage
# Cette commande sera exécutée au lancement du conteneur.
# On utilise un petit script shell pour lancer les deux services en parallèle.
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port 8000 & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]
