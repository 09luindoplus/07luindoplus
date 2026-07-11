from datetime import datetime
import sqlite3
import utils.db as db

# ============================
# 🔗 Conexão com o Banco
# ============================
def get_connection():
    conn = sqlite3.connect("frota.db")
    conn.row_factory = sqlite3.Row
    return conn

# ============================
# 🏗️ Criação de Tabelas
# ============================

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela alunos
    cursor.execute("""
CREATE TABLE IF NOT EXISTS alunos (
    id_aluno INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,                 -- Nome completo do aluno
    classe TEXT NOT NULL,               -- Classe escolar
    encarregado TEXT NOT NULL,          -- Nome do encarregado    telefone TEXT,                      -- Telefone do encarregado
    id_rota INTEGER NOT NULL,           -- FK para rotas
    rota TEXT NOT NULL,                 -- Nome da rota (redundância para facilitar relatórios)
    periodo TEXT,                       -- Manhã / Tarde
    ultimo_mes TEXT,                    -- Último mês pago (ex: '2026-09')
    status TEXT DEFAULT 'Inativo',      -- Ativo ou Inativo
    adesao TEXT NOT NULL,
    data_adesao DATE NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_rota) REFERENCES rotas(id_rota)
); """)

    # Tabela rotas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rotas (
        id_rota INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco REAL NOT NULL
    );
    """)

    # Tabela faturas
    cursor.execute("""

CREATE TABLE IF NOT EXISTS faturas (
        id_fatura INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_fatura TEXT UNIQUE NOT NULL,
        id_aluno INTEGER NOT NULL,
        id_rota INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        mes TEXT,
        valor REAL NOT NULL,
        valor_pago REAL NOT NULL,
        remanescente REAL NOT NULL,
        metodo TEXT NOT NULL,
        data_pagamento DATE NOT NULL,
        observacoes TEXT,
        status TEXT NOT NULL,
        taxa_extra REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_aluno) REFERENCES alunos(id_aluno),
        FOREIGN KEY (id_rota) REFERENCES rotas(id_rota)
    );
    """)

    conn.commit()
    conn.close()


def criar_tabelas():
    conn = get_connection()
    cursor = conn.cursor()

    # Criar tabela de notificações se não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notificacoes (
            id_notificacao INTEGER PRIMARY KEY AUTOINCREMENT,
            mensagem TEXT NOT NULL,
            tipo TEXT NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    conn.commit()
    conn.close()


def inserir_aluno(nome, encarregado, telefone, rota, periodo, classe, status="Ativo"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alunos (nome, encarregado, telefone, rota, periodo, classe, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nome, encarregado, telefone, rota, periodo, classe, status))
    conn.commit()
    conn.close()


    # Motoristas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS motoristas (
            id_motorista INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            viatura INTEGER,
            status TEXT DEFAULT 'Ativo',
            FOREIGN KEY (viatura) REFERENCES viaturas(id_viatura) ON DELETE SET NULL
        )
    """)
def registrar_notificacao(mensagem, tipo="info"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notificacoes (mensagem, tipo)
        VALUES (?, ?)
    """, (mensagem, tipo))
    conn.commit()
    conn.close()

def listar_notificacoes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_notificacao, mensagem, tipo, data
        FROM notificacoes
        ORDER BY data DESC
    """)
    notificacoes = cursor.fetchall()
    conn.close()
    return notificacoes

