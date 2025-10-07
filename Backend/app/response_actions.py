# ============================================================
# Sistema de Ações de Resposta (Defense Control)
# ------------------------------------------------------------
# Função:
#  - Executa bloqueios automáticos de IPs hostis.
#  - Cria e envia alertas enriquecidos ao Centro de Controle.
#  - Gerencia timers de desbloqueio e comunicação assíncrona.
#
# Compatível com Linux (iptables) e Windows (Firewall).
# ============================================================

import subprocess
import threading
import time
import asyncio
import platform
from .enrichment import get_enriched_data

# Referência global ao event loop principal (setada em main.py)
main_loop = None


def set_event_loop(loop):
    """
    Recebe o event loop principal do backend.
    Permite agendar tarefas assíncronas a partir de outras threads.
    """
    global main_loop
    main_loop = loop


# Estruturas de controle do sistema de defesa
new_alerts = []                      # Lista de novos alertas a serem enviados
alerts_lock = threading.Lock()       # Garante acesso seguro à lista de alertas
blocked_ips = {}                     # IPs atualmente bloqueados (ip → Timer ativo)


def block_ip(ip, reason, severity, duration=300):
    """
    Ativa bloqueio temporário de um IP hostil.
    Aplica regra no firewall (iptables ou Windows Firewall) e gera alerta.
    """
    if ip in blocked_ips:
        return

    print(f"[{severity}] AMEAÇA: {reason}. Ativando escudos contra {ip} por {duration}s.")
    os_type = platform.system()
    success = False

    try:
        if os_type == "Linux":
            subprocess.run(
                ['iptables', '-I', 'INPUT', '1', '-s', ip, '-j', 'DROP'],
                check=True, capture_output=True, text=True
            )
            success = True

        elif os_type == "Windows":
            rule_name = f"PROJECT-APOLLO-BLOCK-{ip}"
            command = (
                f'New-NetFirewallRule -DisplayName "{rule_name}" '
                f'-Direction Inbound -Action Block -RemoteAddress "{ip}"'
            )
            subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', command],
                check=True, capture_output=True, text=True
            )
            success = True

        if success:
            # Agenda criação do alerta enriquecido no loop principal
            if main_loop:
                asyncio.run_coroutine_threadsafe(
                    create_enriched_alert(ip, reason, severity, duration),
                    main_loop
                )

            # Inicia timer para desbloquear o IP após o tempo definido
            timer = threading.Timer(duration, unblock_ip, args=[ip])
            timer.start()
            blocked_ips[ip] = timer

    except Exception as e:
        print(f"[ERRO DE DEFESA] Falha ao ativar escudos: {e}")


async def create_enriched_alert(ip, reason, severity, duration):
    """
    Gera alerta detalhado com informações geográficas e de rede.
    Executado de forma assíncrona para não bloquear o loop principal.
    """
    geo_data = await get_enriched_data(ip)
    with alerts_lock:
        new_alerts.append({
            "type": "security_alert",
            "payload": {
                "timestamp": time.time(),
                "ip": ip,
                "reason": reason,
                "action": "BLOQUEADO",
                "severity": severity,
                "geo": geo_data
            }
        })


def unblock_ip(ip):
    """
    Remove regras de bloqueio após o tempo limite.
    Restaura o tráfego normal para o IP.
    """
    print(f"[*] Desativando escudos para {ip}.")
    os_type = platform.system()

    try:
        if os_type == "Linux":
            subprocess.run(
                ['iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP'],
                check=True, capture_output=True, text=True
            )
        elif os_type == "Windows":
            rule_name = f"PROJECT-APOLLO-BLOCK-{ip}"
            command = f'Remove-NetFirewallRule -DisplayName "{rule_name}"'
            subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', command],
                check=True, capture_output=True, text=True
            )

        if ip in blocked_ips:
            del blocked_ips[ip]

    except Exception:
        pass


def get_new_alerts():
    """
    Retorna todos os alertas pendentes e limpa a fila.
    Chamado periodicamente pelo módulo principal (main.py).
    """
    with alerts_lock:
        alerts_to_send = list(new_alerts)
        new_alerts.clear()
        return alerts_to_send
