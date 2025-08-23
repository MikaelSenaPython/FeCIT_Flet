# database.py
import sqlite3
import os

def _get_db_path(page):
    return "finance.db"

def conectar(page):
    db_path = _get_db_path(page)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()

def criar_tabelas(page):
    conn, cursor = conectar(page)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT NOT NULL, descricao TEXT NOT NULL, valor REAL NOT NULL, categoria TEXT NOT NULL, data TEXT NOT NULL)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, valor_objetivo REAL NOT NULL, valor_atual REAL NOT NULL DEFAULT 0)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, tipo TEXT NOT NULL)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# --- Funções CRUD existentes (Transações, Metas, Categorias) ---
# Nenhuma mudança nas funções de adicionar, buscar, deletar e update individuais

def adicionar_transacao_db(page, tipo, descricao, valor, categoria, data):
    conn, cursor = conectar(page)
    cursor.execute("INSERT INTO transacoes (tipo, descricao, valor, categoria, data) VALUES (?, ?, ?, ?, ?)", (tipo, descricao, valor, categoria, data))
    conn.commit()
    conn.close()

def buscar_transacoes_db(page, termo_busca=None):
    """Busca transações. Se 'termo_busca' for fornecido, filtra pela descrição."""
    conn, cursor = conectar(page)
    
    query = "SELECT id, tipo, descricao, valor, categoria, data FROM transacoes"
    params = []

    if termo_busca:
        # Adiciona o filtro de busca se um termo foi passado
        query += " WHERE descricao LIKE ?"
        params.append(f"%{termo_busca}%")

    # Adiciona a ordenação no final
    query += " ORDER BY substr(data, 7, 4) || substr(data, 4, 2) || substr(data, 1, 2) DESC, id DESC"
    
    cursor.execute(query, params)
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
    cursor.execute("UPDATE transacoes SET tipo = ?, descricao = ?, valor = ?, categoria = ?, data = ? WHERE id = ?", (tipo, descricao, valor, categoria, data, id))
    conn.commit()
    conn.close()

def adicionar_meta_db(page, nome, valor_objetivo):
    conn, cursor = conectar(page)
    cursor.execute("INSERT INTO metas (nome, valor_objetivo, valor_atual) VALUES (?, ?, 0)",(nome, valor_objetivo))
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
    cursor.execute("UPDATE metas SET valor_atual = ? WHERE id = ?", (novo_valor, meta_id))
    conn.commit()
    conn.close()

def deletar_meta_db(page, meta_id):
    conn, cursor = conectar(page)
    cursor.execute("DELETE FROM metas WHERE id = ?", (meta_id,))
    conn.commit()
    conn.close()

def adicionar_categoria_db(page, nome, tipo):
    conn, cursor = conectar(page)
    cursor.execute("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", (nome, tipo))
    conn.commit()
    conn.close()

def buscar_categorias_db(page, tipo=None):
    conn, cursor = conectar(page)
    if tipo:
        cursor.execute("SELECT id, nome, tipo FROM categorias WHERE tipo = ? ORDER BY nome", (tipo,))
    else:
        cursor.execute("SELECT id, nome, tipo FROM categorias ORDER BY nome")
    categorias = cursor.fetchall()
    conn.close()
    return categorias

def deletar_categoria_db(page, categoria_id):
    conn, cursor = conectar(page)
    cursor.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
    conn.commit()
    conn.close()

def get_config_value_db(page, key):
    """Busca um valor de configuração pela chave."""
    conn, cursor = conectar(page)
    cursor.execute("SELECT value FROM app_config WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else None

def set_config_value_db(page, key, value):
    """Salva ou atualiza um valor de configuração."""
    conn, cursor = conectar(page)
    # "REPLACE INTO" insere se a chave não existe, ou atualiza se já existe
    cursor.execute("REPLACE INTO app_config (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
