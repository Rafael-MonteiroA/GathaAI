"""
acoes_pc.py

Módulo de ações do computador para a GathaAI.
Permite abrir programas, URLs, pastas, executar comandos shell,
controlar o sistema (desligar, reiniciar, etc.) e mais.

Todas as funções retornam uma string de feedback para o usuário.
"""

import os
import subprocess
import webbrowser
import glob
import shutil


# ──────────────────────────────────────────────────────────────────────
# Dicionário de programas conhecidos no Windows
# Mapeia nomes amigáveis → possíveis nomes de executáveis / caminhos
# ──────────────────────────────────────────────────────────────────────

PROGRAMAS_CONHECIDOS = {
    # Navegadores
    "chrome": {
        "aliases": ["chrome", "google chrome", "navegador chrome"],
        "executaveis": ["chrome.exe"],
        "caminhos": [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ],
    },
    "firefox": {
        "aliases": ["firefox", "mozilla", "mozilla firefox"],
        "executaveis": ["firefox.exe"],
        "caminhos": [
            os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe"),
        ],
    },
    "edge": {
        "aliases": ["edge", "microsoft edge"],
        "executaveis": ["msedge.exe"],
        "caminhos": [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        ],
    },
    "brave": {
        "aliases": ["brave", "brave browser"],
        "executaveis": ["brave.exe"],
        "caminhos": [
            os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        ],
    },
    "opera": {
        "aliases": ["opera", "opera gx"],
        "executaveis": ["opera.exe", "launcher.exe"],
        "caminhos": [
            os.path.expandvars(r"%LocalAppData%\Programs\Opera GX\opera.exe"),
            os.path.expandvars(r"%LocalAppData%\Programs\Opera\opera.exe"),
        ],
    },

    # Comunicação
    "discord": {
        "aliases": ["discord"],
        "executaveis": ["Discord.exe", "Update.exe"],
        "caminhos": [
            os.path.expandvars(r"%LocalAppData%\Discord\Update.exe"),
        ],
        "args_especiais": ["--processStart", "Discord.exe"],
    },
    "telegram": {
        "aliases": ["telegram"],
        "executaveis": ["Telegram.exe"],
        "caminhos": [
            os.path.expandvars(r"%AppData%\Telegram Desktop\Telegram.exe"),
        ],
    },
    "whatsapp": {
        "aliases": ["whatsapp", "whats", "zap"],
        "executaveis": ["WhatsApp.exe"],
        "caminhos": [],
        "shell_cmd": "start whatsapp:",
    },

    # Jogos
    "valorant": {
        "aliases": ["valorant", "vava"],
        "executaveis": ["VALORANT.exe", "RiotClientServices.exe"],
        "caminhos": [
            r"C:\Riot Games\Riot Client\RiotClientServices.exe",
            os.path.expandvars(r"%ProgramFiles%\Riot Games\Riot Client\RiotClientServices.exe"),
        ],
        "args_especiais": ["--launch-product=valorant", "--launch-patchline=live"],
    },
    "league of legends": {
        "aliases": ["league of legends", "lol", "league"],
        "executaveis": ["RiotClientServices.exe", "LeagueClient.exe"],
        "caminhos": [
            r"C:\Riot Games\Riot Client\RiotClientServices.exe",
            os.path.expandvars(r"%ProgramFiles%\Riot Games\Riot Client\RiotClientServices.exe"),
        ],
        "args_especiais": ["--launch-product=league_of_legends", "--launch-patchline=live"],
    },
    "steam": {
        "aliases": ["steam"],
        "executaveis": ["steam.exe"],
        "caminhos": [
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam\steam.exe"),
            os.path.expandvars(r"%ProgramFiles%\Steam\steam.exe"),
        ],
    },
    "epic games": {
        "aliases": ["epic games", "epic", "epic games launcher"],
        "executaveis": ["EpicGamesLauncher.exe"],
        "caminhos": [
            os.path.expandvars(r"%ProgramFiles(x86)%\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe"),
        ],
    },
    "minecraft": {
        "aliases": ["minecraft", "mine"],
        "executaveis": ["MinecraftLauncher.exe"],
        "caminhos": [
            os.path.expandvars(r"%ProgramFiles(x86)%\Minecraft Launcher\MinecraftLauncher.exe"),
        ],
        "shell_cmd": "start minecraft:",
    },

    # Música / Mídia
    "spotify": {
        "aliases": ["spotify"],
        "executaveis": ["Spotify.exe"],
        "caminhos": [
            os.path.expandvars(r"%AppData%\Spotify\Spotify.exe"),
        ],
    },

    # Editores / IDEs
    "vscode": {
        "aliases": ["vscode", "visual studio code", "vs code", "code"],
        "executaveis": ["Code.exe"],
        "caminhos": [
            os.path.expandvars(r"%LocalAppData%\Programs\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft VS Code\Code.exe"),
        ],
    },
    "notepad++": {
        "aliases": ["notepad++", "notepad plus plus", "npp"],
        "executaveis": ["notepad++.exe"],
        "caminhos": [
            os.path.expandvars(r"%ProgramFiles%\Notepad++\notepad++.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Notepad++\notepad++.exe"),
        ],
    },
    "sublime text": {
        "aliases": ["sublime", "sublime text"],
        "executaveis": ["sublime_text.exe", "subl.exe"],
        "caminhos": [
            os.path.expandvars(r"%ProgramFiles%\Sublime Text\sublime_text.exe"),
            os.path.expandvars(r"%ProgramFiles%\Sublime Text 3\sublime_text.exe"),
        ],
    },

    # Utilitários do Windows
    "notepad": {
        "aliases": ["bloco de notas", "notepad", "bloco notas"],
        "executaveis": ["notepad.exe"],
        "caminhos": [r"C:\Windows\notepad.exe"],
    },
    "calculadora": {
        "aliases": ["calculadora", "calc", "calculator"],
        "executaveis": ["calc.exe"],
        "caminhos": [],
        "shell_cmd": "calc",
    },
    "paint": {
        "aliases": ["paint", "mspaint"],
        "executaveis": ["mspaint.exe"],
        "caminhos": [r"C:\Windows\System32\mspaint.exe"],
    },
    "explorador": {
        "aliases": ["explorador", "explorer", "explorador de arquivos", "gerenciador de arquivos"],
        "executaveis": ["explorer.exe"],
        "caminhos": [r"C:\Windows\explorer.exe"],
    },
    "cmd": {
        "aliases": ["cmd", "prompt de comando", "terminal", "prompt"],
        "executaveis": ["cmd.exe"],
        "caminhos": [r"C:\Windows\System32\cmd.exe"],
    },
    "powershell": {
        "aliases": ["powershell", "ps"],
        "executaveis": ["powershell.exe"],
        "caminhos": [r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"],
    },
    "gerenciador de tarefas": {
        "aliases": ["gerenciador de tarefas", "task manager", "taskmgr"],
        "executaveis": ["taskmgr.exe"],
        "caminhos": [r"C:\Windows\System32\Taskmgr.exe"],
    },
    "configuracoes": {
        "aliases": ["configurações", "configuracoes", "settings", "config do windows"],
        "executaveis": [],
        "caminhos": [],
        "shell_cmd": "start ms-settings:",
    },
    "lixeira": {
        "aliases": ["lixeira", "recycle bin"],
        "executaveis": [],
        "caminhos": [],
        "shell_cmd": "start shell:RecycleBinFolder",
    },
    "painel de controle": {
        "aliases": ["painel de controle", "control panel"],
        "executaveis": ["control.exe"],
        "caminhos": [r"C:\Windows\System32\control.exe"],
    },
    "word": {
        "aliases": ["word", "microsoft word"],
        "executaveis": ["WINWORD.EXE"],
        "caminhos": [],
    },
    "excel": {
        "aliases": ["excel", "microsoft excel"],
        "executaveis": ["EXCEL.EXE"],
        "caminhos": [],
    },
    "powerpoint": {
        "aliases": ["powerpoint", "ppt", "microsoft powerpoint"],
        "executaveis": ["POWERPNT.EXE"],
        "caminhos": [],
    },
}

# URLs conhecidas para atalhos rápidos
URLS_CONHECIDAS = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "reddit": "https://www.reddit.com",
    "twitch": "https://www.twitch.tv",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com.br",
    "whatsapp web": "https://web.whatsapp.com",
    "chatgpt": "https://chat.openai.com",
    "claude": "https://claude.ai",
    "stackoverflow": "https://stackoverflow.com",
}

