# src/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# On importe notre objet de configuration centralisé
from ..config import settings

# 1. Création de l'Engine SQLAlchemy
# C'est le point d'entrée principal vers la base de données.
# `pool_pre_ping=True` vérifie les connexions avant de les utiliser.
engine = create_engine(
    settings.database_url, 
    pool_pre_ping=True
)

# 2. Création de la Fabrique de Sessions
# Chaque instance de SessionLocal sera une session de base de données.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 3. Fonction de Dépendance pour FastAPI
def get_db():
    """
    Cette fonction est un "générateur" qui sera utilisé par FastAPI.
    Elle crée une session, la "fournit" (yield) à l'endpoint,
    et s'assure de la fermer (db.close()) à la fin, même en cas d'erreur.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()