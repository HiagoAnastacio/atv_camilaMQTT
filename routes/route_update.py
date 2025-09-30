# FLUXO E A LÓGICA:
# 1. Recebe 'table_name' e 'item_id' da URL.
# 2. Chama `validate_body` (Dependência CRÍTICA) para obter `data_dict` (dados seguros e limpos).
# 3. Constrói a Query SQL UPDATE dinâmica (SET {coluna} = %s).
# 4. A tupla de valores (`values`) é construída com os dados de `data_dict` + `item_id` (para o WHERE).
# 5. Chama `execute` (DAO).
# 6. Retorna 404 se o ID não for encontrado ou se o UPDATE não alterar nenhuma linha.
# A razão de existir: Fornecer um endpoint PUT genérico, seguro e capaz de fazer atualizações parciais (PATCH-like).

from fastapi import APIRouter, HTTPException, Path, Depends, Body 
from typing import Dict, Any
from utils.function_execute import execute # Importa a função DAO para acesso ao DB.
from utils.dependencies import validate_body # Importa a dependência de validação (CRÍTICA).
# from fastapi_limiter.depends import RateLimiter # Importa o limitador de taxa (Camada de Segurança).
import logging

# Variável 'router' (Escopo Global/Módulo).
router = APIRouter()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@router.put("/update/{table_name}/{item_id}", tags=["Generic Data Management"],
            #dependencies=[Depends(RateLimiter(times=5, seconds=30))]
) 
async def update_data(
    table_name: str = Path(..., description="Nome da tabela para atualização."), 
    item_id: int = Path(..., description="ID do item a ser atualizado."), 
    
    # 1. LEITURA/DOCUMENTAÇÃO (MANTIDO para o Swagger)
    request_body: Dict[str, Any] = Body(
        ...,
        description="Corpo JSON com os dados para atualizar. O schema depende da tabela."
    ),
    
    # 2. VALIDAÇÃO 
    data_dict: Dict[str, Any] = Depends(validate_body) 
):
    """Atualiza um item em uma tabela autorizada com base no ID e em um modelo Pydantic."""
    
    if not data_dict:
        # Deve ser validado pelo Pydantic/validate_body, mas é uma verificação defensiva.
        raise HTTPException(status_code=400, detail="Corpo da requisição não pode ser vazio.")
    
    # 1. Construção Dinâmica da Query SQL de UPDATE
    # Cria a parte "coluna = %s" para cada campo presente em data_dict.
    set_clauses = [f"{column} = %s" for column in data_dict.keys()]
    sql_set = ", ".join(set_clauses)
    
    # Tupla de valores para o SQL: valores dos campos + ID do item (para o WHERE).
    values = tuple(list(data_dict.values()) + [item_id])

    try:
        # CORREÇÃO CRÍTICA: Adiciona aspas graves (`) ao redor do nome da tabela e da coluna de ID.
        sql = f"UPDATE `{table_name}` SET {sql_set} WHERE `{table_name}_id` = %s"
        rows_affected = execute(sql=sql, params=values) # Envia para a camada DAO.
        
        # 2. Verificação de Resultado
        if not rows_affected:
            # Retorna 404 se o ID não existe ou se não houve alteração.
            raise HTTPException(status_code=404, detail=f"Item com ID {item_id} não encontrado ou não houve alteração.")

        return {"message": f"Item com ID {item_id} atualizado com sucesso na tabela '{table_name}'.", 
                "rows_affected": rows_affected}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Erro inesperado na rota PUT: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")