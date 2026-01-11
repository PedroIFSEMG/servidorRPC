import socket
import json
import math
import os
from google import genai
from collections import OrderedDict
import requests
from bs4 import BeautifulSoup
import re
from config import (
    ARQUIVO_CACHE, LIMITE_CACHE_BYTES, SERVIDOR_IP, SERVIDOR_PORTA,
    TIMEOUT_CONEXAO, QTD_PADRAO_NOTICIAS, URL_UOL, HEADERS_PADRAO, DEBUG,
    GEMINI_API_KEY, GEMINI_MODEL
)

def carregar_cache():
    if os.path.exists(ARQUIVO_CACHE):
        try:
            with open(ARQUIVO_CACHE, 'r', encoding='utf-8') as f:
                return OrderedDict(json.load(f))
        except Exception:
            return OrderedDict()
    return OrderedDict()

def salvar_cache(cache):
    tmp = ARQUIVO_CACHE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)
    os.replace(tmp, ARQUIVO_CACHE)
    while os.path.getsize(ARQUIVO_CACHE) > LIMITE_CACHE_BYTES and len(cache) > 0:
        cache.popitem(last=False)
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False)
        os.replace(tmp, ARQUIVO_CACHE)

def obter_noticias_uol(qtd=QTD_PADRAO_NOTICIAS):
    try:
        resp = requests.get(URL_UOL, headers=HEADERS_PADRAO, timeout=TIMEOUT_CONEXAO)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        noticias = []
        for h3 in soup.find_all('h3', class_='title__element headlineSub__content__title'):
            titulo = h3.get_text(strip=True)
            link = None
            a_tag = h3.find('a') or h3.find_parent('a')
            if a_tag and a_tag.get('href'):
                link = a_tag['href']
                if link.startswith('/'):
                    link = URL_UOL.rstrip('/') + link
            if titulo:
                noticias.append({'titulo': titulo, 'link': link or 'Sem link'})
            if len(noticias) >= qtd:
                break

        return noticias or ['Nenhuma notícia encontrada.']
    except Exception as e:
        return [f'Erro ao obter notícias: {e}']

def resolver_com_gemini(problema):
    """Resolve problemas usando Gemini API (google-genai)"""
    
    if not GEMINI_API_KEY or len(GEMINI_API_KEY) < 20:
        print("[Gemini] Chave não configurada")
        return None
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        try:
            print(f"[Gemini] Tentando modelo: {GEMINI_MODEL}")
            prompt = f"""
            Você é um assistente matemático.
            Resolva o problema internamente passo a passo,
            mas forneça APENAS o resultado numérico final.

            Problema: {problema}

            Formato da resposta:
            [resultado]

            Exemplo:
            Entrada: 2+2
            Saída: [4]
            """

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )

            resultado = response.text.strip()
            print(f"[Gemini] Resposta bruta: {resultado}")

            # Extrair número
            match = re.search(r'\[?\s*(-?\d+(?:\.\d+)?)\s*\]?', resultado)
            if match:
                return f"(Gemini) {match.group(1)}"

            return f"(Gemini) {resultado[:50]}..."

        except Exception as e_modelo:
            print(f"[Gemini] Erro no modelo {GEMINI_MODEL}: {e_modelo}")
        return None
    except Exception as e:
        print(f"[Gemini] Erro geral: {e}")
        return None

def resolver_problema_local(problema):
    """Tenta resolver localmente - FALLBACK"""
    problema_lower = problema.lower().strip()
    
    # Dicionário de problemas conhecidos
    problemas_conhecidos = {
        "calcule a raiz quadrada de 27": "5.196152",
        "raiz quadrada de 27": "5.196152",
        "square root of 27": "5.196152",
        "calcule a raiz quadrada de 25": "5",
        "raiz quadrada de 25": "5",
        "square root of 25": "5",
        "quanto é 2 + 2": "4",
        "2 + 2": "4",
        "what is 2 + 2": "4",
        "2+2": "4",
        "quanto é 10 * 5": "50",
        "10 * 5": "50",
        "10*5": "50",
        "calcule o fatorial de 5": "120",
        "fatorial de 5": "120",
        "factorial of 5": "120",
        "5!": "120",
        "quanto é 15 / 3": "5",
        "15 / 3": "5",
        "15/3": "5",
        "qual é a potência de 2 elevado a 3": "8",
        "2 elevado a 3": "8",
        "2^3": "8",
        "2**3": "8",
        "2 to the power of 3": "8",
    }
    
    # Verificar problemas conhecidos primeiro
    for chave, resposta in problemas_conhecidos.items():
        if chave in problema_lower:
            print(f"[Local] Resolvido conhecido: {chave} → {resposta}")
            return f"(Local) {resposta}"
    
    # Padrões regex para tentar
    padroes = [
        (r'raiz\s+quadrada\s+de\s+(\d+)', lambda m: str(math.sqrt(float(m.group(1))))),
        (r'square root of (\d+)', lambda m: str(math.sqrt(float(m.group(1))))),
        (r'(\d+)\s*\+\s*(\d+)', lambda m: str(float(m.group(1)) + float(m.group(2)))),
        (r'(\d+)\s*\*\s*(\d+)', lambda m: str(float(m.group(1)) * float(m.group(2)))),
        (r'(\d+)\s*/\s*(\d+)', lambda m: str(float(m.group(1)) / float(m.group(2))) if float(m.group(2)) != 0 else "erro"),
        (r'(\d+)\s*\^\s*(\d+)', lambda m: str(float(m.group(1)) ** float(m.group(2)))),
        (r'(\d+)\s*!', lambda m: str(math.factorial(int(m.group(1))))),
    ]
    
    for padrao, funcao in padroes:
        match = re.search(padrao, problema_lower)
        if match:
            try:
                resultado = funcao(match)
                if resultado != "erro":
                    print(f"[Local] Resolvido com padrão: {resultado}")
                    return f"(Local) {resultado}"
            except:
                continue
    
    print(f"[Local] Não foi possível resolver: {problema_lower[:50]}...")
    return None

