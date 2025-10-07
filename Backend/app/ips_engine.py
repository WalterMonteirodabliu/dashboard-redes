# Sistema de Análise de Ameaças (IPS)
import re, time, requests
from collections import defaultdict, deque
from scapy.all import TCP, IP
from .config import get_config
CONFIG = get_config()
SIGNATURE_RULES = [(re.compile(r['pattern'], re.IGNORECASE), r['name'], r['severity']) for r in CONFIG.get('signature_rules', [])]
THREAT_IPS = set()
def load_threat_intelligence():
    url = CONFIG.get('threat_intelligence_url');
    if not url: return
    try:
        print("[+] Baixando atualizações para o Catálogo de Hostis...")
        r = requests.get(url, timeout=10); r.raise_for_status()
        ips = r.text.splitlines()
        THREAT_IPS.update(ip for ip in ips if not ip.startswith('#') and ip.strip())
        print(f"[+] {len(THREAT_IPS)} hostis conhecidos carregados.")
    except Exception as e: print(f"[!] AVISO: Falha na comunicação com a Central de Inteligência: {e}")
ip_history = defaultdict(lambda: deque(maxlen=CONFIG.get('port_scan_threshold', 50)))
def inspect_packet(packet):
    if not packet.haslayer(IP): return None, None, None
    src_ip = packet.getlayer(IP).src
    if src_ip in THREAT_IPS: return "IP em Blocklist de Ameaças", src_ip, "HIGH"
    if packet.haslayer(TCP):
        history = ip_history[src_ip]
        history.append((time.time(), packet[TCP].dport))
        if len(history) >= CONFIG.get('port_scan_threshold', 20):
            if history[-1][0] - history[0][0] < CONFIG.get('scan_time_window', 10):
                return "Port Scan Detectado", src_ip, "MEDIUM"
    if packet.haslayer('Raw'):
        try:
            payload = packet.getlayer('Raw').load.decode('utf-8', errors='ignore')
            for regex, name, severity in SIGNATURE_RULES:
                if regex.search(payload): return name, src_ip, severity
        except Exception: pass
    return None, None, None
