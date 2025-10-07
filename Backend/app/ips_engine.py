# ============================================================
# Sistema de Análise de Ameaças (IPS Engine)
# ------------------------------------------------------------
# Função:
#  - Analisa pacotes capturados pelo sniffer.
#  - Detecta assinaturas conhecidas e comportamentos suspeitos.
#  - Atualiza IPs hostis via Central de Inteligência.
# ============================================================

import re
import time
import requests
from collections import defaultdict, deque
from scapy.all import TCP, IP
from .config import get_config

# Carrega parâmetros de configuração do sistema
CONFIG = get_config()

# Compila as regras de detecção baseadas em assinaturas (regex)
SIGNATURE_RULES = [
    (re.compile(r['pattern'], re.IGNORECASE), r['name'], r['severity'])
    for r in CONFIG.get('signature_rules', [])
]

# Conjunto de IPs identificados como hostis (Threat Intelligence)
THREAT_IPS = set()


def load_threat_intelligence():
    """
    Baixa e carrega a lista de IPs maliciosos (Threat Intelligence Feed).
    Essa lista é usada para bloquear hosts conhecidos por atividades suspeitas.
    """
    url = CONFIG.get('threat_intelligence_url')
    if not url:
        return

    try:
        print("[+] Atualizando catálogo de IPs hostis...")
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        ips = r.text.splitlines()
        THREAT_IPS.update(ip for ip in ips if not ip.startswith('#') and ip.strip())

        print(f"[+] {len(THREAT_IPS)} IPs carregados.")
    except Exception as e:
        print(f"[!] Falha ao acessar a Central de Inteligência: {e}")


# Histórico de portas acessadas por IP (para detectar port scan)
ip_history = defaultdict(lambda: deque(maxlen=CONFIG.get('port_scan_threshold', 50)))


def inspect_packet(packet):
    """
    Analisa um pacote de rede e retorna:
      - Descrição do alerta
      - IP de origem
      - Severidade
    Caso nada suspeito seja detectado, retorna (None, None, None).
    """
    if not packet.haslayer(IP):
        return None, None, None

    src_ip = packet.getlayer(IP).src

    # Verifica se o IP está na blocklist
    if src_ip in THREAT_IPS:
        return "IP em Blocklist de Ameaças", src_ip, "HIGH"

    # Detecta varredura de portas (port scan)
    if packet.haslayer(TCP):
        history = ip_history[src_ip]
        history.append((time.time(), packet[TCP].dport))

        if len(history) >= CONFIG.get('port_scan_threshold', 20):
            tempo_total = history[-1][0] - history[0][0]
            if tempo_total < CONFIG.get('scan_time_window', 10):
                return "Port Scan Detectado", src_ip, "MEDIUM"

    # Verifica assinaturas conhecidas em payloads textuais
    if packet.haslayer('Raw'):
        try:
            payload = packet.getlayer('Raw').load.decode('utf-8', errors='ignore')
            for regex, name, severity in SIGNATURE_RULES:
                if regex.search(payload):
                    return name, src_ip, severity
        except Exception:
            pass

    return None, None, None
