from .base import *
import os
from config.settings.utils import load_env
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.db_models import Base

environment = os.getenv('ENVIRONMENT', 'production')

load_env(environment)

api_key = os.getenv('API_KEY')
host = os.getenv('HOST')
port = os.getenv('PORT')


class Database:
    def __init__(self, uri: str, db_name: str):
        self.engine = create_engine(uri)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        # Create all tables on startup
        Base.metadata.create_all(bind=self.engine)

    def is_connected(self):
        try:
            with self.engine.connect() as conn:
                return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False


# Create an instance of Database class
db = Database(os.getenv("DB_URI"), os.getenv("DB_NAME"))

if db.is_connected():
    print("Database connection is established.")
else:
    print("Failed to connect to the database.")

db_name = os.getenv("DB_NAME")

print(f"Database Name: {db_name}")