def listar_alunos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            a.id_aluno,
            a.nome,
            a.classe,
            a.periodo,
            r.nome AS nome_rota,
            a.id_rota,
            a.encarregado,
            a.telefone,
            a.status,
            COALESCE(MAX(f.mes), 'Sem pagamento') AS ultimo_mes_pago,
            r.preco AS valor_rota,
            ta.tipo AS tipo_adesao,
            ad.data AS data_adesao
        FROM alunos a
        LEFT JOIN faturas f ON a.id_aluno = f.id_aluno
        LEFT JOIN rotas r ON a.id_rota = r.id_rota
        LEFT JOIN adesoes ad ON a.id_aluno = ad.id_aluno
        LEFT JOIN tipos_adesao ta ON ad.id_tipo = ta.id
        GROUP BY a.id_aluno, a.nome, a.classe, a.periodo,
                 a.id_rota, r.nome, a.encarregado,
                 a.telefone, a.status, r.preco, ta.tipo, ad.data
        ORDER BY a.nome ASC;
    """)
    resultados = cursor.fetchall()
    conn.close()

    alunos = []
    for row in resultados:
        alunos.append({
            "id_aluno": row[0],
            "nome": row[1],
            "classe": row[2],
            "periodo": row[3],
            "nome_rota": row[4] if row[4] else "Sem rota",
            "id_rota": row[5],
            "encarregado": row[6],
            "telefone": row[7],
            "status": row[8],
            "ultimo_mes_pago": row[9],
            "valor_rota": row[10] if row[10] else 0,
            "tipo_adesao": row[11] if row[11] else "Sem adesão",
            "data_adesao": row[12] if row[12] else "-"
        })
    return alunos

def tabela_existe(nome_tabela):
    """Verifica se uma tabela existe no banco SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (nome_tabela,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None

# ✅ Função para cadastrar tipo de adesão
def cadastrar_tipo_adesao(tipo, valor):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tipos_adesao (tipo, valor)
        VALUES (?, ?)
    """, (tipo, valor))
    conn.commit()
    conn.close()


def atualizar_adesao_aluno(id_aluno, tipo_adesao, data_adesao):
    """
    Atualiza ou adiciona o tipo de adesão e a data de adesão
    na tabela alunos para o aluno especificado.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE alunos
        SET adesao = ?, data_adesao = ?
        WHERE id_aluno = ?
    """, (tipo_adesao, data_adesao, id_aluno))

    conn.commit()
    conn.close()
# ✅ Função para listar tipos de adesão
def listar_tipos_adesao():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tipo, valor FROM tipos_adesao")
    tipos = cursor.fetchall()
    conn.close()
    return tipos

# ✅ Função para remover tipo de adesão
def remover_tipo_adesao(id_tipo):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tipos_adesao WHERE id = ?", (id_tipo,))
    conn.commit()
    conn.close()

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # ---------------------------
    # Tabela de tipos de adesão (catálogo)
    # ---------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tipos_adesao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        valor REAL NOT NULL
    );
    """)

    # ---------------------------
    # Tabela de adesões (ligação aluno ↔ tipo)
    # ---------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS adesoes (
        id_adesao INTEGER PRIMARY KEY AUTOINCREMENT,
        id_aluno INTEGER NOT NULL,
        id_tipo INTEGER NOT NULL,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_aluno) REFERENCES alunos(id_aluno),
        FOREIGN KEY (id_tipo) REFERENCES tipos_adesao(id)
    );
    """)

    conn.commit()
    conn.close()


def listar_rotas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_rota, nome, preco
        FROM rotas
        ORDER BY nome ASC
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados

def listar_alunos_paginado(offset, limit):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_aluno, nome, classe, encarregado,periodo,rota
        FROM alunos
        ORDER BY nome ASC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    dados = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM alunos")
    total = cursor.fetchone()[0]
    conn.close()

    alunos = []
    for row in dados:
        alunos.append({
            "id_aluno": row[0],   # mantém o nome real da coluna
            "nome": row[1],
            "classe": row[2],
            "encarregado": row[3],
            "periodo": row[4],
            "rota": row[5]



        })
    return alunos, total

def buscar_alunos_autocomplete(termo):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            a.id_aluno,
            a.nome,
            a.classe,
            a.periodo,
            a.encarregado,
            a.telefone,
            a.status,
            COALESCE(MAX(f.mes), 'Sem pagamento') AS ultimo_mes_pago,
            r.nome AS nome_rota,
            r.preco AS valor_rota,
            a.id_rota
        FROM alunos a
        LEFT JOIN faturas f ON a.id_aluno = f.id_aluno
        LEFT JOIN rotas r ON a.id_rota = r.id_rota
        WHERE a.id_aluno LIKE ? OR a.nome LIKE ? OR a.encarregado LIKE ?
        GROUP BY a.id_aluno, a.nome, a.classe, a.periodo,
                 a.encarregado, a.telefone, a.status,
                 r.nome, r.preco, a.id_rota
        ORDER BY a.nome ASC
        LIMIT 10
    """, (f"{termo}%", f"{termo}%", f"{termo}%"))

    resultados = cursor.fetchall()
    conn.close()

    alunos = []
    for row in resultados:
        alunos.append({
            "id": row["id_aluno"],            # JS espera aluno.id
            "nome": row["nome"],
            "classe": row["classe"],
            "periodo": row["periodo"],
            "encarregado": row["encarregado"],
            "telefone": row["telefone"],
            "status": row["status"],
            "ultimo_mes_pago": row["ultimo_mes_pago"],
            "nome_rota": row["nome_rota"],
            "valor_rota": row["valor_rota"],
            "id_rota": row["id_rota"]
        })
    return alunos


