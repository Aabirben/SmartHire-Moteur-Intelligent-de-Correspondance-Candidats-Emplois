import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            sslmode=os.getenv('DB_SSL')
        )
        print("Connexion à la base de données établie avec succès!")
        return conn
    except Exception as e:
        print(f"Erreur de connexion à la base de données: {e}")
        return None