# FLUXO E A LÓGICA:
# 1. Inicializa o objeto de conexão com o banco de dados (Database).
# 2. A função 'execute' encapsula a execução SQL.
# 3. 'execute' realiza a conexão, chama o método do DB, e desconecta.
# 4. Trata erros do DB, transformando-os em HTTPException 500 DETALHADO.

from fastapi import HTTPException 
from model.db import Database 

# Inicializa o objeto de banco de dados globalmente
db = Database()

def execute(sql: str, params: tuple = None): 
    """
    Executa um comando SQL usando a conexão do banco (Database).
    """
    try:
        db.connect() # Tentará a conexão, e levantará o erro de conexão se falhar (graças à correção em db.py).
        result = db.execute_comand(sql, params) 
        db.disconnect() 
        return result 
    except Exception as e:
        # Garante que a conexão seja sempre fechada, mesmo em caso de erro
        db.disconnect() 
        
        # --- BLOCO CRÍTICO PARA DEBUG: REVELA O ERRO ---
        detail_message = f"Erro no banco de dados: {type(e).__name__}: {e}"
        print(f"DEBUG SQL ERRO 500: {detail_message}") # Imprime o erro no seu console/terminal
        
        # Lança erro HTTP 500 para o FastAPI com a mensagem detalhada do MySQL
        raise HTTPException(status_code=500, detail=detail_message)