def buscar_aluno(id_aluno):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alunos WHERE id_aluno = ?", (id_aluno,))
    aluno = cursor.fetchone()
    conn.close()
    return aluno

def inserir_rota(nome, preco):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rotas (nome, preco)
        VALUES (?, ?)
    """, (nome, preco))
    conn.commit()
    conn.close()


def obter_rota(id_rota):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM rotas WHERE id_rota = ?", (id_rota,))
    rota = cursor.fetchone()
    conn.close()

    return dict(rota) if rota else None


def valor_rota(id_rota):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT preco FROM rotas WHERE id_rota = ?", (id_rota,))
    rota = cursor.fetchone()
    conn.close()

    # Se não encontrar rota devolve None
    return rota["preco"] if rota else None

def relatorio_rotas_com_detalhes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id_rota, r.nome, r.preco,
               COUNT(a.id_aluno) AS total_alunos,
               SUM(CASE WHEN a.status='Inativo' THEN 1 ELSE 0 END) AS inativos,
               SUM(CASE WHEN a.status='Desistente' THEN 1 ELSE 0 END) AS desistentes
        FROM rotas r
        LEFT JOIN alunos a ON r.id_rota = a.rota
        GROUP BY r.id_rota, r.nome, r.preco
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados

def alunos_por_rota(id_rota):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alunos WHERE rota=? ORDER BY nome", (id_rota,))
    dados = cursor.fetchall()
    conn.close()
    return dados

    # Viaturas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS viaturas (
            id_viatura INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT NOT NULL,
            matricula TEXT NOT NULL,
            capacidade INTEGER,
            status TEXT DEFAULT 'Ativo'
        )
    """)


def inativar_aluno(id_aluno):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alunos SET status = 'Inativo' WHERE id_aluno = ?", (id_aluno,))
    conn.commit()
    conn.close()


def atualizar_aluno(id_aluno, nome, encarregado, telefone, rota, periodo, classe, status):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alunos
            SET nome = ?, encarregado = ?, telefone = ?, rota = ?, periodo = ?, classe = ?, status = ?
            WHERE id_aluno = ?
        """, (nome, encarregado, telefone, rota, periodo, classe, status, id_aluno))
        conn.commit()

    # Financeiro
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mes TEXT,
        valor_pago REAL,
        despesa REAL
    )
    """)

    # Períodos letivos (bi-anual)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS periodos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ano TEXT NOT NULL,
        inicio TEXT NOT NULL,
        fim TEXT NOT NULL
    )
    """)

    # Inserir período 25/26 se não existir
    cursor.execute("""
    INSERT OR IGNORE INTO periodos (ano, inicio, fim)
    VALUES ('25/26', '2025-09-01', '2026-07-31')
    """)

    conn.commit()
    conn.close()

def listar_alunos_filtrados(classe=None, status=None, ano=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT id_aluno, nome, classe, encarregado, status, ano FROM alunos WHERE 1=1"
    params = []

    if classe:
        query += " AND classe = ?"
        params.append(classe)
    if status:
        query += " AND status = ?"
        params.append(status)
    if ano:
        query += " AND ano = ?"
        params.append(ano)

    cursor.execute(query, params)
    resultados = cursor.fetchall()
    conn.close()
    return [dict(row) for row in resultados]



# ============================
# 👨‍🎓 Funções Alunos
# ============================
def cadastrar_aluno(nome, classe, encarregado, id_rota, valor, periodo, telefone, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alunos (nome, classe, encarregado, id_rota, valor, periodo, telefone, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, classe, encarregado, id_rota, valor, periodo, telefone, status))
    conn.commit()
    conn.close()

def inativar_aluno(id_aluno):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alunos SET status = 'Inativo' WHERE id_aluno = ?", (id_aluno,))
    conn.commit()
    conn.close()


def listar_rotas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_rota, nome, preco
        FROM rotas
        ORDER BY nome ASC
    """)
    rotas = cursor.fetchall()
    conn.close()
    return rotas

