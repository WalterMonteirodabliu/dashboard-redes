"""
Módulo principal do backend do IPS Dashboard.
Este servidor utiliza FastAPI e WebSockets para receber dados de tráfego,
gerados pelo sniffer, e transmitir informações em tempo real ao frontend.
"""

import asyncio
import threading
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .sniffer import start_sniffing
from .aggregator import get_and_clear_old_window_data
from .response_actions import get_new_alerts


# Instancia a aplicação FastAPI
app = FastAPI(title="Server Traffic IPS Dashboard")

# Configuração do CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """
    Gerencia as conexões WebSocket ativas.
    Permite conectar, desconectar e enviar mensagens em broadcast.
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Aceita e armazena nova conexão WebSocket."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove uma conexão WebSocket da lista ativa."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Envia uma mensagem para todos os clientes conectados."""
        for connection in self.active_connections:
            await connection.send_text(message)


# Instancia global do gerenciador de conexões
manager = ConnectionManager()


@app.on_event("startup")
def on_startup():
    """
    Evento disparado no início da aplicação.
    Inicia o sniffer em uma thread separada.
    """
    sniffer_thread = threading.Thread(target=start_sniffing, daemon=True)
    sniffer_thread.start()


@app.websocket("/ws/data")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket responsável por enviar:
    - Dados de tráfego (a cada 5 segundos).
    - Alertas de segurança detectados pelo motor IPS.
    """
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(5)

            # Envia dados de tráfego agregados
            traffic_data = get_and_clear_old_window_data()
            if traffic_data:
                await manager.broadcast(json.dumps({
                    "type": "traffic_data",
                    "payload": traffic_data
                }))

            # Envia novos alertas de segurança
            alerts = get_new_alerts()
            for alert in alerts:
                await manager.broadcast(json.dumps(alert))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Cliente WebSocket desconectado")

    except Exception as e:
        print(f"[WebSocket Error] {e}")
        manager.disconnect(websocket)
