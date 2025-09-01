import flet as ft
import sqlite3
from datetime import datetime
import os

def criar_tabelas(page: ft.Page):
    """Cria as tabelas necessárias no banco de dados"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    
    # Tabela de transações
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
    
    # Tabela de categorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            tipo TEXT NOT NULL
        )
    """)
    
    # Tabela de metas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor_objetivo REAL NOT NULL,
            valor_atual REAL DEFAULT 0.0
        )
    """)
    
    # Tabela de configurações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    """)
    
    # Inserir categorias padrão
    categorias_padrao = [
        ("Salário", "Receita"),
        ("Freelance", "Receita"),
        ("Investimentos", "Receita"),
        ("Retirada de Meta", "Receita"),
        ("Alimentação", "Despesa"),
        ("Transporte", "Despesa"),
        ("Lazer", "Despesa"),
        ("Contas", "Despesa"),
        ("Depósito em Meta", "Despesa"),
    ]
    
    for nome, tipo in categorias_padrao:
        cursor.execute("INSERT OR IGNORE INTO categorias (nome, tipo) VALUES (?, ?)", (nome, tipo))
    
    conn.commit()
    conn.close()

def adicionar_transacao_db(page: ft.Page, tipo, descricao, valor, categoria, data):
    """Adiciona uma nova transação ao banco de dados"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transacoes (tipo, descricao, valor, categoria, data) VALUES (?, ?, ?, ?, ?)",
        (tipo, descricao, valor, categoria, data)
    )
    conn.commit()
    conn.close()

def buscar_transacoes_db(page: ft.Page, termo_busca=None):
    """Busca todas as transações ou filtra por termo de busca"""
    # ADICIONE A LINHA ABAIXO
    print(f"DEBUG DB: Buscando em '{os.path.abspath('financeiro.db')}'")

    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    
    if termo_busca:
        cursor.execute(
            "SELECT * FROM transacoes WHERE descricao LIKE ? ORDER BY data DESC",
            (f"%{termo_busca}%",)
        )
    else:
        cursor.execute("SELECT * FROM transacoes ORDER BY data DESC")
    
    transacoes = []
    for row in cursor.fetchall():
        transacoes.append({
            "id": row[0],
            "tipo": row[1],
            "descricao": row[2],
            "valor": row[3],
            "categoria": row[4],
            "data": row[5]
        })
    
    conn.close()
    return transacoes

def update_transacao_db(page: ft.Page, id, tipo, descricao, valor, categoria, data):
    """Atualiza uma transação existente"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE transacoes SET tipo=?, descricao=?, valor=?, categoria=?, data=? WHERE id=?",
        (tipo, descricao, valor, categoria, data, id)
    )
    conn.commit()
    conn.close()

def deletar_transacao_db(page: ft.Page, id):
    """Remove uma transação do banco de dados"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transacoes WHERE id=?", (id,))
    conn.commit()
    conn.close()

def buscar_categorias_db(page: ft.Page, tipo=None):
    """Busca categorias, opcionalmente filtradas por tipo"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    
    if tipo:
        cursor.execute("SELECT * FROM categorias WHERE tipo=? ORDER BY nome", (tipo,))
    else:
        cursor.execute("SELECT * FROM categorias ORDER BY nome")
    
    categorias = []
    for row in cursor.fetchall():
        categorias.append({
            "id": row[0],
            "nome": row[1],
            "tipo": row[2]
        })
    
    conn.close()
    return categorias

def adicionar_categoria_db(page: ft.Page, nome, tipo):
    """Adiciona uma nova categoria"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", (nome, tipo))
    conn.commit()
    conn.close()

def deletar_categoria_db(page: ft.Page, id):
    """Remove uma categoria"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categorias WHERE id=?", (id,))
    conn.commit()
    conn.close()

def buscar_metas_db(page: ft.Page):
    """Busca todas as metas"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM metas ORDER BY nome")
    
    metas = []
    for row in cursor.fetchall():
        metas.append({
            "id": row[0],
            "nome": row[1],
            "valor_objetivo": row[2],
            "valor_atual": row[3]
        })
    
    conn.close()
    return metas

def adicionar_meta_db(page: ft.Page, nome, valor_objetivo):
    """Adiciona uma nova meta"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO metas (nome, valor_objetivo) VALUES (?, ?)", (nome, valor_objetivo))
    conn.commit()
    conn.close()

def atualizar_valor_meta_db(page: ft.Page, id, novo_valor):
    """Atualiza o valor atual de uma meta"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE metas SET valor_atual=? WHERE id=?", (novo_valor, id))
    conn.commit()
    conn.close()

def deletar_meta_db(page: ft.Page, id):
    """Remove uma meta"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM metas WHERE id=?", (id,))
    conn.commit()
    conn.close()

def set_config_value_db(page: ft.Page, chave, valor):
    """Salva um valor de configuração"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", (chave, valor))
    conn.commit()
    conn.close()

def get_config_value_db(page: ft.Page, chave):
    """Recupera um valor de configuração"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracoes WHERE chave=?", (chave,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None