def relatorio_alunos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_aluno, nome, classe, periodo, rota, encarregado, telefone, status
        FROM alunos
        ORDER BY nome ASC
    """)
    alunos = cursor.fetchall()
    conn.close()
    return alunos


# ============================
# 🚐 Funções Motoristas
# ============================
def cadastrar_motorista(nome, telefone, carta):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO motoristas (nome, telefone, carta) VALUES (?, ?, ?)",
                   (nome, telefone, carta))
    conn.commit()
    conn.close()

def relatorio_motoristas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM motoristas")
    motoristas = cursor.fetchall()
    conn.close()
    return motoristas

# ============================
# 🚍 Funções Viaturas
# ============================
def cadastrar_viatura(matricula, modelo, capacidade):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO viaturas (matricula, modelo, capacidade) VALUES (?, ?, ?)",
                   (matricula, modelo, capacidade))
    conn.commit()
    conn.close()

def relatorio_viaturas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM viaturas")
    viaturas = cursor.fetchall()
    conn.close()
    return viaturas


def registrar_notificacao(mensagem, tipo="info"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notificacoes (mensagem, tipo)
        VALUES (?, ?)
    """, (mensagem, tipo))
    conn.commit()
    conn.close()

# ============================
# 🛣️ Funções Rotas
# ============================

def cadastrar_rota(nome, preco):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rotas (nome, preco)
        VALUES (?, ?)
    """, (nome, preco))
    conn.commit()
    conn.close()

def relatorio_rotas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_rota, nome, preco
        FROM rotas
        ORDER BY nome ASC
    """)
    rotas = cursor.fetchall()
    conn.close()
    return rotas

# ============================
# 💳 Funções Faturas
# ============================


def obter_ultima_fatura(id_aluno):
    conn = get_connection()
    conn.row_factory = sqlite3.Row  # permite acessar colunas por nome
    cursor = conn.cursor()

    cursor.execute("""
        SELECT f.id_fatura, f.numero_fatura, f.tipo, f.mes, f.valor, f.valor_pago,
               f.remanescente, f.metodo, f.data_pagamento, f.observacoes,
               a.nome, a.classe, a.encarregado, a.rota, a.ultimo_mes, a.status,
               r.nome AS rota_nome, r.preco,
               (f.valor + COALESCE(f.taxa_extra, 0)) AS valor_total
        FROM faturas f
        JOIN alunos a ON f.id_aluno = a.id_aluno
        JOIN rotas r ON f.id_rota = r.id_rota
        WHERE f.id_aluno = ?
        ORDER BY f.id_fatura DESC
        LIMIT 1
    """, (id_aluno,))

    fatura = cursor.fetchone()
    conn.close()

    if fatura:
        return dict(fatura)  # converte Row para dict
    return None


# -------------------------------
# Rota para emitir fatura
# -------------------------------
def registrar_fatura(id_pagamento, numero_fatura, valor, metodo, data_pagamento):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO faturas (id_pagamento, numero_fatura, valor, metodo, data_pagamento, status)
        VALUES (?, ?, ?, ?, ?, 'Pago')
    """, (id_pagamento, numero_fatura, valor, metodo, data_pagamento))
    conn.commit()
    conn.close()
def relatorio_faturas():
    conn = sqlite3.connect("frota.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            f.id_fatura,
            f.numero_fatura,
            a.id_aluno,
            a.nome AS nome_aluno,
            a.classe,
            a.encarregado,
            f.tipo AS descricao_contrato,
            CASE
                WHEN f.tipo IN ('Adesão','Confirmação','Taxa de Reativação')
                THEN f.tipo
                ELSE f.mes
            END AS descricao_tipo,
            f.valor,
            f.valor_pago,
            f.metodo,
            f.data_pagamento,
            CASE
                WHEN f.valor_pago < f.valor THEN 'Parcial'
                WHEN f.valor_pago = f.valor THEN 'Pago'
                ELSE 'Crédito'
            END AS status
        FROM faturas f
        JOIN alunos a ON f.id_aluno = a.id_aluno
        ORDER BY f.data_pagamento DESC;
    """)

    faturas = cursor.fetchall()
    conn.close()
    return [dict(row) for row in faturas]

