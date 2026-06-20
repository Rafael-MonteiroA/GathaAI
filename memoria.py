import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dados", "memoria.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(
    DB_PATH,
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS memoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    resposta TEXT
)
""")

conn.commit()


def salvar(usuario, resposta):

    cursor.execute(
        "INSERT INTO memoria (usuario,resposta) VALUES (?,?)",
        (usuario, resposta)
    )

    conn.commit()


def recuperar():

    cursor.execute("""
        SELECT usuario,resposta
        FROM memoria
        ORDER BY id DESC
        LIMIT 20
    """)

    return cursor.fetchall()


def limpar():

    cursor.execute(
        "DELETE FROM memoria"
    )

    conn.commit()
