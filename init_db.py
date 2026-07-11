import sqlite3
import os
from utils.db import create_tables
from utils.auth import create_user_table, seed_usuarios_iniciais

def init_database():
    try:
        db_path = os.getenv("SQLITE_DB_PATH", "frota.db")
        conn = sqlite3.connect(db_path)
        conn.close()

        create_tables()
        create_user_table()
        seed_usuarios_iniciais()

        print("Banco inicializado com sucesso!")
    except Exception as e:
        print("Erro ao inicializar banco:", e)

if __name__ == "__main__":
    init_database()
