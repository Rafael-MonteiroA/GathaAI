import os

from memoria import recuperar
from memoria import limpar

from fatos import apagar

from memoria_vetorial import (
    apagar_memoria_vetorial
)

import config_manager
import estado
import leitor_arquivos

AJUDA_TEXTO = """
Comandos disponiveis:

  Conversa e memoria
  -------------------
  /ajuda                         mostra esta mensagem
  /memoria                       mostra o historico recente de conversa
  /limpar                        apaga apenas o historico de conversa
  /apagar_memoria                apaga conversa + memoria vetorial + fatos aprendidos
  /status                        mostra o estado atual da GathaAI

  Arquivos e projetos
  --------------------
  /arquivo <caminho>             carrega um arquivo (.txt .pdf .zip .py .c .cpp .java ...)
                                  como contexto para a proxima pergunta
  /analisar <caminho_da_pasta>   le um projeto inteiro (pasta ou .zip) e o
                                  carrega como contexto
  /limpar_arquivo                remove o arquivo/projeto atualmente carregado

  IA externa via API
  --------------------
  /logapi <provedor> <chave> [modelo]
                                  configura uma IA externa para auxiliar
                                  (provedores: anthropic, openai, groq, custom)
  /logapi custom <chave> <modelo> <url_base>
                                  configuracao para um endpoint customizado
                                  compativel com o formato da OpenAI
  /logapi status                 mostra o provedor/modelo configurados
  /logapi remover                remove a chave de API salva

  Modo de resposta
  ------------------
  /modelo local [nome_do_modelo] usa o modelo local via Ollama (padrao)
  /modelo api                    usa a IA externa configurada com /logapi
  /modelo status                 mostra o modo atual

  sair                            encerra a GathaAI
"""


def _formatar_memoria():
    mem = recuperar()

    if not mem:
        return "Nenhuma conversa registrada ainda."

    texto = ""
    for u, r in mem:
        texto += f"\nVocê: {u}\nIA: {r}\n"

    return texto


def _comando_logapi(partes):
    if len(partes) < 2:
        return (
            "Uso: /logapi <provedor> <chave> [modelo]\n"
            "Provedores: anthropic, openai, groq, custom\n"
            "Exemplo: /logapi anthropic sk-ant-xxxx claude-sonnet-4-6\n"
            "Tambem: /logapi status   |   /logapi remover"
        )

    sub = partes[1].lower()

    if sub == "status":
        return config_manager.status_texto()

    if sub == "remover":
        return config_manager.remover_api()

    provedor = partes[1]

    if len(partes) < 3:
        return "Faltou a chave de API. Uso: /logapi <provedor> <chave> [modelo]"

    chave = partes[2]
    modelo = partes[3] if len(partes) > 3 else None
    base_url = partes[4] if len(partes) > 4 else None

    if provedor.lower() == "custom" and len(partes) > 3:
        # /logapi custom <chave> <modelo> <url_base>
        modelo = partes[3]
        base_url = partes[4] if len(partes) > 4 else None

    ok, mensagem = config_manager.definir_api(
        provedor, chave, modelo=modelo, base_url=base_url
    )

    return mensagem


def _comando_modelo(partes):
    if len(partes) < 2:
        return config_manager.status_texto()

    sub = partes[1].lower()

    if sub == "status":
        return config_manager.status_texto()

    if sub == "local":
        modelo_local = partes[2] if len(partes) > 2 else None
        ok, mensagem = config_manager.definir_modo("local", modelo_local=modelo_local)
        return mensagem

    if sub == "api":
        ok, mensagem = config_manager.definir_modo("api")
        return mensagem

    return "Uso: /modelo local [nome_do_modelo]   ou   /modelo api   ou   /modelo status"


def _comando_arquivo(partes):
    if len(partes) < 2:
        return "Uso: /arquivo <caminho_do_arquivo>"

    caminho = " ".join(partes[1:]).strip().strip('"')

    try:
        conteudo, truncado = leitor_arquivos.ler_arquivo(caminho)
    except leitor_arquivos.ErroLeitura as erro:
        return f"Erro ao ler arquivo: {erro}"
    except Exception as erro:
        return f"Erro inesperado ao ler '{caminho}': {erro}"

    estado.definir_arquivo(os.path.basename(caminho), conteudo, truncado)

    aviso = " (conteudo truncado)" if truncado else ""

    return (
        f"Arquivo '{os.path.basename(caminho)}' carregado com sucesso{aviso}.\n"
        "Ele sera usado como contexto em todas as proximas perguntas, ate voce\n"
        "carregar outro arquivo ou usar /limpar_arquivo."
    )


def _comando_analisar(partes):
    if len(partes) < 2:
        return "Uso: /analisar <caminho_da_pasta_ou_zip>"

    caminho = " ".join(partes[1:]).strip().strip('"')

    try:
        if os.path.isdir(caminho):
            conteudo = leitor_arquivos.analisar_pasta(caminho)
            truncado = False
            if len(conteudo) > leitor_arquivos.LIMITE_CARACTERES:
                conteudo = conteudo[: leitor_arquivos.LIMITE_CARACTERES]
                truncado = True
        elif caminho.lower().endswith(".zip"):
            conteudo, truncado = leitor_arquivos.ler_zip(caminho)
        else:
            return "Informe uma pasta ou um arquivo .zip para /analisar."
    except leitor_arquivos.ErroLeitura as erro:
        return f"Erro ao analisar: {erro}"
    except Exception as erro:
        return f"Erro inesperado ao analisar '{caminho}': {erro}"

    estado.definir_arquivo(os.path.basename(caminho.rstrip("/\\")) or caminho, conteudo, truncado)

    aviso = " (conteudo truncado)" if truncado else ""

    return (
        f"Projeto '{caminho}' analisado e carregado como contexto{aviso}.\n"
        "Pergunte algo sobre o codigo, peca uma revisao, sugestoes ou correcoes.\n"
        "Use /limpar_arquivo para remove-lo do contexto."
    )


def executar_comando(comando):

    partes = comando.strip().split()

    if not partes:
        return None

    base = partes[0].lower()

    if base == "/ajuda":
        return AJUDA_TEXTO

    if base == "/memoria":
        return _formatar_memoria()

    if base == "/limpar":
        limpar()
        return "Memória de conversa apagada."

    if base == "/apagar_memoria":
        limpar()
        apagar()
        apagar_memoria_vetorial()
        return (
            "Memória completamente apagada.\n\n"
            "✓ Conversas\n"
            "✓ Memória vetorial\n"
            "✓ Fatos aprendidos"
        )

    if base == "/status":
        linhas = [
            config_manager.status_texto(),
            "",
            estado.resumo_arquivo_carregado(),
        ]
        return "\n".join(linhas)

    if base == "/logapi":
        return _comando_logapi(partes)

    if base == "/modelo":
        return _comando_modelo(partes)

    if base == "/arquivo":
        return _comando_arquivo(partes)

    if base == "/analisar":
        return _comando_analisar(partes)

    if base == "/limpar_arquivo":
        estado.limpar_arquivo()
        return "Arquivo/projeto removido do contexto."

    return f"Comando '{base}' nao reconhecido. Digite /ajuda para ver a lista de comandos."
