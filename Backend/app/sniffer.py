# Sensores de Longo Alcance
import os
from scapy.all import sniff, IP
from .aggregator import add_packet_data
from .ips_engine import inspect_packet
from .response_actions import block_ip
SERVER_IP = os.getenv("SERVER_IP")
def process_packet(packet):
    reason, malicious_ip, severity = inspect_packet(packet)
    if reason: block_ip(malicious_ip, reason, severity); return
    add_packet_data(packet, SERVER_IP)
def start_sniffing():
    print("[*] Sensores de longo alcance ativados. Escutando todo o tráfego de rede...")
    try:
        sniff(prn=process_packet, store=0, iface=None)
    except PermissionError: print("\n[ALERTA VERMELHO] Permissão negada. Execute como Administrador/sudo."); exit(1)
