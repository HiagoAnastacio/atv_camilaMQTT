# app/utils/dependencies.py

# FLUXO E A LÓGICA:
# 1. **`validate_data_core`** faz a validação Pydantic de dados brutos (chamada pelo MQTT).
# 2. **`validate_body`** é a dependência HTTP que usa `validate_data_core` e é injetada nas rotas POST/PUT.
# RAZÃO DE EXISTIR: Camada de Validação Centralizada e reutilizável.

from fastapi import HTTPException, Path, Body 
from pydantic import BaseModel, ValidationError, HttpUrl 
from typing import Dict, Any 
from model.model_resolver import get_model_for_table 
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- FUNÇÃO CORE DE VALIDAÇÃO (Reutilizável pelo MQTT) ---

def validate_data_core(table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Função de validação core que pode ser chamada diretamente por serviços NÃO-HTTP (como MQTT).
    Valida dados brutos usando o Schema Pydantic da tabela e retorna um dicionário seguro.
    """
    try:
        # 1. Resolução do Modelo
        model = get_model_for_table(table_name)
    except ValueError as e:
        raise ValueError(f"Tabela '{table_name}' não mapeada. Detalhe: {e}")

    # 2. Validação Pydantic
    try:
        validated_data = model.model_validate(data) 
        data_dict = validated_data.model_dump(exclude_none=True)
        
        # 3. Conversão de Tipos Complexos (HttpUrl para str)
        converted_data_dict = {}
        for key, value in data_dict.items():
            converted_data_dict[key] = str(value) if isinstance(value, HttpUrl) else value
            
        return converted_data_dict
            
    except ValidationError as e:
        # Lança o erro de validação (para ser capturado pelo chamador)
        raise ValidationError(f"Dados inválidos para a tabela {table_name}: {e.errors()}")


# --- FUNÇÃO DE DEPENDÊNCIA HTTP (Chamada pelo FastAPI) ---

async def validate_body( 
    request_body: Dict[str, Any] = Body(...),
    table_name: str = Path(..., description="Nome da tabela de destino.")
) -> Dict[str, Any]:
    """
    Dependência HTTP do FastAPI. Valida o corpo da requisição e retorna o dicionário limpo, 
    usando a lógica de validação core.
    """
    
    # 1. Validação do Nome da Tabela e Schema
    try:
        # Usa a função core de validação
        data_dict = validate_data_core(table_name, request_body)
        return data_dict 
        
    # 2. Tratamento de Erros
    except ValueError as e:
        # Erro 400 se o nome da tabela for inválido ou não mapeado
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        # Erro 422 se o corpo não estiver de acordo com o Schema Pydantic.
        error_detail = json.loads(e.json()) 
        raise HTTPException(status_code=422, detail=f"Erro de validação de dados: {error_detail}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno de validação: {e}")