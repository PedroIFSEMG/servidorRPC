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
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MODEL_BACKUP
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
    """Resolve problemas usando Gemini API - TENTATIVA PRIMÁRIA"""
    if not GEMINI_API_KEY or len(GEMINI_API_KEY) < 20:
        print("[Gemini] Chave não configurada")
        return None
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Modelos para tentar (em ordem de preferência)
        modelos = [
            'gemini-3-flash-preview',  # Modelo mais novo
            'gemini-2.0-flash-exp',    # Alternativa
            'gemini-pro',              # Modelo estável
            'models/gemini-pro',       # Outro formato
        ]
        
        for modelo_nome in modelos:
            try:
                print(f"[Gemini] Tentando modelo: {modelo_nome}")
                model = genai.GenerativeModel(modelo_nome)
                
                # Prompt com Chain-of-Thought
                prompt = f"""Você é um assistente matemático.
                Resolva este problema passo a passo (Chain-of-Thought), 
                mas forneça APENAS o resultado numérico final.

                Problema: {problema}

                Instruções:
                1. Faça o raciocínio passo a passo internamente
                2. Realize todos os cálculos necessários
                3. A resposta final deve ser APENAS o número
                4. Use ponto para decimais
                5. Formato: [resultado]

                Exemplo: Para "2+2", responda: [4]

                Agora resolva: {problema}"""
                
                response = model.generate_content(prompt)
                resultado = response.text.strip()
                print(f"[Gemini] Resposta: {resultado[:100]}...")
                
                # Extrair número da resposta
                match = re.search(r'\[?(?P<numero>-?\d+(\.\d+)?)\]?', resultado)
                if match:
                    return f"(Gemini) {match.group('numero')}"
                
                # Tentar limpar a resposta
                linhas = resultado.split('\n')
                for linha in reversed(linhas):  # Começar do final
                    linha_limpa = linha.strip()
                    if linha_limpa and any(c.isdigit() for c in linha_limpa):
                        numeros = re.findall(r'-?\d+(?:\.\d+)?', linha_limpa)
                        if numeros:
                            return f"(Gemini) {numeros[-1]}"
                
                return f"(Gemini) {resultado[:50]}..."
                
            except Exception as e_modelo:
                erro_msg = str(e_modelo).lower()
                if "not found" in erro_msg or "not supported" in erro_msg:
                    continue  # Tenta próximo modelo
                else:
                    print(f"[Gemini] Erro no modelo {modelo_nome}: {e_modelo}")
                    break  # Outro erro, para de tentar
        
        return None  # Todos os modelos falharam
        
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
        print("Estratégia: Gemini primeiro → Local fallback")

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
