# config.py
import os
from dotenv import load_dotenv

load_dotenv()

PG = {
    'host': os.getenv('POSTGRES_HOST'),
    'db': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD')
}