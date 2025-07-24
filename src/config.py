# src/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from dotenv import load_dotenv

# Charge les variables depuis un fichier .env
# Note : la configuration dans SettingsConfigDict rend cet appel redondant,
# mais il est conservé pour la clarté.
load_dotenv()

class Settings(BaseSettings):
    # --- Variables chargées depuis le fichier .env ---
    # Base de Données
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    db_name: str
    
    # Sécurité JWT
    api_url: str
    api_user: Optional[str] = None
    api_password: Optional[str] = None
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    decision_threshold: float
    
    # Fichiers de données et modèle
    model_path: str
    train_data_file: str
    test_data_file: str

    @property
    def database_url(self) -> str:
        """Génère l'URL de connexion à la base de données."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # --- CORRECTION APPLIQUÉE ICI ---
    # On indique explicitement à Pydantic d'utiliser l'encodage UTF-8
    # pour lire le fichier .env. C'est la syntaxe pour Pydantic V2.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

# Instance unique des paramètres qui sera importée dans les autres modules
settings = Settings()
