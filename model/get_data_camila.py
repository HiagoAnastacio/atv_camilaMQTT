import os
import uuid
import json
import logging
from typing import Optional, Dict, Any, Tuple

# Bibliotecas MQTT
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Importa a função DAO para acesso ao DB
from utils.function_execute import execute 
# Importa o modelo Pydantic unificado
from model.models import PedidosBase 

# Carrega as variáveis de ambiente
load_dotenv()

# Configuração de Log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurações do Broker MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "bancada/camila/#") 
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PSWD = os.getenv("MQTT_PSWD")

# Variável global para armazenar a instância do cliente MQTT
mqtt_client: Optional[mqtt.Client] = None

# --- FUNÇÕES DE CALLBACKS DO PAHO-MQTT ---

def on_connect(client, userdata, flags, rc):
    """Chamado quando o cliente recebe uma resposta CONNACK do broker."""
    if rc == 0:
        logging.info("--- CONEXÃO MQTT SUCESSO ---: Conectado ao Broker.")
        result, mid = client.subscribe(MQTT_TOPIC, qos=0) 
        if result == mqtt.MQTT_ERR_SUCCESS:
            logging.info(f"--- SUBSTRIÇÃO SUCESSO ---: Subscrição em '{MQTT_TOPIC}' enviada.")
        else:
            logging.error(f"--- ERRO SUBSTRIÇÃO ---: Falha ao enviar comando de subscrição. Código: {result}")
    else:
        logging.error(f"--- ERRO CONEXÃO MQTT ---: Falha na conexão, código de retorno: {rc}.")

def on_message(client, userdata, msg):
    """Chamado quando uma mensagem é recebida do broker."""
    logging.info("--- ESTÁGIO 1: INFO CHEGOU ---") 

    try:
        payload_str = msg.payload.decode('utf-8')
        data = json.loads(payload_str)
        logging.info(f"Tópico: {msg.topic}, Payload Bruto: {payload_str}")

        # CHAMA A FUNÇÃO DE PERSISTÊNCIA CORRIGIDA
        save_data_to_db(msg.topic, data)
        
    except json.JSONDecodeError:
        logging.error(f"ERRO DE PARSE: Mensagem não é um JSON válido. Payload: {payload_str}")
    except Exception as e:
        logging.error(f"ERRO INESPERADO no on_message: {e}")

# --- FUNÇÕES DE CONTROLE DO CLIENTE ---

def start_mqtt_client(client_id: str = "FastAPICamilaCollector") -> Optional[mqtt.Client]:
    """Inicializa e conecta o cliente MQTT com um ID único."""
    global mqtt_client
    # CORREÇÃO CRÍTICA: Gera um ID ÚNICO.
    unique_id = f"{client_id}-{uuid.uuid4().hex[:8]}" 
    logging.info(f"Iniciando Cliente MQTT com ID ÚNICO: {unique_id}")

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=unique_id)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PSWD)

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start() 
        logging.info("Loop MQTT iniciado em thread separada.")
        return mqtt_client
    
    except Exception as e:
        logging.error(f"Falha ao conectar ao Broker MQTT em {MQTT_BROKER}:{MQTT_PORT}. Erro: {e}")
        return None

def stop_mqtt_client():
    """Para o cliente MQTT e a thread de loop."""
    global mqtt_client
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logging.info("Cliente MQTT desconectado e loop parado.")


# --- LÓGICA DE PERSISTÊNCIA NA TABELA 'pedidos' ---

def save_data_to_db(topic: str, data: Dict[str, Any]):
    """
    Mapeia os dados MQTT para as colunas tipo_do_pedido e valor_do_pedido
    da tabela 'pedidos' e persiste usando o DAO.
    """
    table_name = "pedidos" 
    
    # --- 1. Mapeamento e Validação para a Tabela 'pedidos' ---
    data_to_map = {
        # O tópico é a categoria do dado (ex: bancada/camila/sensor/temperatura)
        "tipo_do_pedido": topic, 
        # O payload JSON completo é salvo como string na coluna de valor.
        "valor_do_pedido": json.dumps(data) 
    }
    
    try:
        # Validação: Usa PedidosBase para garantir que os dois campos requeridos estão presentes.
        validated_data = PedidosBase.model_validate(data_to_map)
        data_to_insert = validated_data.model_dump(exclude_none=True) 
        
    except Exception as e:
        logging.error(f"ERRO DE VALIDAÇÃO PYDANTIC para MQTT -> PedidosBase: {e}")
        return

    # --- 2. Construção e Execução da Query na tabela 'pedidos' ---
    columns = ", ".join(data_to_insert.keys())
    placeholders = ", ".join(["%s"] * len(data_to_insert))
    values = tuple(data_to_insert.values())
    
    try:
        # Insere na tabela 'pedidos'
        sql = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"
        new_id = execute(sql=sql, params=values)
        logging.info(f"--- ESTÁGIO 3: DB PERSISTIDO ---. Tabela: '{table_name}'. ID: {new_id}")
        
    except Exception as e:
        logging.error(f"Falha CRÍTICA ao inserir dados MQTT no DB (Tabela: '{table_name}'): {e}")