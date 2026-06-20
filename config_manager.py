"""
config_manager.py

Gerencia as configuracoes persistentes da GathaAI:
- Qual provedor de IA externa esta configurado (anthropic, openai, groq, custom)
- A chave de API (armazenada localmente, em texto puro, no arquivo de config)
- O modelo a ser usado em cada provedor
- O modo de operacao atual: "local" (Ollama) ou "api" (IA externa via /logapi)

Nada aqui e enviado para fora da maquina do usuario, exceto quando uma
pergunta e de fato enviada para a API configurada em ia_api.py.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "api_config.json")

os.makedirs(CONFIG_DIR, exist_ok=True)

PROVEDORES_VALIDOS = ["anthropic", "openai", "groq", "custom"]

MODELOS_PADRAO = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4.1",
    "groq": "llama-3.3-70b-versatile",
    "custom": "",
}

PADRAO = {
    "modo": "local",        # "local" (Ollama) ou "api" (IA externa)
    "modelo_local": "qwen3:8b",
    "provedor": None,       # anthropic | openai | groq | custom
    "api_key": None,
    "modelo_api": None,
    "base_url": None,       # usado apenas pelo provedor "custom" (compatível com OpenAI)
}


def _carregar():
    if not os.path.exists(CONFIG_FILE):
        return dict(PADRAO)

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(PADRAO)

    config = dict(PADRAO)
    config.update(dados)
    return config


def _salvar(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def obter_config():
    """Retorna o dicionario de configuracao completo."""
    return _carregar()


def definir_api(provedor, api_key, modelo=None, base_url=None):
    """Salva a chave de API e o provedor escolhido."""

    provedor = provedor.lower().strip()

    if provedor not in PROVEDORES_VALIDOS:
        return False, (
            f"Provedor '{provedor}' nao reconhecido. "
            f"Use um destes: {', '.join(PROVEDORES_VALIDOS)}"
        )

    if provedor == "custom" and not base_url:
        return False, (
            "Para o provedor 'custom' informe a URL base, exemplo:\n"
            "/logapi custom SUA_CHAVE modelo https://api.exemplo.com/v1"
        )

    config = _carregar()

    config["provedor"] = provedor
    config["api_key"] = api_key
    config["modelo_api"] = modelo or MODELOS_PADRAO.get(provedor, "")
    config["base_url"] = base_url
    config["modo"] = "api"

    _salvar(config)

    return True, (
        f"Chave de API configurada para o provedor '{provedor}'.\n"
        f"Modelo: {config['modelo_api']}\n"
        f"Modo de resposta alterado automaticamente para: api"
    )


def remover_api():
    """Remove a chave de API salva e volta para o modo local."""

    config = _carregar()
    config["provedor"] = None
    config["api_key"] = None
    config["modelo_api"] = None
    config["base_url"] = None
    config["modo"] = "local"
    _salvar(config)

    return "Chave de API removida. Modo de resposta voltou para: local"


def definir_modo(modo, modelo_local=None):
    """Alterna entre 'local' (Ollama) e 'api' (IA externa configurada)."""

    modo = modo.lower().strip()

    if modo not in ("local", "api"):
        return False, "Modo invalido. Use: /modelo local  ou  /modelo api"

    config = _carregar()

    if modo == "api" and not config.get("api_key"):
        return False, (
            "Nenhuma chave de API configurada ainda.\n"
            "Use /logapi <provedor> <chave> antes de ativar o modo api."
        )

    config["modo"] = modo

    if modelo_local:
        config["modelo_local"] = modelo_local

    _salvar(config)

    return True, f"Modo de resposta alterado para: {modo}"


def mascarar_chave(chave):
    if not chave:
        return "(nao configurada)"

    if len(chave) <= 8:
        return "*" * len(chave)

    return chave[:4] + "*" * (len(chave) - 8) + chave[-4:]


def status_texto():
    config = _carregar()

    linhas = [
        "Status da GathaAI:",
        f"  Modo atual......: {config['modo']}",
        f"  Modelo local....: {config['modelo_local']}  (Ollama)",
        f"  Provedor de API.: {config['provedor'] or '(nenhum)'}",
        f"  Modelo de API...: {config['modelo_api'] or '(nenhum)'}",
        f"  Chave de API....: {mascarar_chave(config['api_key'])}",
    ]

    if config.get("provedor") == "custom":
        linhas.append(f"  URL base........: {config['base_url'] or '(nao definida)'}")

    return "\n".join(linhas)
