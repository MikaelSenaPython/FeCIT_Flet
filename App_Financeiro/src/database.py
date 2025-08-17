# database.py
import sqlite3
import os

def _get_db_path(page):
    """Retorna o caminho completo para o arquivo do banco de dados em uma pasta específica do app."""
    home_dir = os.path.expanduser("~")
    app_folder_name = "Meu App Financeiro"
    app_folder_path = os.path.join(home_dir, app_folder_name)
    
    if not os.path.exists(app_folder_path):
        os.makedirs(app_folder_path)
        
    return os.path.join(app_folder_path, "finance.db")

def conectar(page):
    """Conecta ao banco de dados SQLite no caminho persistente."""
    db_path = _get_db_path(page)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()

def criar_tabelas(page):
    """Cria as tabelas de transações e metas se elas não existirem."""
    conn, cursor = conectar(page)
    # Tabela de Transações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            categoria TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)
    # Tabela de Metas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor_objetivo REAL NOT NULL,
            valor_atual REAL NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# --- Funções de Transações ---

def adicionar_transacao_db(page, tipo, descricao, valor, categoria, data):
    conn, cursor = conectar(page)
    cursor.execute(
        "INSERT INTO transacoes (tipo, descricao, valor, categoria, data) VALUES (?, ?, ?, ?, ?)",
        (tipo, descricao, valor, categoria, data)
    )
    conn.commit()
    conn.close()

def buscar_transacoes_db(page):
    conn, cursor = conectar(page)
    cursor.execute("SELECT id, tipo, descricao, valor, categoria, data FROM transacoes ORDER BY substr(data, 7, 4) || substr(data, 4, 2) || substr(data, 1, 2) DESC, id DESC")
    transacoes = cursor.fetchall()
    conn.close()
    return transacoes

def deletar_transacao_db(page, transacao_id):
    conn, cursor = conectar(page)
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (transacao_id,))
    conn.commit()
    conn.close()

def update_transacao_db(page, id, tipo, descricao, valor, categoria, data):
    conn, cursor = conectar(page)
    cursor.execute(
        "UPDATE transacoes SET tipo = ?, descricao = ?, valor = ?, categoria = ?, data = ? WHERE id = ?",
        (tipo, descricao, valor, categoria, data, id)
    )
    conn.commit()
    conn.close()

# --- Funções de Metas ---

def adicionar_meta_db(page, nome, valor_objetivo):
    conn, cursor = conectar(page)
    cursor.execute(
        "INSERT INTO metas (nome, valor_objetivo, valor_atual) VALUES (?, ?, 0)",
        (nome, valor_objetivo)
    )
    conn.commit()
    conn.close()

def buscar_metas_db(page):
    conn, cursor = conectar(page)
    cursor.execute("SELECT id, nome, valor_objetivo, valor_atual FROM metas ORDER BY id DESC")
    metas = cursor.fetchall()
    conn.close()
    return metas

def atualizar_valor_meta_db(page, meta_id, novo_valor):
    conn, cursor = conectar(page)
    cursor.execute(
        "UPDATE metas SET valor_atual = ? WHERE id = ?",
        (novo_valor, meta_id)
    )
    conn.commit()
    conn.close()

def deletar_meta_db(page, meta_id):
    conn, cursor = conectar(page)
    cursor.execute("DELETE FROM metas WHERE id = ?", (meta_id,))
    conn.commit()
    conn.close()
