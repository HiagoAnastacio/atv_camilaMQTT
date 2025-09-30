# app/model/model_resolver.py

from fastapi import HTTPException
from typing import Type
from pydantic import BaseModel
from model.models import (
    PedidosBase,
    CamilaDataBase, # NOVO IMPORT
)

# Mapeamento Estático: Mapeia a URL/tabela com o Schema Pydantic
TABLE_MODEL_MAPPING: dict[str, Type[BaseModel]] = {
    # Mapeamentos Existentes:
    # "categoria_pedidos": CategoriaPedidoBase, <--- LINHA REMOVIDA
    "pedidos": PedidosBase,
    
    # MAPEAMENTO PARA MQTT:
    "camila_data": CamilaDataBase, 
}

def get_model_for_table(table_name: str) -> Type[BaseModel]:
    """Retorna a classe do modelo Pydantic correspondente a uma tabela."""
    model = TABLE_MODEL_MAPPING.get(table_name.lower())
    
    if not model:
        raise ValueError(f"Tabela '{table_name}' não mapeada. Verifique 'model_resolver.py' ou o nome da tabela.")
    
    return model