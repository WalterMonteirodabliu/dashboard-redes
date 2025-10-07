# ============================================================
# Módulo: Processador de Telemetria de Voo (Aggregator)
# ------------------------------------------------------------
# Função:
#  - Acumula dados de pacotes capturados pelo sniffer.
#  - Calcula throughput (bytes e pacotes) por janelas de tempo.
#  - Limpa dados antigos para manter uso de memória controlado.
#
# Parte integrante do Projeto Apollo - Centro de Controle.
# ============================================================

import time
import threading
from collections import defaultdict
from scapy.all import IP


# Armazena dados de throughput por janela de tempo
throughput_data = defaultdict(lambda: {"bytes_total": 0, "packets": 0})
data_lock = threading.Lock()


def get_current_window(window_size=1):
    """
    Retorna o timestamp da janela atual (inteiro).
    window_size: tamanho da janela em segundos.
    """
    return int(time.time() // window_size * window_size)


def add_packet_data(packet, server_ip=None):
    """
    Adiciona um pacote à janela de tempo atual.
    Atualiza contagem de pacotes e bytes.
    """
    if not packet.haslayer(IP):
        return

    window = get_current_window()
    with data_lock:
        throughput_data[window]["packets"] += 1
        throughput_data[window]["bytes_total"] += len(packet)


def get_and_clear_old_data():
    """
    Retorna os dados da janela anterior e remove janelas antigas (>5 min).
    Evita crescimento infinito do dicionário.
    """
    current_window = get_current_window()
    previous_window = current_window - 1

    with data_lock:
        data_to_send = throughput_data.get(previous_window, {})

        # Remove dados muito antigos
        keys_to_delete = [k for k in throughput_data if k < current_window - 300]
        for key in keys_to_delete:
            del throughput_data[key]

        return {str(previous_window): data_to_send} if data_to_send else None
