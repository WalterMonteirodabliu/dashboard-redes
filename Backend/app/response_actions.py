# backend/app/response_actions.py (VERSÃO CORRIGIDA PARA WINDOWS ASYNCIO)
import subprocess
import threading
import time
import asyncio
import platform
from .enrichment import get_enriched_data

# --- INÍCIO DA MUDANÇA ---
# Variável global para guardar uma referência ao "gerente" principal (event loop)
main_loop = None

def set_event_loop(loop):
    """
    Esta função é chamada pelo main.py no início para nos dar o "ramal" do gerente principal.
    """
    global main_loop
    main_loop = loop
# --- FIM DA MUDANÇA ---

new_alerts = []
alerts_lock = threading.Lock()
blocked_ips = {}

def block_ip(ip, reason, severity, duration=300):
    if ip in blocked_ips:
        return
    
    print(f"[{severity}] AMEAÇA: {reason}. Ativando escudos contra {ip} por {duration}s.")
    
    os_type = platform.system()
    success = False
    
    try:
        if os_type == "Linux":
            subprocess.run(['iptables', '-I', 'INPUT', '1', '-s', ip, '-j', 'DROP'], check=True, capture_output=True, text=True)
            success = True
        elif os_type == "Windows":
            rule_name = f"PROJECT-APOLLO-BLOCK-{ip}"
            command = f'New-NetFirewallRule -DisplayName "{rule_name}" -Direction Inbound -Action Block -RemoteAddress "{ip}"'
            subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-Command', command], check=True, capture_output=True, text=True)
            success = True

        if success:
            # --- INÍCIO DA MUDANÇA ---
            # Em vez de criar um novo gerente (asyncio.run), pedimos ao gerente principal para executar a tarefa.
            # `run_coroutine_threadsafe` é a forma correta de fazer isso a partir de outra thread.
            if main_loop:
                asyncio.run_coroutine_threadsafe(create_enriched_alert(ip, reason, severity, duration), main_loop)
            # --- FIM DA MUDANÇA ---

            timer = threading.Timer(duration, unblock_ip, args=[ip])
            timer.start()
            blocked_ips[ip] = timer
    except Exception as e:
        print(f"[ERRO DE SISTEMA DE DEFESA] Falha ao ativar escudos: {e}")

async def create_enriched_alert(ip, reason, severity, duration):
    geo_data = await get_enriched_data(ip)
    with alerts_lock:
        new_alerts.append({
            "type": "security_alert",
            "payload": {
                "timestamp": time.time(), "ip": ip, "reason": reason, "action": "BLOQUEADO",
                "severity": severity, "geo": geo_data
            }
        })

def unblock_ip(ip):
    # (Esta função permanece a mesma)
    print(f"[*] Desativando escudos para {ip}.")
    os_type = platform.system()
    try:
        if os_type == "Linux":
            subprocess.run(['iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP'], check=True, capture_output=True, text=True)
        elif os_type == "Windows":
            rule_name = f"PROJECT-APOLLO-BLOCK-{ip}"
            command = f'Remove-NetFirewallRule -DisplayName "{rule_name}"'
            subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-Command', command], check=True, capture_output=True, text=True)
        if ip in blocked_ips:
            del blocked_ips[ip]
    except Exception:
        pass

def get_new_alerts():
    with alerts_lock:
        alerts_to_send = list(new_alerts)
        new_alerts.clear()
        return alerts_to_send