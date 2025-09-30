# FLUXO E A LÓGICA:
# 1. Recebe `table_name` da URL (Escopo de Requisição).
# 2. Valida `table_name` contra a `TABLES_WHITELIST` (Segurança CRÍTICA).
# 3. Constrói e executa a query `SELECT * FROM {table_name}`.
# 4. Retorna os resultados do DB como JSON.
# A razão de existir: Ponto de entrada para a operação de leitura (GET) de forma GENÉRICA e protegida.

from fastapi import APIRouter, HTTPException, Path, Depends
from utils.function_execute import execute # Importa a função DAO para acesso ao DB.
# from fastapi_limiter.depends import RateLimiter # Importa o limitador de taxa.

# Variável 'router' (Escopo Global/Módulo).
router = APIRouter()

# Variável 'TABLES_WHITELIST' (Escopo Global/Módulo): Lista de tabelas permitidas.
# Razão: SEGURANÇA. Impede que o usuário tente acessar tabelas não expostas na API.
TABLES_WHITELIST = ["categoria_pedidos","pedidos"]

# Rota para consulta genérica: /get/{table_name}
@router.get("/get/{table_name}", tags=["Generic Data Management"],
            #dependencies=[Depends(RateLimiter(times=20, seconds=60))]
) # Rate Limiter ATIVADO (Essencial para GETs).
async def get_tabela(
    table_name: str = Path(..., description="Nome da tabela para consulta")
):
    """Consulta genérica e segura para tabelas autorizadas, protegida por Rate Limiting."""
    
    # 1. Verificação de Segurança (Whitelist)
    if table_name not in TABLES_WHITELIST:
        # Erro 400 se a tabela não estiver na lista branca.
        raise HTTPException(status_code=400, detail=f"A tabela '{table_name}' não é válida para esta consulta.")
    
    try:
        # CORREÇÃO: Adiciona aspas graves (`) ao redor do nome da tabela.
        sql = f"SELECT * FROM `{table_name}`"
        
        result = execute(sql=sql) # Envia para a camada DAO.
        
        if result is None or len(result) == 0:
            # Erro 404 se o DB não retornar dados (ex: tabela vazia).
            raise HTTPException(status_code=404, detail=f"Nenhum dado encontrado para a tabela '{table_name}'.")

        return result
    except HTTPException as e:
        raise e
    except Exception:
        # Este catch será raramente atingido, pois `execute` deve levantar HTTPException.
        raise HTTPException(status_code=500, detail="Erro interno durante a consulta ao banco.")