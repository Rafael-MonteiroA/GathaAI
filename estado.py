"""
estado.py

Guarda o estado da sessao atual (em memoria, nao persiste em disco):
- conteudo de um arquivo ou projeto carregado via /arquivo ou /analisar,
  que e injetado no proximo prompt enviado para a IA.
- atalhos personalizados para programas (persistidos via config_manager).
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


# ──────────────────────────────────────────────────────────────────────
# Atalhos personalizados para programas
# ──────────────────────────────────────────────────────────────────────

def obter_atalhos():
    """Retorna o dicionário de atalhos personalizados (persistidos em config)."""
    import config_manager
    config = config_manager.obter_config()
    return config.get("atalhos_pc", {})


def definir_atalho(nome, caminho):
    """Registra um atalho personalizado para um programa."""
    import config_manager
    config = config_manager.obter_config()
    atalhos = config.get("atalhos_pc", {})
    atalhos[nome.lower().strip()] = caminho.strip().strip('"')
    config["atalhos_pc"] = atalhos
    config_manager._salvar(config)


def remover_atalho(nome):
    """Remove um atalho personalizado."""
    import config_manager
    config = config_manager.obter_config()
    atalhos = config.get("atalhos_pc", {})
    nome_lower = nome.lower().strip()
    if nome_lower in atalhos:
        del atalhos[nome_lower]
        config["atalhos_pc"] = atalhos
        config_manager._salvar(config)
        return True
    return False


def listar_atalhos():
    """Retorna texto formatado com todos os atalhos."""
    atalhos = obter_atalhos()
    if not atalhos:
        return "Nenhum atalho personalizado registrado.\nUse: /atalho <nome> <caminho_do_executavel>"
    linhas = ["Atalhos personalizados:"]
    for nome, caminho in sorted(atalhos.items()):
        linhas.append(f"  {nome} → {caminho}")
    return "\n".join(linhas)
