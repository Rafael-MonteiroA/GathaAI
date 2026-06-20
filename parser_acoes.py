"""
parser_acoes.py

Parser que extrai ações estruturadas da resposta da IA e as executa.
A IA inclui blocos no formato [AÇÃO]: {"tipo": "...", ...} nas suas respostas
quando o usuário pede para executar algo no computador.
"""

import json
import re

import acoes_pc


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
    Recebe o dict da ação e chama a função correspondente em acoes_pc.
    Retorna string de feedback.
    """
    if isinstance(acao, list):
        # Múltiplas ações
        resultados = []
        for a in acao:
            resultado = _executar_uma_acao(a)
            if resultado:
                resultados.append(resultado)
        return "\n".join(resultados)

    return _executar_uma_acao(acao)


def _executar_uma_acao(acao):
    """Executa uma única ação e retorna feedback."""
    tipo = acao.get("tipo", "").lower().strip()

    if tipo == "abrir_programa":
        alvo = acao.get("alvo", "")
        if not alvo:
            return "[ERRO] Ação 'abrir_programa' sem alvo especificado."
        return acoes_pc.abrir_programa(alvo)

    if tipo == "abrir_url":
        url = acao.get("url", "")
        if not url:
            return "[ERRO] Ação 'abrir_url' sem URL especificada."
        return acoes_pc.abrir_url(url)

    if tipo == "abrir_site":
        nome = acao.get("nome", acao.get("alvo", ""))
        if not nome:
            return "[ERRO] Ação 'abrir_site' sem nome especificado."
        return acoes_pc.abrir_site_conhecido(nome)

    if tipo == "pesquisar_google":
        termo = acao.get("termo", acao.get("query", ""))
        if not termo:
            return "[ERRO] Ação 'pesquisar_google' sem termo especificado."
        return acoes_pc.pesquisar_google(termo)

    if tipo == "abrir_pasta":
        caminho = acao.get("caminho", acao.get("alvo", ""))
        if not caminho:
            return "[ERRO] Ação 'abrir_pasta' sem caminho especificado."
        return acoes_pc.abrir_pasta(caminho)

    if tipo == "abrir_arquivo":
        caminho = acao.get("caminho", acao.get("alvo", ""))
        if not caminho:
            return "[ERRO] Ação 'abrir_arquivo' sem caminho especificado."
        return acoes_pc.abrir_arquivo(caminho)

    if tipo == "executar_comando":
        comando = acao.get("comando", acao.get("cmd", ""))
        if not comando:
            return "[ERRO] Ação 'executar_comando' sem comando especificado."
        return acoes_pc.executar_comando_shell(comando)

    if tipo == "controle_sistema":
        acao_sistema = acao.get("acao", acao.get("alvo", ""))
        if not acao_sistema:
            return "[ERRO] Ação 'controle_sistema' sem ação especificada."
        return acoes_pc.controle_sistema(acao_sistema)

    if tipo == "fechar_programa":
        alvo = acao.get("alvo", "")
        if not alvo:
            return "[ERRO] Ação 'fechar_programa' sem alvo especificado."
        return acoes_pc.fechar_programa(alvo)

    return f"[ERRO] Tipo de ação desconhecido: '{tipo}'"
