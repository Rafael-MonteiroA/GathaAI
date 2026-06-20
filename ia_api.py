"""
ia_api.py

Faz a chamada para uma IA externa via API, usando a configuracao salva
por config_manager.py (definida atraves do comando /logapi).

Provedores suportados:
- anthropic  -> api.anthropic.com/v1/messages
- openai     -> api.openai.com/v1/chat/completions
- groq       -> api.groq.com/openai/v1/chat/completions (compativel com OpenAI)
- custom     -> qualquer endpoint compativel com o formato de chat da OpenAI
"""

import requests

import config_manager

TIMEOUT_SEGUNDOS = 60

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class ErroAPI(Exception):
    pass


def _chamar_anthropic(prompt, api_key, modelo):
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": modelo,
        "max_tokens": 2048,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    resposta = requests.post(
        ANTHROPIC_URL, headers=headers, json=payload, timeout=TIMEOUT_SEGUNDOS
    )

    if resposta.status_code != 200:
        raise ErroAPI(
            f"Erro da API Anthropic ({resposta.status_code}): {resposta.text[:300]}"
        )

    dados = resposta.json()

    blocos_texto = [
        bloco["text"]
        for bloco in dados.get("content", [])
        if bloco.get("type") == "text"
    ]

    return "\n".join(blocos_texto).strip()


def _chamar_formato_openai(url, prompt, api_key, modelo):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": modelo,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    resposta = requests.post(
        url, headers=headers, json=payload, timeout=TIMEOUT_SEGUNDOS
    )

    if resposta.status_code != 200:
        raise ErroAPI(
            f"Erro da API ({resposta.status_code}): {resposta.text[:300]}"
        )

    dados = resposta.json()

    try:
        return dados["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        raise ErroAPI(f"Resposta inesperada da API: {dados}")


def perguntar_ia_externa(prompt):
    """
    Envia o prompt para o provedor de IA externa configurado via /logapi.
    Lanca ErroAPI em caso de falha.
    """

    config = config_manager.obter_config()

    provedor = config.get("provedor")
    api_key = config.get("api_key")
    modelo = config.get("modelo_api")

    if not provedor or not api_key:
        raise ErroAPI(
            "Nenhuma IA externa configurada. Use /logapi <provedor> <chave> primeiro."
        )

    try:
        if provedor == "anthropic":
            return _chamar_anthropic(prompt, api_key, modelo)

        if provedor == "openai":
            return _chamar_formato_openai(OPENAI_URL, prompt, api_key, modelo)

        if provedor == "groq":
            return _chamar_formato_openai(GROQ_URL, prompt, api_key, modelo)

        if provedor == "custom":
            base_url = config.get("base_url")
            if not base_url:
                raise ErroAPI("Provedor 'custom' configurado sem URL base.")
            return _chamar_formato_openai(base_url, prompt, api_key, modelo)

        raise ErroAPI(f"Provedor desconhecido: {provedor}")

    except requests.exceptions.Timeout:
        raise ErroAPI("A API demorou demais para responder (timeout).")

    except requests.exceptions.ConnectionError:
        raise ErroAPI("Nao foi possivel conectar a API. Verifique sua internet.")
