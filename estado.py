"""
estado.py

Guarda o estado da sessao atual (em memoria, nao persiste em disco):
- conteudo de um arquivo ou projeto carregado via /arquivo ou /analisar,
  que e injetado no proximo prompt enviado para a IA.
"""

arquivo_carregado = {
    "nome": None,
    "conteudo": None,
    "truncado": False,
}


def definir_arquivo(nome, conteudo, truncado=False):
    arquivo_carregado["nome"] = nome
    arquivo_carregado["conteudo"] = conteudo
    arquivo_carregado["truncado"] = truncado


def limpar_arquivo():
    arquivo_carregado["nome"] = None
    arquivo_carregado["conteudo"] = None
    arquivo_carregado["truncado"] = False


def tem_arquivo_carregado():
    return arquivo_carregado["conteudo"] is not None


def resumo_arquivo_carregado():
    if not tem_arquivo_carregado():
        return "Nenhum arquivo carregado no momento."

    aviso = " (conteudo truncado para caber no contexto)" if arquivo_carregado["truncado"] else ""
    tamanho = len(arquivo_carregado["conteudo"])

    return f"Arquivo carregado: {arquivo_carregado['nome']} ({tamanho} caracteres){aviso}"
