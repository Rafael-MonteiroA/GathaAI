from memoria import salvar
from memoria import recuperar

from internet import pesquisar

from comandos.comandos import executar_comando

from parser_acoes import (
    extrair_acao,
    executar_acao_extraida,
    limpar_acao_da_resposta,
)

from memoria_vetorial import (
    salvar_memoria,
    buscar_memoria
)

from fatos import (
    salvar as salvar_fato,
    listar
)

import config_manager
import estado
import ia_api
import threading
import time
import sys

try:
    from colorama import init as _init_colorama, Fore, Style
    _init_colorama()
    _COR_TITULO = Fore.RED + Style.BRIGHT
    _COR_IA = Fore.RED
    _COR_AVISO = Fore.YELLOW
    _COR_ERRO = Fore.GREEN
    _RESET = Style.RESET_ALL
except ImportError:
    _COR_TITULO = _COR_IA = _COR_AVISO = _COR_ERRO = _RESET = ""


BANNER = r"""
 ██████╗  █████╗ ████████╗██╗  ██╗ █████╗      █████╗ ██╗
██╔════╝ ██╔══██╗╚══██╔══╝██║  ██║██╔══██╗    ██╔══██╗██║
██║  ███╗███████║   ██║   ███████║███████║    ███████║██║
██║   ██║██╔══██║   ██║   ██╔══██║██╔══██║    ██╔══██║██║
╚██████╔╝██║  ██║   ██║   ██║  ██║██║  ██║    ██║  ██║██║
 ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝
"""


def barra_progresso(funcao, *args):
    """Executa `funcao(*args)` em thread separada enquanto exibe uma barra de progresso."""
    resultado = [None]
    erro = [None]
    concluido = threading.Event()

    def _worker():
        try:
            resultado[0] = funcao(*args)
        except Exception as e:
            erro[0] = e
        finally:
            concluido.set()

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

    largura = 30
    inicio = time.time()

    while not concluido.is_set():
        decorrido = time.time() - inicio
        # Progresso assintótico: avança rápido no início, desacelera perto de 100%
        pct = min(99, int(100 * (1 - 1 / (1 + decorrido / 8))))
        preenchido = int(largura * pct / 100)
        barra = "█" * preenchido + "░" * (largura - preenchido)
        sys.stdout.write(f"\r  {_COR_TITULO}[{barra}] {pct:3d}%{_RESET}")
        sys.stdout.flush()
        concluido.wait(timeout=0.15)

    # Barra completa
    barra = "█" * largura
    sys.stdout.write(f"\r  {_COR_TITULO}[{barra}] 100%{_RESET}\n")
    sys.stdout.flush()

    if erro[0] is not None:
        raise erro[0]

    return resultado[0]


PALAVRAS_WEB = [
    "o que é",
    "quem é",
    "notícia",
    "noticias",
    "pesquise",
    "pesquisar",
    "internet",
    "google",
    "procure",
    "buscar",
]


def montar_prompt(pergunta, contexto, contexto_memoria, fatos, web):

    bloco_arquivo = ""

    if estado.tem_arquivo_carregado():
        bloco_arquivo = f"""
Arquivo ou projeto carregado pelo usuário (use isso para ajudar no código,
revisão, debug ou planejamento do projeto quando for relevante):

{estado.arquivo_carregado['conteudo']}
"""

    # Montar bloco de atalhos personalizados
    atalhos = estado.obter_atalhos()
    bloco_atalhos = ""
    if atalhos:
        lista = ", ".join(f"{n} → {c}" for n, c in atalhos.items())
        bloco_atalhos = f"\nAtalhos personalizados do usuário: {lista}\n"

    return f"""
Você é GathaAI.

Regras:

- Responda sempre em português.
- Seja amigável.
- Seja útil.
- Não invente fatos sobre o usuário.
- Utilize memórias quando forem relevantes.
- Aprenda com as informações fornecidas.
- Quando houver um arquivo ou projeto de código carregado, use-o para dar
  respostas técnicas precisas: aponte bugs, sugira melhorias, explique o
  código ou ajude a continuar o desenvolvimento, conforme o que for pedido.
- Se não souber algo, admita.

Controle do Linux:

Você atua como um agente de sistema Linux. Quando o usuário pedir para abrir programas, gerenciar arquivos, controlar processos, instalar pacotes ou qualquer ação no sistema, inclua um bloco de ação no final da sua resposta. Responda amigavelmente informando o que será feito.

Formato: [AÇÃO]: {{"tipo": "...", ...}}

Ações disponíveis:
- abrir_programa: {{"tipo": "abrir_programa", "alvo": "nome do programa"}}
  Ex: chrome, firefox, vscode, spotify, discord
- abrir_url: {{"tipo": "abrir_url", "url": "https://..."}}
- instalar_programa: {{"tipo": "instalar_programa", "pacote": "nome_do_pacote"}}
- atualizar_sistema: {{"tipo": "atualizar_sistema"}}
- controle_processo: {{"tipo": "controle_processo", "acao": "fechar|matar", "alvo": "nome_ou_pid"}}
- gerenciar_arquivos: {{"tipo": "gerenciar_arquivos", "acao": "criar_pasta|mover|renomear|copiar|apagar", "origem": "caminho_1", "destino": "caminho_2_se_aplicavel"}}
- controle_energia: {{"tipo": "controle_energia", "acao": "desligar|reiniciar|hibernar|suspender"}}
- executar_comando_linux: {{"tipo": "executar_comando_linux", "comando_str": "comando completo"}}
  Ex: Use isso para comandos não mapeados, como 'systemctl restart bluetooth' ou 'find / -name arquivo'.

Regras para ações:
- Use APENAS UM bloco [AÇÃO] por resposta.
- A GathaAI tem níveis de risco, você será bloqueado de executar ações críticas (ex: rm -rf /).
- Responda de forma sucinta e deixe o System Agent lidar com a confirmação.
{bloco_atalhos}
Memória recente:

{contexto}

Memórias relevantes:

{contexto_memoria}

Fatos aprendidos:

{fatos}

Informações da internet:

{web}
{bloco_arquivo}
Pergunta:

{pergunta}
"""


