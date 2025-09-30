# app/routes/extra/route_mqtt.py

# FLUXO E A LÓGICA:
# 1. Define as rotas HTTP para gerenciar o estado do cliente MQTT (ativar/desativar).
# 2. As rotas chamam as funções de controle do ciclo de vida que estão em get_data_camila.py.
# RAZÃO DE EXISTIR: Isolamento da lógica de controle (Routes) da lógica de negócios (models) e das rotas CRUD.

from fastapi import APIRouter, HTTPException
# Importa as funções de controle do ciclo de vida
from model.get_data_camila import start_mqtt_client, stop_mqtt_client, get_mqtt_status 

router = APIRouter()

# ----------------------------------------------------------------
# ROTAS DE CONTROLE MQTT
# ----------------------------------------------------------------

@router.post("/mqtt/start", tags=["MQTT Control"], summary="Ativa a Subscrição MQTT")
async def start_mqtt():
    """Ativa o cliente MQTT para começar a consumir e persistir dados da bancada."""
    if get_mqtt_status():
        return {"status": "running", "message": "Cliente MQTT já está ativo."}
        
    if start_mqtt_client():
        return {"status": "running", "message": "Cliente MQTT ativado com sucesso."}
    else:
        raise HTTPException(status_code=500, detail="Falha crítica ao iniciar o cliente MQTT. Verifique logs e credenciais.")

@router.post("/mqtt/stop", tags=["MQTT Control"], summary="Desativa a Subscrição MQTT")
async def stop_mqtt():
    """Desativa o cliente MQTT e encerra o loop de subscrição."""
    if not get_mqtt_status():
        return {"status": "stopped", "message": "Cliente MQTT já está inativo."}
        
    if stop_mqtt_client():
        return {"status": "stopped", "message": "Cliente MQTT desativado com sucesso."}
    else:
        raise HTTPException(status_code=500, detail="Falha ao encerrar o cliente MQTT.")

@router.get("/mqtt/status", tags=["MQTT Control"], summary="Verifica o Status do Cliente MQTT")
async def status_mqtt():
    """Verifica se o cliente MQTT está atualmente conectado e em execução."""
    status = "running" if get_mqtt_status() else "stopped"
    return {"status": status, "message": f"O Cliente MQTT está atualmente {status}."}