# src/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # --- Variables chargées depuis le fichier .env ---
    # Base de Données
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    db_name: str
    
    # Sécurité JWT
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # --- Variables définies directement ici ---
    # URL de l'API pour le dashboard
    api_url: str = "http://127.0.0.1:8000"
    
    # Chemins (construits à partir de la racine du projet)
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_artifacts_path: str = os.path.join(base_dir, "model_artifacts", "credit_scoring_model.joblib")
    data_path: str = os.path.join(base_dir, "data")
    train_data_file: str = os.path.join(data_path, "application_train_rdy.csv")
    test_data_file: str = os.path.join(data_path, "application_test_rdy.csv")

    @property
    def database_url(self) -> str:
        """Génère l'URL de connexion à la base de données."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # --- CORRECTION APPLIQUÉE ICI ---
    # Utilisation de la syntaxe Pydantic V2 pour la configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

# Instance unique des paramètres qui sera importée dans les autres modules
settings = Settings()