# Pastas conhecidas do Windows
PASTAS_CONHECIDAS = {
    "downloads": os.path.expanduser("~\\Downloads"),
    "documentos": os.path.expanduser("~\\Documents"),
    "desktop": os.path.expanduser("~\\Desktop"),
    "área de trabalho": os.path.expanduser("~\\Desktop"),
    "area de trabalho": os.path.expanduser("~\\Desktop"),
    "imagens": os.path.expanduser("~\\Pictures"),
    "fotos": os.path.expanduser("~\\Pictures"),
    "músicas": os.path.expanduser("~\\Music"),
    "musicas": os.path.expanduser("~\\Music"),
    "vídeos": os.path.expanduser("~\\Videos"),
    "videos": os.path.expanduser("~\\Videos"),
    "appdata": os.path.expandvars(r"%AppData%"),
    "temp": os.path.expandvars(r"%Temp%"),
    "home": os.path.expanduser("~"),
    "pasta do usuário": os.path.expanduser("~"),
    "pasta do usuario": os.path.expanduser("~"),
}


# ──────────────────────────────────────────────────────────────────────
# Funções auxiliares
# ──────────────────────────────────────────────────────────────────────

def _encontrar_executavel(nome_programa):
    """
    Tenta encontrar o executável de um programa por:
    1. Atalhos personalizados do usuário
    2. Dicionário de programas conhecidos (caminhos fixos)
    3. Busca no PATH do sistema (shutil.which)
    4. Busca nos atalhos do Menu Iniciar (.lnk)
    """
    import estado

    nome_lower = nome_programa.lower().strip()

    # 1. Atalhos personalizados
    atalhos = estado.obter_atalhos()
    if nome_lower in atalhos:
        caminho = atalhos[nome_lower]
        if os.path.exists(caminho):
            return caminho, None, None
        return None, None, f"Atalho '{nome_lower}' aponta para '{caminho}', mas o arquivo não existe."

    # 2. Dicionário de programas conhecidos
    for chave, info in PROGRAMAS_CONHECIDOS.items():
        aliases = [a.lower() for a in info.get("aliases", [])]
        if nome_lower in aliases or nome_lower == chave.lower():
            # Verificar shell_cmd especial
            shell_cmd = info.get("shell_cmd")
            if shell_cmd:
                return None, shell_cmd, None

            # Verificar caminhos fixos
            for caminho in info.get("caminhos", []):
                if os.path.exists(caminho):
                    args = info.get("args_especiais")
                    return caminho, None, args

            # Tentar no PATH
            for exe in info.get("executaveis", []):
                encontrado = shutil.which(exe)
                if encontrado:
                    args = info.get("args_especiais")
                    return encontrado, None, args

    # 3. Busca genérica no PATH
    encontrado = shutil.which(nome_lower)
    if encontrado:
        return encontrado, None, None

    # Tentar com .exe
    if not nome_lower.endswith(".exe"):
        encontrado = shutil.which(nome_lower + ".exe")
        if encontrado:
            return encontrado, None, None

    # 4. Buscar nos atalhos do Menu Iniciar
    caminho_lnk = _buscar_menu_iniciar(nome_lower)
    if caminho_lnk:
        return caminho_lnk, None, None

    return None, None, None


