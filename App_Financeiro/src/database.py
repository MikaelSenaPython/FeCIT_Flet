# database.py
import sqlite3
import os

def _get_db_path(page):
    """Retorna o caminho completo para o arquivo do banco de dados em uma pasta específica do app."""
    # Usa o diretório "home" do usuário para garantir compatibilidade
    home_dir = os.path.expanduser("~")
    
    # Define o nome da pasta do aplicativo
    app_folder_name = "Meu App Financeiro"
    # Cria o caminho completo para a pasta do aplicativo dentro do diretório home
    app_folder_path = os.path.join(home_dir, app_folder_name)
    
    # Garante que a pasta do aplicativo exista
    if not os.path.exists(app_folder_path):
        os.makedirs(app_folder_path)
        
    # Retorna o caminho completo para o arquivo do banco de dados
    return os.path.join(app_folder_path, "finance.db")

def conectar(page):
    """Conecta ao banco de dados SQLite no caminho persistente."""
    db_path = _get_db_path(page)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()

def criar_tabela(page):
    """Cria a tabela de transações se ela não existir."""
    conn, cursor = conectar(page)
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

def adicionar_transacao_db(page, tipo, descricao, valor, categoria, data):
    """Adiciona uma nova transação ao banco de dados."""
    conn, cursor = conectar(page)
    cursor.execute(
        "INSERT INTO transacoes (tipo, descricao, valor, categoria, data) VALUES (?, ?, ?, ?, ?)",
        (tipo, descricao, valor, categoria, data)
    )
    conn.commit()
    conn.close()

def buscar_transacoes_db(page):
    """Busca e retorna todas as transações do banco de dados."""
    conn, cursor = conectar(page)
    # Ordena pela data em formato AAAA-MM-DD para garantir a ordem correta
    cursor.execute("SELECT id, tipo, descricao, valor, categoria, data FROM transacoes ORDER BY substr(data, 7, 4) || substr(data, 4, 2) || substr(data, 1, 2) DESC, id DESC")
    transacoes = cursor.fetchall()
    conn.close()
    return transacoes

def deletar_transacao_db(page, transacao_id):
    """Deleta uma transação do banco de dados pelo seu ID."""
    conn, cursor = conectar(page)
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (transacao_id,))
    conn.commit()
    conn.close()

def update_transacao_db(page, id, tipo, descricao, valor, categoria, data):
    """Atualiza uma transação existente no banco de dados."""
    conn, cursor = conectar(page)
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
