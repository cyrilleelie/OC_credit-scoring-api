# scripts/hash_password.py

import sys
from passlib.context import CryptContext

# Créer un contexte de mot de passe, comme dans security.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    """Génère un hash bcrypt pour un mot de passe donné."""
    return pwd_context.hash(password)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/hash_password.py <mot_de_passe_a_hasher>")
        sys.exit(1)
    
    password_to_hash = sys.argv[1]
    hashed_password = hash_password(password_to_hash)
    
    print("\n--- HASH BCRYPT VALIDE ---")
    print("Copiez la ligne suivante dans votre fichier 'src/security.py' à la place de l'ancienne valeur de 'hashed_password'.\n")
    print(hashed_password)
    print("\n--------------------------")