def _buscar_menu_iniciar(nome):
    """Busca atalhos .lnk no Menu Iniciar que contenham o nome do programa."""
    pastas_menu = [
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
    ]

    for pasta in pastas_menu:
        if not os.path.isdir(pasta):
            continue

        for lnk in glob.glob(os.path.join(pasta, "**", "*.lnk"), recursive=True):
            nome_arquivo = os.path.splitext(os.path.basename(lnk))[0].lower()
            if nome in nome_arquivo or nome_arquivo in nome:
                return lnk

    return None


# ──────────────────────────────────────────────────────────────────────
# Ações principais
# ──────────────────────────────────────────────────────────────────────

def abrir_programa(nome):
    """Encontra e abre um programa pelo nome."""
    caminho, shell_cmd, args_extras = _encontrar_executavel(nome)

    if shell_cmd:
        try:
            os.system(shell_cmd)
            return f"[OK] '{nome}' aberto com sucesso."
        except Exception as e:
            return f"[ERRO] Erro ao abrir '{nome}': {e}"

    if caminho is None:
        # args_extras pode conter mensagem de erro do atalho
        if isinstance(args_extras, str):
            return f"[ERRO] {args_extras}"
        return (
            f"[ERRO] Não encontrei o programa '{nome}' no computador.\n"
            f"  Dica: use /atalho {nome} \"C:\\caminho\\do\\programa.exe\" para registrar."
        )

    try:
        cmd = [caminho]
        if isinstance(args_extras, list):
            cmd.extend(args_extras)

        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        return f"[OK] '{nome}' aberto com sucesso."
    except Exception as e:
        return f"[ERRO] Erro ao abrir '{nome}': {e}"


