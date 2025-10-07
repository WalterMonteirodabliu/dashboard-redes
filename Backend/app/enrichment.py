# ============================================================
# Módulo: Inteligência de Alvo (Geo & Hostname Enrichment)
# ------------------------------------------------------------
# Função:
#  - Enriquecer informações de IPs com país e hostname.
#  - Integração com GeoLite2 para geolocalização.
#  - Cache interno para otimizar consultas repetidas.
#
# Parte integrante do Projeto Apollo - Centro de Controle.
# ============================================================

import geoip2.database
import socket
import asyncio
import os


# Cache de IPs já consultados
ip_cache = {}

# Caminho para o banco GeoLite2
GEO_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'GeoLite2-Country.mmdb')

try:
    geoip_reader = geoip2.database.Reader(GEO_DB_PATH)
except FileNotFoundError:
    print(f"[!] AVISO: Mapa estelar (GeoLite2) não encontrado. Geolocalização desativada.")
    geoip_reader = None


async def get_enriched_data(ip: str):
    """
    Retorna dados enriquecidos de um IP:
      - country_code: código do país
      - hostname: nome do host

    Verifica cache antes de consultar GeoLite2 ou DNS.
    """
    if ip in ip_cache:
        return ip_cache[ip]

    enriched_info = {"country_code": "N/A", "hostname": "N/A"}

    # Consulta geolocalização
    if geoip_reader:
        try:
            response = geoip_reader.country(ip)
            if response.country.iso_code:
                enriched_info["country_code"] = response.country.iso_code
        except geoip2.errors.AddressNotFoundError:
            pass

    # Consulta hostname de forma assíncrona
    try:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, socket.gethostbyaddr, ip)
        enriched_info["hostname"] = res[0]
    except (socket.herror, socket.gaierror):
        pass

    # Armazena no cache
    ip_cache[ip] = enriched_info
    return enriched_info