def inserir_fatura(numero_fatura, id_aluno, id_rota, tipo, mes, valor, valor_pago,
                   remanescente, metodo, data_pagamento, observacoes, status, taxa_extra):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO faturas (
            numero_fatura, id_aluno, id_rota, tipo, mes, valor, valor_pago,
            remanescente, metodo, data_pagamento, observacoes, status, taxa_extra
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (numero_fatura, id_aluno, id_rota, tipo, mes, valor, valor_pago,
          remanescente, metodo, data_pagamento, observacoes, status, taxa_extra))

    conn.commit()
    conn.close()


def atualizar_status_aluno(id_aluno, novo_status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE alunos
        SET status = ?
        WHERE id_aluno = ?
    """, (novo_status, id_aluno))

    conn.commit()
    conn.close()


def buscar_aluno_por_id(id_aluno):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alunos WHERE id_aluno = ?", (id_aluno,))
    aluno = cursor.fetchone()

    conn.close()
    return dict(aluno) if aluno else None


# -------------------------------
# Função para gerar número único da fatura
# -------------------------------
def gerar_numero_fatura():
    ano = datetime.now().year
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id_fatura) FROM faturas")
    ultimo_id = cursor.fetchone()[0]
    conn.close()
    if ultimo_id is None:
        ultimo_id = 0
    return f"FT-{ano}-{ultimo_id + 1:03d}"

# -------------------------------
# Inserir fatura
# -------------------------------
def inserir_fatura(mes, descricao, valor, valor_pago, remanescente, metodo, data_pagamento, id_aluno, observacoes):
    numero_fatura = gerar_numero_fatura()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO faturas (numero_fatura, mes, descricao, valor, valor_pago, remanescente, metodo, data_pagamento, id_aluno, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (numero_fatura, mes, descricao, valor, valor_pago, remanescente, metodo, data_pagamento, id_aluno, observacoes))
    conn.commit()
    conn.close()


# -------------------------------
# Obter fatura específica
# -------------------------------
def obter_fatura(id_fatura):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.id_fatura, f.numero_fatura, f.mes, f.descricao, f.valor, f.valor_pago,
               f.remanescente, f.metodo, f.data_pagamento, f.observacoes,
               a.id_aluno, a.nome AS aluno
        FROM faturas f
        JOIN alunos a ON f.id_aluno = a.id_aluno
        WHERE f.id_fatura = ?
    """, (id_fatura,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado

def listar_faturas():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            f.id_fatura,
            f.numero_fatura,
            f.tipo AS descricao_contrato,
            CASE
                WHEN f.tipo IN ('Adesão','Confirmação','Taxa de Reativação')
                THEN f.tipo
                ELSE f.mes
            END AS descricao_tipo,
            f.valor,
            f.valor_pago,
            f.remanescente,
            f.metodo,
            f.data_pagamento,
            f.status,
            a.id_aluno,
            a.nome AS nome_aluno,
            a.classe,
            a.encarregado,
            r.nome AS rota
        FROM faturas f
        JOIN alunos a ON f.id_aluno = a.id_aluno
        LEFT JOIN rotas r ON a.id_rota = r.id_rota
        ORDER BY f.id_fatura DESC
    """)
    resultados = cursor.fetchall()
    conn.close()
    return [dict(row) for row in resultados]

# -------------------------------
# Obter dados para recibo/pagamento
# -------------------------------
def obter_dados_pagamento(id_fatura):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            f.id_fatura,
            f.numero_fatura,
            f.tipo,
            f.mes,
            f.valor,
            f.valor_pago,
            f.remanescente,
            f.metodo,
            f.data_pagamento,
            f.status,
            a.id_aluno,
            a.nome AS nome_aluno,
            a.classe,
            a.encarregado,
            r.nome AS rota
        FROM faturas f
        JOIN alunos a ON f.id_aluno = a.id_aluno
        LEFT JOIN rotas r ON a.id_rota = r.id_rota
        WHERE f.id_fatura = ?
    """, (id_fatura,))
    dados = cursor.fetchone()
    conn.close()
    return dict(dados) if dados else None


def obter_aluno(id_aluno):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alunos WHERE id_aluno=?", (id_aluno,))
    dados = cursor.fetchone()
    conn.close()
    return dados

def atualizar_fatura(id_fatura, id_aluno, valor, metodo, data_pagamento, observacoes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE faturas
        SET id_aluno=?, valor=?, metodo=?, data_pagamento=?, observacoes=?
        WHERE id_fatura=?
    """, (id_aluno, valor, metodo, data_pagamento, observacoes, id_fatura))
    conn.commit()
    conn.close()


def inserir_fatura(tipo, mes, valor, valor_pago, remanescente, metodo, data_pagamento, id_aluno, id_rota, observacoes=None, taxa_extra=None):
    conn = get_connection()
    cursor = conn.cursor()

    # Gerar número único da fatura (exemplo: FAT-2026-001)
    cursor.execute("SELECT COUNT(*) FROM faturas")
    total = cursor.fetchone()[0] + 1
    numero_fatura = f"FAT-{total:05d}"

    cursor.execute("""
        INSERT INTO faturas (
            numero_fatura, id_aluno, id_rota, tipo, mes, valor, valor_pago,
            remanescente, metodo, data_pagamento, observacoes, status, taxa_extra
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        numero_fatura, id_aluno, id_rota, tipo, mes, valor, valor_pago,
        remanescente, metodo, data_pagamento, observacoes, 
        "Pago" if remanescente <= 0 else "Pendente",
        taxa_extra
    ))

    conn.commit()
    conn.close()



# ============================
# 📑 Relatórios Financeiros
# ============================
def relatorio_financeiro_bi_anual(ano):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT strftime('%m', data_emissao) as mes,
               SUM(valor) as receita
        FROM faturas
        WHERE data_emissao BETWEEN
              (SELECT inicio FROM periodos WHERE ano = ?)
              AND
              (SELECT fim FROM periodos WHERE ano = ?)
        GROUP BY mes
        ORDER BY mes
    """, (ano, ano))
    dados = cursor.fetchall()
    conn.close()
    return dados

def relatorio_financeiro_pagamento(ano):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT forma_pagamento, SUM(valor) AS total
        FROM faturas
        WHERE strftime('%Y', data_emissao) = ?
        GROUP BY forma_pagamento
    """

    cursor.execute(query, (str(ano),))
    dados = cursor.fetchall()
    conn.close()

    # Converte para lista de dicionários
    resultado = []
    for linha in dados:
        resultado.append({
            "forma_pagamento": linha[0],
            "total": linha[1]
        })
    return resultado

def relatorio_contabilistico_bi_anual(ano, rota=None, periodo=None):
    conn = get_connection()
    cursor = conn.cursor()

    # Filtros dinâmicos
    filtros = ["strftime('%Y', data_emissao) = ?"]
    params = [str(ano)]

    if rota:
        filtros.append("rota = ?")
        params.append(rota)

    if periodo:
        filtros.append("periodo = ?")  # coluna 'periodo' deve existir na tabela
        params.append(periodo)

    where_clause = " AND ".join(filtros)

    # Relatório bi-anual: Setembro → Julho
    query = f"""
        SELECT CASE 
                 WHEN strftime('%m', data_emissao) IN ('09','10','11','12') THEN 'Set-Dez'
                 WHEN strftime('%m', data_emissao) IN ('01','02','03') THEN 'Jan-Mar'
                 WHEN strftime('%m', data_emissao) IN ('04','05','06','07') THEN 'Abr-Jul'
               END AS periodo,
               SUM(valor) AS total
        FROM faturas
        WHERE {where_clause}
        GROUP BY periodo
        ORDER BY periodo
    """

    cursor.execute(query, tuple(params))
    dados = cursor.fetchall()
    conn.close()
    return dados


def relatorio_contabilistico(ano, tipo="mensal", rota=None, mes=None, periodo=None):
    conn = get_connection()
    cursor = conn.cursor()

    filtros = ["strftime('%Y', data_emissao) = ?"]
    params = [str(ano)]

    if rota:
        filtros.append("rota = ?")
        params.append(rota)

    if mes:
        filtros.append("strftime('%m', data_emissao) = ?")
        params.append(str(mes).zfill(2))

    if periodo:
        filtros.append("periodo = ?")  # coluna 'periodo' deve existir na tabela
        params.append(periodo)

    where_clause = " AND ".join(filtros)

    if tipo == "mensal":
        query = f"""
            SELECT strftime('%m', data_emissao) AS periodo, SUM(valor) AS total
            FROM faturas WHERE {where_clause}
            GROUP BY periodo ORDER BY periodo
        """
    elif tipo == "trimestral":
        query = f"""
            SELECT ((strftime('%m', data_emissao)-1)/3 + 1) AS periodo, SUM(valor) AS total
            FROM faturas WHERE {where_clause}
            GROUP BY periodo ORDER BY periodo
        """
    elif tipo == "semestral":
        query = f"""
            SELECT CASE WHEN strftime('%m', data_emissao) BETWEEN '01' AND '06' THEN '1º Semestre'
                        ELSE '2º Semestre' END AS periodo, SUM(valor) AS total
            FROM faturas WHERE {where_clause}
            GROUP BY periodo ORDER BY periodo
        """
    elif tipo == "anual":
        query = f"""
            SELECT strftime('%Y', data_emissao) AS periodo, SUM(valor) AS total
            FROM faturas WHERE {where_clause}
            GROUP BY periodo
        """

    cursor.execute(query, tuple(params))
    dados = cursor.fetchall()
    conn.close()
    return dados



def relatorio_por_pagamento(ano, tipo="mensal", forma_pagamento=None):
    conn = get_connection()
    cursor = conn.cursor()

    filtros = ["strftime('%Y', data_emissao) = ?"]
    params = [str(ano)]

    if forma_pagamento:
        filtros.append("forma_pagamento = ?")  # coluna 'forma_pagamento' na tabela faturas
        params.append(forma_pagamento)

    where_clause = " AND ".join(filtros)

    if tipo == "mensal":
        query = f"""
            SELECT strftime('%m', data_emissao) AS periodo, SUM(valor) AS total
            FROM faturas WHERE {where_clause}
            GROUP BY periodo ORDER BY periodo
        """
    elif tipo == "anual":
        query = f"""
            SELECT strftime('%Y', data_emissao) AS periodo, SUM(valor) AS total
            FROM faturas WHERE {where_clause}
            GROUP BY periodo
        """

    cursor.execute(query, tuple(params))
    dados = cursor.fetchall()
    conn.close()
    return dados
# ============================
# 📊 Resumo para Dashboard
# ============================




def obter_resumo():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    resumo = {}

    # Contagens básicas
    cursor.execute("SELECT COUNT(*) as total FROM alunos")
    resumo["alunos"] = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM motoristas")
    resumo["motoristas"] = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM viaturas")
    resumo["viaturas"] = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM rotas")
    resumo["rotas"] = cursor.fetchone()["total"]

    # Receita: somatório dos valores pagos
    cursor.execute("SELECT SUM(valor_pago) as receita FROM faturas")
    receita = cursor.fetchone()["receita"]
    resumo["receita"] = receita if receita else 0

    # Em aberto: somatório dos remanescentes
    cursor.execute("SELECT SUM(remanescente) as em_aberto FROM faturas")
    em_aberto = cursor.fetchone()["em_aberto"]
    resumo["em_aberto"] = em_aberto if em_aberto else 0

    conn.close()
    return resumo# ============================
# 📅 Período Letivo Atual
# ============================
def obter_periodo_atual():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ano, inicio, fim FROM periodos
        WHERE date('now') BETWEEN inicio AND fim
    """)
    periodo = cursor.fetchone()
    conn.close()
    return periodo

