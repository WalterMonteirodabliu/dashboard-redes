# =============================================
# Computador de Bordo - Carregador do Plano de Voo
# ---------------------------------------------
# Função: Carrega o arquivo config.yaml contendo
# parâmetros da missão do Sistema IDS/IPS.
#
# Em caso de falha: emite alerta vermelho e aborta.
# =============================================

import yaml, os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
config = {}

try:
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    print("[+] Plano de Voo (config.yaml) carregado.")
except Exception as e:
    print(f"[!] ALERTA VERMELHO: Falha ao carregar o Plano de Voo: {e}")
    exit(1)

def get_config():
    """Retorna o dicionário de configuração da missão (IDS/IPS)."""
    return config
