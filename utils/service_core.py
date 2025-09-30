# app/utils/service_core.py

# FLUXO E A LÓGICA:
# 1. Este módulo contém funções de persistência de dados (Data Access Object - DAO) que são reutilizáveis.
# 2. A função **`insert_data_core`** executa a inserção SQL e é chamada por rotas HTTP (route_post.py) e serviços não-HTTP (get_data_camila.py).
# RAZÃO DE EXISTIR: Centralizar a lógica de persistência (DAO) de forma desacoplada, evitando duplicação de código SQL e mantendo o dependencies.py focado apenas em validação.

from typing import Dict, Any
from fastapi import HTTPException
from utils.function_execute import execute # Importa a função DAO
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def insert_data_core(table_name: str, data_to_insert: Dict[str, Any]) -> int:
    """
    Insere dados validados no DB, isolando a lógica SQL. 
    Retorna o ID do novo item ou levanta uma exceção HTTPException.
    """
    
    # 1. Construção e Execução SQL
    columns = ", ".join(data_to_insert.keys()) 
    placeholders = ", ".join(["%s"] * len(data_to_insert)) 
    values = tuple(data_to_insert.values())
    
    try:
        # SQL para INSERT seguro
        sql = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"
        new_id = execute(sql=sql, params=values) 
        
        if not new_id:
            # Erro 500 se o DB não retornar o ID (falha interna)
            raise HTTPException(status_code=500, detail=f"Não foi possível inserir os dados na tabela '{table_name}'.")

        logging.info(f"Dados inseridos em '{table_name}'. Novo ID: {new_id}")
        return new_id
    
    except HTTPException as e:
        # Propaga o erro HTTP (ex: erro no DB)
        raise e
    except Exception as e:
        # Captura erros inesperados e os transforma em erro HTTP 500
        logging.error(f"Erro inesperado no DB durante inserção em '{table_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Falha na inserção: {type(e).__name__}: {e}")