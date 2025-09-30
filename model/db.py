# FLUXO E A LÓGICA:
# 1. O construtor `__init__` lê as variáveis de ambiente (Escopo Global/Módulo).
# 2. `connect()` abre a conexão com o DB (Escopo de Requisição).
# 3. `execute_comand()` executa o SQL, faz `COMMIT` ou retorna dados (Escopo de Requisição).
# 4. `disconnect()` fecha a conexão (Escopo de Requisição).
# A razão de existir: Encapsular o acesso ao driver MySQL. É a interface de baixo nível entre a aplicação Python e o banco de dados.

from typing import Any, Optional, Tuple, Union, List # Tipagem: Define tipos complexos.
import mysql.connector as mc # Biblioteca do conector do MySQL.
from mysql.connector import Error, MySQLConnection # Classes específicas de erro e conexão.
from dotenv import load_dotenv # Função para carregar variáveis de ambiente.
from os import getenv # Função para ler variáveis de ambiente.

class Database: # Classe que gerencia a conexão com o banco
    def __init__(self) -> None:
        load_dotenv() # Carrega as variáveis do arquivo .env.
        # Inicializa atributos com as credenciais do DB (getenv).
        self.host: str = getenv('DB_HOST')
        self.username: str = getenv('DB_USER')
        self.password: str = getenv('DB_PSWD')
        self.database: str = getenv('DB_NAME') # O nome do DB é 'projeto_ads2'.
        self.connection: Optional[MySQLConnection] = None # Objeto de conexão real. Inicia como None.
        self.cursor: Union[List[dict], None] = None # Cursor principal. Inicia como None.
 
# ===============================================================================================================
# Métodos de conexão, desconexão e execução de comandos no banco de dados.
# ===============================================================================================================
    # Conectar ao banco de dados
    def connect(self) -> None:
        """
        Estabelece uma conexão com o banco de dados.
        CRÍTICO: Deve levantar a exceção (raise) em caso de falha de conexão.
        """
        try:
            # Tenta estabelecer a conexão usando as credenciais
            self.connection = mc.connect(
                host = self.host,
                database = self.database,
                user = self.username,
                password = self.password
            )
            if self.connection.is_connected():
                # Cria um cursor que retorna resultados como dicionários (dictionary=True)
                self.cursor = self.connection.cursor(dictionary=True)
                print("Conexão ao banco de dados realizada com sucesso,")
        except Error as e:
            # Em caso de falha de conexão, reseta a conexão para None (limpeza)
            print(f"Erro de conexão do DB: {e}")
            self.connection = None
            self.cursor = None
            # IMPORTANTE: Re-levanta o erro para que function_execute.py o capture e o exponha.
            raise e
 
    # Desconectar do banco de dados
    def disconnect(self) -> None:
        """Encerra a conexão com o banco de dados e o cursor, se eles existirem."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("Conexão com o banco de dados encerrada com sucesso;")
    
    # Executar comando no banco de dados
    def execute_comand(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Union[List[dict], Any]]:
        """Executa um comando SQL de forma segura, gerencia o cursor e o COMMIT."""
        # Se o connect() falhar e levantar exceção (como corrigido acima), esta parte não é atingida.
        if self.connection is None:
            print('ERRO: Conexão ao banco de dados não estabelecida.')
            return None

        # Cria um novo cursor (o objeto de execução)
        cursor = self.connection.cursor(dictionary=True) 
        try:
            # Executa o comando SQL com os parâmetros (prevenindo SQL Injection)
            cursor.execute(sql, params)
            
            # Se for um SELECT, busca todos os resultados
            if sql.strip().lower().startswith("select"):
                result = cursor.fetchall()
                return result
            else:
                # Se for INSERT/UPDATE/DELETE, confirma a alteração
                self.connection.commit()
                # Retorna o ID do último registro inserido ou o número de linhas afetadas
                return cursor.lastrowid if sql.strip().lower().startswith("insert") else cursor.rowcount
        except Error as e:
            # Levanta o erro para ser capturado por function_execute.py
            raise e