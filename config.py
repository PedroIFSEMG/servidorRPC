"""
Arquivo de configuração global do sistema RPC.
Contém parâmetros usados pelo servidor e pelo cliente.
Inclui validações básicas para evitar que valores inválidos quebrem o sistema.
"""

from pathlib import Path
import os

_DEFAULTS = {
    'SERVIDOR_IP': '127.0.0.1',
    'SERVIDOR_PORTA': 5000,
    'ARQUIVO_CACHE': 'cache_servidor.json',
    'LIMITE_CACHE_BYTES': 30720,  # 30 KB
    'TIMEOUT_CONEXAO': 10,

    'EXPIRACAO_MINUTOS': 2,
    'CACHE_CLIENTE_ARQUIVO': 'cache_cliente.json',

    'QTD_PADRAO_NOTICIAS': 10,
    'URL_UOL': 'https://www.uol.com.br/',
    'HEADERS_PADRAO': {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/132.0.0.0 Safari/537.36'
    },
    'DEBUG': True,
    'GEMINI_API_KEY': 'AIzaSyBzAkO877SMimzHJxzjBEVCR7S2du8FeBg',
    'GEMINI_MODEL': 'gemini-3-flash-preview',  # Modelo mais recente
    'GEMINI_MODEL_BACKUP': 'gemini-pro',  # Modelo alternativo
}


SERVIDOR_IP = _DEFAULTS['SERVIDOR_IP']
SERVIDOR_PORTA = _DEFAULTS['SERVIDOR_PORTA']
ARQUIVO_CACHE = _DEFAULTS['ARQUIVO_CACHE']
LIMITE_CACHE_BYTES = _DEFAULTS['LIMITE_CACHE_BYTES']
TIMEOUT_CONEXAO = _DEFAULTS['TIMEOUT_CONEXAO']

EXPIRACAO_MINUTOS = _DEFAULTS['EXPIRACAO_MINUTOS']
CACHE_CLIENTE_ARQUIVO = _DEFAULTS['CACHE_CLIENTE_ARQUIVO']

QTD_PADRAO_NOTICIAS = _DEFAULTS['QTD_PADRAO_NOTICIAS']
URL_UOL = _DEFAULTS['URL_UOL']
HEADERS_PADRAO = _DEFAULTS['HEADERS_PADRAO']
DEBUG = _DEFAULTS['DEBUG']
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', _DEFAULTS['GEMINI_API_KEY'])
GEMINI_MODEL = _DEFAULTS['GEMINI_MODEL']
GEMINI_MODEL_BACKUP = _DEFAULTS['GEMINI_MODEL_BACKUP']

# Tentar usar a chave da variável de ambiente se não estiver configurada
if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.environ.get('GOOGLE_API_KEY', '')

try:
    LIMITE_CACHE_BYTES = int(LIMITE_CACHE_BYTES)
    if LIMITE_CACHE_BYTES <= 0:
        LIMITE_CACHE_BYTES = _DEFAULTS['LIMITE_CACHE_BYTES']
except Exception:
    LIMITE_CACHE_BYTES = _DEFAULTS['LIMITE_CACHE_BYTES']

try:
    EXPIRACAO_MINUTOS = float(EXPIRACAO_MINUTOS)
    if EXPIRACAO_MINUTOS < 0:
        EXPIRACAO_MINUTOS = _DEFAULTS['EXPIRACAO_MINUTOS']
except Exception:
    EXPIRACAO_MINUTOS = _DEFAULTS['EXPIRACAO_MINUTOS']

ARQUIVO_CACHE = str(Path(ARQUIVO_CACHE))
CACHE_CLIENTE_ARQUIVO = str(Path(CACHE_CLIENTE_ARQUIVO))

_MAX_RECOMMENDED = 50_000_000
if LIMITE_CACHE_BYTES > _MAX_RECOMMENDED:
    print(f"[AVISO] LIMITE_CACHE_BYTES muito grande ({LIMITE_CACHE_BYTES} bytes). Isso pode afetar desempenho.")

# Validação da chave Gemini
if GEMINI_API_KEY and len(GEMINI_API_KEY) < 20:
    print("[AVISO] Chave da API Gemini parece muito curta. Verifique se está correta.")