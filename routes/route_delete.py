# FLUXO E A LÓGICA:
# 1. Recebe 'table_name' e 'item_id' da URL (Escopo de Requisição).
# 2. Executa a dependência de Rate Limiting (Segurança).
# 3. Valida se 'table_name' está na Whitelist (Segurança Crítica).
# 4. Constrói a Query SQL DELETE dinâmica.
# 5. Chama `execute` (DAO).

from fastapi import APIRouter, HTTPException, Path, Depends
from utils.function_execute import execute
# from fastapi_limiter.depends import RateLimiter

router = APIRouter()

# Lista de tabelas permitidas para exclusão.
TABLES_WHITELIST = ["categoria_pedidos","pedidos"]

@router.delete("/delete/{table_name}/{item_id}", tags=["Generic Data Management"],
            #dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def delete_data(
    table_name: str = Path(..., description="Nome da tabela para exclusão"),
    item_id: int = Path(..., description="ID do item a ser excluído")
):
    """Exclui um item de uma tabela autorizada com base no ID."""

    # 1. Verificação de Segurança (Whitelist)
    if table_name not in TABLES_WHITELIST:
        raise HTTPException(status_code=400, detail=f"A tabela '{table_name}' não é válida para esta operação.")

    try:
        # CORREÇÃO CRÍTICA: Adiciona aspas graves (`) ao redor do nome da tabela e da coluna de ID.
        # Isso resolve o erro de palavra reservada (ex: 'rank').
        sql = f"DELETE FROM `{table_name}` WHERE `{table_name}_id` = %s"

        rows_affected = execute(sql=sql, params=(item_id,))

        # 2. Verificação de Resultado
        if not rows_affected:
            # Retorna 404 se o DB não excluiu nada (ID não existe).
            raise HTTPException(status_code=404, detail=f"Item com ID {item_id} não encontrado ou não houve exclusão.")

        return {"message": f"Item com ID {item_id} excluído com sucesso da tabela '{table_name}'.",
                "rows_affected": rows_affected}

    except HTTPException as e:
        raise e
    except Exception:
        # Erro genérico (500) para falhas não esperadas.
        raise HTTPException(status_code=500, detail="Erro interno do servidor durante a exclusão.")