def resolver_problema_matematico(problema):
    """Resolve problemas matemáticos - GEMINI PRIMEIRO, DEPOIS LOCAL"""
    print(f"[Solver] Problema recebido: {problema[:50]}...")
    
    # 1. TENTAR GEMINI PRIMEIRO
    if GEMINI_API_KEY and len(GEMINI_API_KEY) > 20:
        print("[Solver] Tentando Gemini primeiro...")
        resultado = resolver_com_gemini(problema)
        if resultado:
            print(f"[Solver] Gemini resolveu: {resultado}")
            return resultado
    
    # 2. SE GEMINI FALHOU OU NÃO DISPONÍVEL, TENTAR LOCAL
    print("[Solver] Gemini não resolveu, tentando local...")
    resultado = resolver_problema_local(problema)
    if resultado:
        print(f"[Solver] Local resolveu: {resultado}")
        return resultado
    
    # 3. NADA FUNCIONOU
    mensagem_erro = "Não foi possível resolver. "
    if GEMINI_API_KEY:
        mensagem_erro += "Gemini falhou e não há solução local."
    else:
        mensagem_erro += "Gemini não configurado e não há solução local."
    
    return mensagem_erro

def executar_operacao(operacao, *args):
    try:
        if operacao == 'soma': 
            return sum(args)
        elif operacao == 'subtracao':
            r = args[0]
            for n in args[1:]: 
                r -= n
            return r
        elif operacao == 'produto':
            r = 1
            for n in args: 
                r *= n
            return r
        elif operacao == 'divisao':
            r = args[0]
            for n in args[1:]:
                if n == 0: 
                    return 'Erro: divisão por zero'
                r /= n
            return r
        elif operacao == 'fatorial': 
            return math.factorial(int(args[0]))
        elif operacao == 'potencia': 
            return args[0] ** args[1]
        elif operacao == 'raiz_quadrada': 
            return math.sqrt(args[0])
        elif operacao == 'ultimas_noticias': 
            return obter_noticias_uol(int(args[0]) if args else 5)
        elif operacao == 'math_problem_solver': 
            return resolver_problema_matematico(args[0] if args else '')
        else: 
            return 'Operação inválida'
    except Exception as e:
        return f'Erro: {e}'

def servidor_rpc():
    cache = carregar_cache()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((SERVIDOR_IP, SERVIDOR_PORTA))
        servidor.listen()
        print(f"Servidor RPC ativo em {SERVIDOR_IP}:{SERVIDOR_PORTA}")
        print(f"Gemini API: {'Configurada' if GEMINI_API_KEY and len(GEMINI_API_KEY) > 20 else 'Não configurada'}")

        while True:
            conexao, _ = servidor.accept()
            with conexao:
                dados = conexao.recv(8192)
                if not dados:
                    continue
                try:
                    req = json.loads(dados.decode('utf-8'))
                    operacao, args = req['operacao'], tuple(req.get('args', []))
                    chave = f"{operacao}:{args}"
                    
                    if chave in cache:
                        resultado = cache[chave]
                        print(f"[Cache] {operacao}{args}")
                    else:
                        resultado = executar_operacao(operacao, *args)
                        cache[chave] = resultado
                        salvar_cache(cache)
                        print(f"[Executado] {operacao}{args} → {str(resultado)[:50]}")
                    
                    conexao.sendall(json.dumps({'resultado': resultado}, ensure_ascii=False).encode('utf-8'))
                except Exception as e:
                    erro_msg = f'Erro: {e}'
                    conexao.sendall(json.dumps({'resultado': erro_msg}).encode('utf-8'))
                    print(f"[Erro] {e}")

if __name__ == "__main__":
        servidor_rpc()