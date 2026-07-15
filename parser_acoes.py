"""
parser_acoes.py

Parser que extrai ações estruturadas da resposta da IA e as executa.
A IA inclui blocos no formato [AÇÃO]: {"tipo": "...", ...} nas suas respostas
quando o usuário pede para executar algo no computador.
"""

import json
import re

import system_agent

# Regex para encontrar blocos de ação na resposta da IA
# Aceita [AÇÃO], [ACAO], [ACTION] (case-insensitive)
PADRAO_ACAO = re.compile(
    r'\[A[ÇC](?:[ÃA]O|TION)\]\s*:\s*(\{.*?\})',
    re.IGNORECASE | re.DOTALL,
)


def extrair_acao(resposta_ia):
    """
    Busca um bloco [AÇÃO]: {...} na resposta da IA.
    Retorna o dict da ação, ou None se não houver.
    Pode retornar múltiplas ações em uma lista se houver mais de uma.
    """
    matches = PADRAO_ACAO.findall(resposta_ia)

    if not matches:
        return None

    acoes = []
    for match in matches:
        try:
            acao = json.loads(match)
            if isinstance(acao, dict) and "tipo" in acao:
                acoes.append(acao)
        except json.JSONDecodeError:
            continue

    if not acoes:
        return None

    return acoes if len(acoes) > 1 else acoes[0]


def limpar_acao_da_resposta(resposta_ia):
    """
    Remove os blocos [AÇÃO]: {...} da resposta para exibição limpa ao usuário.
    """
    texto_limpo = PADRAO_ACAO.sub("", resposta_ia).strip()
    # Remover linhas vazias duplas resultantes
    texto_limpo = re.sub(r'\n{3,}', '\n\n', texto_limpo)
    return texto_limpo


def executar_acao_extraida(acao):
    """
    Recebe o dict da ação e chama a função correspondente no system_agent.
    Retorna string de feedback.
    """
    if isinstance(acao, list):
        # Múltiplas ações
        resultados = []
        for a in acao:
            resultado = system_agent.agent.processar_acao_ia(a)
            if resultado:
                resultados.append(resultado)
        return "\n".join(resultados)

    return system_agent.agent.processar_acao_ia(acao)
