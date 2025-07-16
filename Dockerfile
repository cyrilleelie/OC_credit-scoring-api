# Étape 1: Utiliser une image Python de base légère
FROM python:3.12-slim

# Étape 2: Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Étape 3: Installer Poetry
# On utilise pip pour installer poetry lui-même
RUN pip install poetry

# Étape 4: Copier les fichiers de dépendances
# On copie d'abord ces fichiers pour profiter du cache Docker.
# Si ces fichiers ne changent pas, les dépendances ne seront pas réinstallées.
COPY pyproject.toml poetry.lock ./

# Étape 5: Installer les dépendances du projet avec Poetry
# - On désactive la création d'environnements virtuels dans le conteneur.
# - On installe uniquement les dépendances de production (--without dev).
RUN poetry config virtualenvs.create false && poetry install --no-root --without dev

# Étape 6: Copier le code source de l'application et le modèle
COPY ./src ./src
COPY ./model_artifacts ./model_artifacts

# Étape 7: Définir la commande pour lancer l'application
# On expose le port 8000 et on s'assure que l'API est accessible de l'extérieur du conteneur (host 0.0.0.0)
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
