# src/models.py

from sqlalchemy import (
    Boolean, Column, Integer, String, DateTime, 
    JSON, Float, Text
)
from sqlalchemy.orm import declarative_base

# Base est la classe mère dont tous vos modèles de table hériteront.
# SQLAlchemy l'utilise pour mapper vos classes Python aux tables de la BDD.
Base = declarative_base()

# --- Modèle pour la table des utilisateurs ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False)

# --- Modèle pour les logs de l'API ---
class ApiLog(Base):
    __tablename__ = 'api_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    request_timestamp = Column(DateTime, nullable=False)
    client_id = Column(Integer, nullable=True)
    input_data = Column(JSON, nullable=False)
    prediction_proba = Column(Float, nullable=False)
    prediction_decision = Column(String, nullable=False)
    inference_time_ms = Column(Float, nullable=False)
    http_status_code = Column(Integer, nullable=False)

# --- Modèle pour les rapports de dérive de données ---
class DriftReport(Base):
    __tablename__ = 'drift_reports'
    
    id = Column(Integer, primary_key=True, index=True)
    report_timestamp = Column(DateTime, nullable=False)
    report_html = Column(Text, nullable=False)

# --- Modèle pour stocker les données d'entraînement ---
class TrainingData(Base):
    __tablename__ = 'training_data'
    
    # On utilise sk_id_curr comme clé primaire, comme dans les données réelles
    sk_id_curr = Column(Integer, primary_key=True, index=True)
    data = Column(JSON, nullable=False)
    target = Column(Integer, nullable=False)

# --- Modèle pour stocker les données de test ---
class ClientDataForTest(Base):
    __tablename__ = 'test_data'

    # On utilise également sk_id_curr comme clé primaire
    sk_id_curr = Column(Integer, primary_key=True, index=True)
    data = Column(JSON, nullable=False)