def obter_resposta_ia(prompt):
    """
    Decide se a resposta vem do modelo local (Ollama) ou da IA externa
    configurada via /logapi, de acordo com o modo atual.
    """

    config = config_manager.obter_config()

    if config["modo"] == "api":
        return ia_api.perguntar_ia_externa(prompt)

    # Modo local (Ollama)
    try:
        import ollama
    except ImportError:
        raise RuntimeError(
            "O pacote 'ollama' não está instalado. Rode: pip install ollama\n"
            "Ou configure uma IA externa com /logapi e use /modelo api."
        )

    try:
        resposta = ollama.chat(
            model=config["modelo_local"],
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as erro:
        raise RuntimeError(
            f"Não foi possível falar com o Ollama local ({erro}).\n"
            "Verifique se o Ollama está instalado e rodando, ou use "
            "/logapi para configurar uma IA externa e depois /modelo api."
        )

    return resposta["message"]["content"]


def loop_principal():

    print(f"{_COR_TITULO}{BANNER}{_RESET}")
    print("Digite /ajuda para ver os comandos disponíveis. Digite 'sair' para encerrar.\n")

    while True:

        pergunta = input("\nVocê: ")

        if pergunta.lower() == "sair":
            print(f"{_COR_AVISO}Até mais!{_RESET}")
            break

        if not pergunta.strip():
            continue

        if pergunta.startswith("/"):

            resultado = executar_comando(pergunta)

            if resultado:
                print(resultado)

            continue

        memoria = recuperar()

        contexto = ""

        for user, resp in memoria:
            contexto += f"\nUsuário: {user}\n\nIA: {resp}\n"

        # Aprende fatos simples

        texto_lower = pergunta.lower()

        if "meu nome é" in texto_lower:
            salvar_fato(pergunta)

        if "meu cachorro se chama" in texto_lower:
            salvar_fato(pergunta)

        if "eu gosto de" in texto_lower:
            salvar_fato(pergunta)

        print("Consultando memória vetorial...")

        try:
            lembrancas = buscar_memoria(pergunta)
        except Exception as erro:
            print(f"{_COR_AVISO}(memória vetorial indisponível: {erro}){_RESET}")
            lembrancas = []

        contexto_memoria = "\n".join(lembrancas)

        fatos = "\n".join(listar())

        web = ""

        if any(p in texto_lower for p in PALAVRAS_WEB):
            print("Pesquisando internet...")
            web = pesquisar(pergunta)

        prompt = montar_prompt(pergunta, contexto, contexto_memoria, fatos, web)

        config = config_manager.obter_config()
        print(f"Consultando IA ({config['modo']})...\n")

        try:
            texto = barra_progresso(obter_resposta_ia, prompt)
        except (RuntimeError, ia_api.ErroAPI) as erro:
            print(f"{_COR_ERRO}Erro: {erro}{_RESET}")
            continue

        # Verificar se a IA quer executar uma ação no computador
        acao = extrair_acao(texto)
        texto_limpo = limpar_acao_da_resposta(texto) if acao else texto

        print(f"\n{_COR_IA}GathaAI:{_RESET}", texto_limpo)

        if acao:
            resultado_acao = executar_acao_extraida(acao)
            if resultado_acao:
                print(f"\n{_COR_AVISO}>> {resultado_acao}{_RESET}")

        salvar(pergunta, texto_limpo)

        try:
            salvar_memoria(f"\nUsuário:\n{pergunta}\n\nIA:\n{texto_limpo}\n")
        except Exception as erro:
            print(f"{_COR_AVISO}(não foi possível salvar na memória vetorial: {erro}){_RESET}")


if __name__ == "__main__":
    loop_principal()
