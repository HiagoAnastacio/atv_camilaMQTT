# FLUXO E A LÓGICA:
# 1. O arquivo principal inicializa o FastAPI.
# 2. As configurações de segurança (Lifespan para Redis/Rate Limit e CORS) foram importadas, mas estão DESATIVADAS no main.py.
# 3. Ele atua como um 'coletor' de rotas, incluindo todos os módulos CRUD (`route_*.py`) sob o prefixo `/api`, 
#    direcionando o tráfego e garantindo a modularidade da aplicação.

from fastapi import FastAPI # Importa o framework principal. Razão: Base da API.
from routes import route_get, route_post, route_update, route_delete # Importa as rotas CRUD. Razão: Modularidade do código.

# 1. Inicialização do FastAPI:
app = FastAPI()                               

# 2. Inclusão de Rotas Modulares
# As rotas são incluídas aqui. O tráfego para `/api/*` será direcionado aos módulos importados.
app.include_router(route_get.router, prefix="/api")            
app.include_router(route_post.router, prefix="/api")           
app.include_router(route_update.router, prefix="/api")         
app.include_router(route_delete.router, prefix="/api")  
       
