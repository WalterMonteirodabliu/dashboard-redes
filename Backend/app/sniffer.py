# ============================================================
# Sensores de Longo Alcance (Sniffer)
# ------------------------------------------------------------
# Função:
#  - Captura pacotes de rede em tempo real.
#  - Encaminha dados ao agregador de tráfego.
#  - Submete pacotes ao motor IPS para detecção de ameaças.
#  - Executa bloqueios imediatos em caso de detecção.
#
# Parte integrante do Projeto Apollo - Centro de Controle.
# ============================================================

import os
from scapy.all import sniff, IP
from .aggregator import add_packet_data
from .ips_engine import inspect_packet
from .response_actions import block_ip


# IP do servidor alvo (obtido do ambiente)
SERVER_IP = os.getenv("SERVER_IP")


def process_packet(packet):
    """
    Analisa cada pacote capturado:
      1. Envia ao motor IPS para verificação de ameaças.
      2. Se identificado comportamento malicioso → bloqueia o IP.
      3. Caso contrário → encaminha dados ao agregador de tráfego.
    """
    reason, malicious_ip, severity = inspect_packet(packet)

    if reason:
        # Ameaça detectada — aciona bloqueio automático
        block_ip(malicious_ip, reason, severity)
        return

    # Nenhuma ameaça → registra dados no agregador
    add_packet_data(packet, SERVER_IP)


def start_sniffing():
    """
    Ativa o modo de escuta dos sensores de rede.
    Captura todo o tráfego visível pela interface configurada.
    """
    print("[*] Sensores de longo alcance ativados. Escutando todo o tráfego de rede...")

    try:
        sniff(prn=process_packet, store=0, iface=None)
    except PermissionError:
        print("\n[ALERTA VERMELHO] Permissão negada. Execute como Administrador/sudo.")
        exit(1)