def abrir_url(url):
    """Abre uma URL no navegador padrão."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        webbrowser.open(url)
        return f"[OK] URL aberta: {url}"
    except Exception as e:
        return f"[ERRO] Erro ao abrir URL '{url}': {e}"


def pesquisar_google(termo):
    """Abre uma pesquisa no Google no navegador padrão."""
    import urllib.parse
    url = f"https://www.google.com/search?q={urllib.parse.quote(termo)}"
    try:
        webbrowser.open(url)
        return f"[OK] Pesquisa no Google aberta: '{termo}'"
    except Exception as e:
        return f"[ERRO] Erro ao pesquisar: {e}"


def abrir_pasta(caminho_ou_nome):
    """Abre uma pasta no explorador de arquivos."""
    # Verificar se é um nome conhecido
    nome_lower = caminho_ou_nome.lower().strip()
    caminho = PASTAS_CONHECIDAS.get(nome_lower, caminho_ou_nome)

    # Expandir variáveis de ambiente e ~
    caminho = os.path.expanduser(os.path.expandvars(caminho))

    if not os.path.isdir(caminho):
        return f"[ERRO] Pasta não encontrada: '{caminho}'"

    try:
        os.startfile(caminho)
        return f"[OK] Pasta aberta: {caminho}"
    except Exception as e:
        return f"[ERRO] Erro ao abrir pasta '{caminho}': {e}"


def abrir_arquivo(caminho):
    """Abre um arquivo com o programa padrão do sistema."""
    caminho = os.path.expanduser(os.path.expandvars(caminho))

    if not os.path.exists(caminho):
        return f"[ERRO] Arquivo não encontrado: '{caminho}'"

    try:
        os.startfile(caminho)
        return f"[OK] Arquivo aberto: {os.path.basename(caminho)}"
    except Exception as e:
        return f"[ERRO] Erro ao abrir arquivo '{caminho}': {e}"


def executar_comando_shell(comando):
    """
    Executa um comando no terminal.
    Pede confirmação do usuário antes de executar.
    """
    print(f"\n[!] A IA quer executar o seguinte comando no terminal:")
    print(f"    > {comando}")
    confirmacao = input("    Permitir? (s/n): ").strip().lower()

    if confirmacao not in ("s", "sim", "y", "yes"):
        return "[ERRO] Comando cancelado pelo usuário."

    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )

        saida = resultado.stdout.strip()
        erro = resultado.stderr.strip()

        if resultado.returncode == 0:
            msg = f"[OK] Comando executado com sucesso."
            if saida:
                msg += f"\n  Saída:\n{saida}"
            return msg
        else:
            msg = f"[ERRO] Comando retornou código {resultado.returncode}."
            if erro:
                msg += f"\n  Erro:\n{erro}"
            if saida:
                msg += f"\n  Saída:\n{saida}"
            return msg

    except subprocess.TimeoutExpired:
        return "[ERRO] Comando excedeu o tempo limite (30s)."
    except Exception as e:
        return f"[ERRO] Erro ao executar comando: {e}"


def controle_sistema(acao):
    """Executa ações de controle do sistema (desligar, reiniciar, etc.)."""
    acao = acao.lower().strip()

    ACOES_SISTEMA = {
        "desligar": ("shutdown /s /t 60", "O computador será desligado em 60 segundos. Use 'shutdown /a' para cancelar."),
        "reiniciar": ("shutdown /r /t 60", "O computador será reiniciado em 60 segundos. Use 'shutdown /a' para cancelar."),
        "hibernar": ("shutdown /h", "O computador entrará em hibernação."),
        "bloquear": ("rundll32.exe user32.dll,LockWorkStation", "Tela bloqueada."),
        "suspender": ("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", "Computador suspenso."),
        "cancelar desligamento": ("shutdown /a", "Desligamento/reinicialização cancelado."),
    }

    if acao not in ACOES_SISTEMA:
        acoes_str = ", ".join(ACOES_SISTEMA.keys())
        return f"[ERRO] Ação de sistema desconhecida: '{acao}'. Ações disponíveis: {acoes_str}"

    comando, descricao = ACOES_SISTEMA[acao]

    # Sempre pedir confirmação para ações de sistema
    print(f"\n[!] A IA quer executar uma acao de sistema: {acao.upper()}")
    print(f"    Comando: {comando}")
    confirmacao = input("    Permitir? (s/n): ").strip().lower()

    if confirmacao not in ("s", "sim", "y", "yes"):
        return "[ERRO] Ação de sistema cancelada pelo usuário."

    try:
        os.system(comando)
        return f"[OK] {descricao}"
    except Exception as e:
        return f"[ERRO] Erro ao executar ação de sistema: {e}"


def fechar_programa(nome):
    """Fecha um programa pelo nome do processo."""
    nome_lower = nome.lower().strip()

    # Encontrar o nome do executável
    nomes_processo = [nome_lower]

    for chave, info in PROGRAMAS_CONHECIDOS.items():
        aliases = [a.lower() for a in info.get("aliases", [])]
        if nome_lower in aliases or nome_lower == chave.lower():
            nomes_processo.extend([e.lower().replace(".exe", "") for e in info.get("executaveis", [])])
            break

    print(f"\n[!] A IA quer fechar o programa: {nome}")
    confirmacao = input("    Permitir? (s/n): ").strip().lower()

    if confirmacao not in ("s", "sim", "y", "yes"):
        return "[ERRO] Ação cancelada pelo usuário."

    for proc_nome in set(nomes_processo):
        exe_nome = proc_nome if proc_nome.endswith(".exe") else proc_nome + ".exe"
        try:
            resultado = subprocess.run(
                ["taskkill", "/IM", exe_nome, "/F"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if resultado.returncode == 0:
                return f"[OK] '{nome}' fechado com sucesso."
        except Exception:
            continue

    return f"[ERRO] Não foi possível fechar '{nome}'. O programa pode não estar aberto."


def abrir_site_conhecido(nome):
    """Abre um site pelo nome amigável (google, youtube, etc.)."""
    nome_lower = nome.lower().strip()

    url = URLS_CONHECIDAS.get(nome_lower)
    if url:
        return abrir_url(url)

    return f"[ERRO] Site '{nome}' não reconhecido. Tente fornecer a URL completa."
