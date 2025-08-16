# database.py
import sqlite3

DB_FILE = "finance.db"

def conectar():
    """Conecta ao banco de dados SQLite e retorna a conexão e o cursor."""
    conn = sqlite3.connect(DB_FILE)
    # Retorna os resultados como tuplas que podem ser acessadas por nome de coluna
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()

def criar_tabela():
    """Cria a tabela de transações se ela não existir."""
    conn, cursor = conectar()
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
    conn.commit()
    conn.close()

def adicionar_transacao_db(tipo, descricao, valor, categoria, data):
    """Adiciona uma nova transação ao banco de dados."""
    conn, cursor = conectar()
    cursor.execute(
        "INSERT INTO transacoes (tipo, descricao, valor, categoria, data) VALUES (?, ?, ?, ?, ?)",
        (tipo, descricao, valor, categoria, data)
    )
    conn.commit()
    conn.close()

def buscar_transacoes_db():
    """Busca e retorna todas as transações do banco de dados."""
    conn, cursor = conectar()
    cursor.execute("SELECT id, tipo, descricao, valor, categoria, data FROM transacoes ORDER BY data DESC, id DESC")
    transacoes = cursor.fetchall()
    conn.close()
    return transacoes

def deletar_transacao_db(transacao_id):
    """Deleta uma transação do banco de dados pelo seu ID."""
    conn, cursor = conectar()
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (transacao_id,))
    conn.commit()
    conn.close()

# --- NOVA FUNÇÃO AQUI ---
def update_transacao_db(id, tipo, descricao, valor, categoria, data):
    """Atualiza uma transação existente no banco de dados."""
    conn, cursor = conectar()
    cursor.execute(
        """
        UPDATE transacoes
        SET tipo = ?, descricao = ?, valor = ?, categoria = ?, data = ?
        WHERE id = ?
        """,
        (tipo, descricao, valor, categoria, data, id)
    )
    conn.commit()
    conn.close()

# Garante que a tabela seja criada na primeira vez que o módulo for importado
criar_tabela()