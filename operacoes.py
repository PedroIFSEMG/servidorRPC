import socket, json, os
from collections import OrderedDict
from config import SERVIDOR_IP, SERVIDOR_PORTA, TIMEOUT_CONEXAO

class RPCServerNotFound(Exception): pass

class Operacoes:
    def __init__(self, ip=SERVIDOR_IP, porta=SERVIDOR_PORTA):
        self.ip = ip
        self.porta = porta
        self.cache = OrderedDict()

    def _enviar_requisicao(self, operacao, *args):
        chave_cache = (operacao, args)
        if chave_cache in self.cache:
            print('→ Cliente: resultado do cache em memória.')
            return self.cache[chave_cache]
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
                cliente.settimeout(TIMEOUT_CONEXAO)
                cliente.connect((self.ip, self.porta))
                dados = json.dumps({'operacao': operacao, 'args': args}).encode('utf-8')
                cliente.sendall(dados)
                resposta = cliente.recv(16384)
                resultado = json.loads(resposta.decode('utf-8'))['resultado']
                self.cache[chave_cache] = resultado
                return resultado
        except (ConnectionRefusedError, socket.timeout):
            raise RPCServerNotFound("Servidor RPC não encontrado ou inativo.")
        except Exception as e:
            raise Exception(f"Erro: {e}")

    # Operações matemáticas
    def soma(self, *args): return self._enviar_requisicao('soma', *args)
    def subtracao(self, *args): return self._enviar_requisicao('subtracao', *args)
    def produto(self, *args): return self._enviar_requisicao('produto', *args)
    def divisao(self, *args): return self._enviar_requisicao('divisao', *args)
    def fatorial(self, n): return self._enviar_requisicao('fatorial', n)
    def potencia(self, base, exp): return self._enviar_requisicao('potencia', base, exp)
    def raiz_quadrada(self, n): return self._enviar_requisicao('raiz_quadrada', n)
    def ultimas_noticias(self, qtd): return self._enviar_requisicao('ultimas_noticias', qtd)
    def math_problem_solver(self, problema): return self._enviar_requisicao('math_problem_solver', problema)