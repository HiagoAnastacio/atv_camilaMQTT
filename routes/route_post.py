# FLUXO E A LÓGICA:
# 1. Recebe 'table_name' da URL e o corpo via `request_body` (Escopo de Requisição).
# 2. Chama `validate_body` (Dependência) para obter o dicionário seguro `data_dict`.
# 3. Constrói a *query* SQL `INSERT` dinamicamente usando as chaves e valores de `data_dict`.
# 4. Chama `execute` (DAO) para rodar o comando SQL.
# A razão de existir: Ponto de entrada para a operação de escrita (POST) de forma GENÉRICA.

from fastapi import APIRouter, HTTPException, Path, Depends, Body 
from typing import Dict, Any
from utils.function_execute import execute
import logging 
from utils.dependencies import validate_body # Importa a dependência de validação (Camada de Lógica).
# from fastapi_limiter.depends import RateLimiter # Importa o limitador de taxa (Camada de Segurança).

# Variável 'router' (Escopo Global/Módulo): Objeto APIRouter para agrupar rotas.
router = APIRouter()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Configuração básica de log.

# Rota para inserir dados genéricos: /insert/{table_name}
@router.post("/insert/{table_name}", tags=["Generic Data Management"], 
            #dependencies=[Depends(RateLimiter(times=5, seconds=30))] # Camada de segurança (comentado/desativado).
) 
async def insert_data(
    table_name: str = Path(..., description="Nome da tabela para inserção."), 
    
    # 1. LEITURA/DOCUMENTAÇÃO (MANTIDO para o Swagger)
    request_body: Dict[str, Any] = Body(
        ...,
        description="Corpo JSON com os dados para inserir. O schema depende da tabela."
    ),
    
    # 2. VALIDAÇÃO (CRÍTICA: Injeção de Dependência que valida e limpa os dados.)
    data_dict: Dict[str, Any] = Depends(validate_body) 
):
    """Insere um novo item em uma tabela autorizada com base em um modelo Pydantic."""
    
    # Construção Dinâmica da Query SQL (Usando apenas os dados validados de data_dict)
    columns = ", ".join(data_dict.keys()) # Ex: "rank_name"
    placeholders = ", ".join(["%s"] * len(data_dict)) # Ex: "%s"
    values = tuple(data_dict.values()) # Valores que serão passados de forma segura.

    try:
        # CORREÇÃO CRÍTICA: Adiciona aspas graves (`) ao redor do nome da tabela.
        sql = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"
        new_id = execute(sql=sql, params=values) # Envia para a camada DAO.
        
        if not new_id:
            raise HTTPException(status_code=500, detail="Não foi possível inserir os dados.")

        return {"message": f"Dados inseridos com sucesso na tabela '{table_name}'.", "new_id": new_id}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        # Este catch geralmente só será atingido se 'function_execute' falhar em lançar a HTTPException (ex: código antigo).
        logging.error(f"Erro inesperado na rota POST: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")