# ============================================================
# Módulo: Servidor Central (Backend Principal)
# ------------------------------------------------------------
# Função:
#  - Gerencia o fluxo de dados entre o sniffer e o frontend.
#  - Utiliza FastAPI + WebSocket para envio em tempo real.
#  - Integra o IPS Engine e o sistema de resposta automática.
#
# Parte integrante do Projeto Apollo - Centro de Controle.
# ============================================================

from dotenv import load_dotenv
load_dotenv()

import asyncio
import threading
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .sniffer import start_sniffing
from .aggregator import get_and_clear_old_data
from .response_actions import get_new_alerts
from .ips_engine import load_threat_intelligence
from . import response_actions


# --- Inicialização da aplicação FastAPI ---
app = FastAPI(title="Projeto Apollo - Centro de Controle")

# Libera acesso CORS (modo desenvolvimento)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Gerenciador de conexões WebSocket ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


# --- Rotinas de inicialização ---
@app.on_event("startup")
def on_startup():
    loop = asyncio.get_running_loop()
    response_actions.set_event_loop(loop)

    # Carrega inteligência de ameaças e inicia o sniffer
    threading.Thread(target=load_threat_intelligence).start()
    threading.Thread(target=start_sniffing, daemon=True).start()


# --- Endpoint WebSocket ---
@app.websocket("/ws/data")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await asyncio.sleep(1)

            # Envia dados de throughput
            throughput_data = get_and_clear_old_data()
            if throughput_data:
                await manager.broadcast(json.dumps({
                    "type": "throughput_data",
                    "payload": throughput_data
                }))

            # Envia alertas de segurança
            alerts = get_new_alerts()
            for alert in alerts:
                await manager.broadcast(json.dumps(alert))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Cliente WebSocket desconectado")

    except Exception as e:
        print(f"[WebSocket Error] {e}")
        manager.disconnect(websocket)
