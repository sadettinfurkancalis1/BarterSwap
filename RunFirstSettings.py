import psycopg2
import os

def create_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('DATABASE_NAME', 'barterswap'),
        user=os.getenv('DATABASE_USER', 'barterswap_user'),
        password=os.getenv('DATABASE_PASSWORD', 'BarterSwapSecure2025Pass'),
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=os.getenv('DATABASE_PORT', '5432')
    )
    return conn

def get_password():
    return os.getenv('PRIVATE_HASH_PASSWORD', 'default_hash_password')