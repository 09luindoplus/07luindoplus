import sqlite3
import re

# ============================
# 🔗 Conexão com o banco
# ============================
def get_connection():
    conn = sqlite3.connect("frota.db")
    conn.row_factory = sqlite3.Row
    return conn

# ============================
# 🗂️ Criação da tabela de usuários
# ============================
def create_user_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        perfil TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

# ============================
# 🔑 Validação de senha forte
# ============================
def validar_senha_forte(senha):
    """
    Verifica se a senha é forte:
    - Mínimo 8 caracteres
    - Pelo menos uma letra maiúscula
    - Pelo menos um número
    - Pelo menos um caractere especial
    """
    if len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r"[A-Z]", senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula."
    if not re.search(r"[0-9]", senha):
        return False, "A senha deve conter pelo menos um número."
    if not re.search(r"[@$!%*?&]", senha):
        return False, "A senha deve conter pelo menos um caractere especial (@$!%*?&)."
    return True, "Senha válida."

# ============================
# 👤 Cadastro de usuário
# ============================
def cadastrar_usuario(usuario, senha, perfil):
    valida, msg = validar_senha_forte(senha)
    if not valida:
        return False, msg

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO usuarios (usuario, senha, perfil)
        VALUES (?, ?, ?)
    """, (usuario, senha, perfil))
    conn.commit()
    conn.close()
    return True, "Usuário cadastrado com sucesso!"

# ============================
# 🚀 Inserção inicial de usuários
# ============================
def seed_usuarios_iniciais():
    conn = get_connection()
    cursor = conn.cursor()

    # Usuário Administrador
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, perfil) VALUES ('admin', 'Admin@2026', 'Administrador')")

    # Usuário Operador
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, perfil) VALUES ('operador', 'Operador@2026', 'Operador')")

    # Usuário Gestor Financeiro
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, perfil) VALUES ('financeiro', 'Financeiro@2026', 'Gestor Financeiro')")

    # Usuário Motorista
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, perfil) VALUES ('motorista', 'Motorista@2026', 'Motorista')")

    # Usuário Aluno
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, perfil) VALUES ('aluno', 'Aluno@2026', 'Aluno')")

    conn.commit()
    conn.close()


# ============================
# 📋 Listar usuários
# ============================
def listar_usuarios():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, usuario, perfil FROM usuarios ORDER BY id ASC")
    usuarios = cursor.fetchall()
    conn.close()

    lista = []
    for u in usuarios:
        lista.append({
            "id": u["id"],
            "usuario": u["usuario"],
            "perfil": u["perfil"]
        })
    return lista

# ============================
# 🔐 Validação de login
# ============================
def validar_login(usuario, senha):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT perfil FROM usuarios
        WHERE usuario = ? AND senha = ?
    """, (usuario, senha))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["perfil"]   # retorna o perfil (Administrador, Motorista, etc.)
    return None
