"""
Módulo principal do backend do Projeto Apollo - Centro de Controle.
Este servidor utiliza FastAPI e WebSockets para receber dados de tráfego,
gerados pelo sniffer, e transmitir informações em tempo real ao frontend.

Além disso, ele integra o motor de resposta (IPS Engine) e o módulo
de inteligência de ameaças, garantindo que as ações de defesa e os alertas
sejam processados de forma assíncrona e coordenada.
"""

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


# Instancia a aplicação FastAPI
app = FastAPI(title="Projeto Apollo - Centro de Controle")

# Configuração do CORS para permitir acesso de qualquer origem (ambiente de desenvolvimento)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        """Envia uma mensagem em broadcast para todos os clientes conectados."""
        for connection in self.active_connections:
            await connection.send_text(message)


# Instância global do gerenciador de conexões
manager = ConnectionManager()


@app.on_event("startup")
def on_startup():
    """
    Evento disparado no início da aplicação.
    Inicializa o sniffer, carrega a inteligência de ameaças e entrega
    o event loop principal ao módulo de resposta.
    """
    loop = asyncio.get_running_loop()
    response_actions.set_event_loop(loop)

    threading.Thread(target=load_threat_intelligence).start()
    threading.Thread(target=start_sniffing, daemon=True).start()


@app.websocket("/ws/data")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket responsável por enviar:
    - Dados de throughput (taxa de tráfego).
    - Alertas de segurança detectados pelo motor IPS.

    O envio ocorre de forma contínua e assíncrona,
    permitindo atualização em tempo real no frontend.
    """
    await manager.connect(websocket)

    try:
        while True:
            await asyncio.sleep(1)

            # Envia dados de throughput (janela de dados)
            throughput_data = get_and_clear_old_data()
            if throughput_data:
                await manager.broadcast(json.dumps({
                    "type": "throughput_data",
                    "payload": throughput_data
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
