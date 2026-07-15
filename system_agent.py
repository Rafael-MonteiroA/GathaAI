"""
system_agent.py

Agente do Sistema Linux da GathaAI.
Responsável por interpretar, validar e executar ações no sistema com segurança.
Utiliza níveis de risco e evita a execução via shell=True.
"""

import os
import subprocess
import shutil
from typing import List, Optional, Tuple, Dict, Any

# =====================================================================
# Configurações de Cores para o Terminal (copiado de chatbot.py)
# =====================================================================
try:
    from colorama import Fore, Style
    COR_AVISO = Fore.YELLOW
    COR_ERRO = Fore.RED
    COR_SUCESSO = Fore.GREEN
    COR_TITULO = Fore.CYAN + Style.BRIGHT
    RESET = Style.RESET_ALL
except ImportError:
    COR_AVISO = COR_ERRO = COR_SUCESSO = COR_TITULO = RESET = ""


# =====================================================================
# Níveis de Risco
# =====================================================================
class RiskLevel:
    SEGURO = 0     # Automático (Ex: abrir programas, listar arquivos)
    MODERADO = 1   # Confirmação simples [S/N] (Ex: instalar programas, reiniciar serviços)
    ALTO = 2       # Dupla confirmação [CONFIRMAR] (Ex: remover programas, matar processos)
    CRITICO = 3    # Bloqueio total (Ex: formatar discos, apagar raiz)


# =====================================================================
# Utilitários de Detecção de OS
# =====================================================================
def detect_package_manager() -> str:
    """Detecta o gerenciador de pacotes baseado na distro."""
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release", "r") as f:
            content = f.read().lower()
            if "arch" in content or "manjaro" in content:
                return "pacman"
            elif "ubuntu" in content or "debian" in content or "mint" in content:
                return "apt"
            elif "fedora" in content:
                return "dnf"
            elif "suse" in content:
                return "zypper"
    return "apt" # fallback

# =====================================================================
# Agente Principal
# =====================================================================
class SystemAgent:
    def __init__(self):
        self.pkg_mgr = detect_package_manager()
        self._history = []

    def register_history(self, action_desc: str):
        """Registra a ação executada."""
        import datetime
        now = datetime.datetime.now().strftime("%H:%M")
        self._history.append(f"{now} ✔ {action_desc}")
        
    def get_history(self) -> str:
        return "\n".join(self._history)

    def _ask_confirmation(self, action_name: str, cmd_list: List[str], risk_level: int) -> bool:
        """Pede confirmação do usuário baseado no risco."""
        if risk_level == RiskLevel.SEGURO:
            return True

        print(f"\n{COR_TITULO}Ação:{RESET} {action_name}")
        
        # Oculta comandos muito extensos ou arrays puramente lógicos se for None
        if cmd_list:
            print(f"{COR_TITULO}Comando:{RESET} {' '.join(cmd_list)}")
            
        if risk_level == RiskLevel.MODERADO:
            print(f"{COR_TITULO}Nível de risco:{RESET} {COR_AVISO}Moderado{RESET}")
            resp = input(f"Deseja continuar? [S/N]: ").strip().lower()
            return resp in ["s", "sim", "y", "yes"]

        elif risk_level == RiskLevel.ALTO:
            print(f"{COR_TITULO}Nível de risco:{RESET} {COR_ERRO}ALTO{RESET}")
            print(f"{COR_ERRO}Esta ação é destrutiva e pode causar perda de dados ou comportamento inesperado.{RESET}")
            resp = input(f"Digite 'CONFIRMAR' para prosseguir: ").strip()
            return resp == "CONFIRMAR"

        elif risk_level == RiskLevel.CRITICO:
            print(f"{COR_TITULO}Nível de risco:{RESET} {COR_ERRO}CRÍTICO{RESET}")
            print("Essa ação possui risco crítico para o sistema.")
            print("Por segurança, a GathaAI não executa esse tipo de operação automaticamente.")
            return False
            
        return False

    def _execute_command(self, cmd_list: List[str], capture: bool = True) -> Tuple[bool, str]:
        """Executa um comando de forma segura sem shell=True."""
        try:
            # Exibir comando rodando se não capturar (ex: pacman pede input)
            if not capture:
                proc = subprocess.run(cmd_list, shell=False)
                return (proc.returncode == 0, "")
            else:
                proc = subprocess.run(
                    cmd_list,
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    encoding="utf-8",
                    errors="replace"
                )
                success = proc.returncode == 0
                output = proc.stdout.strip()
                error = proc.stderr.strip()
                
                res_str = output
                if not success and error:
                    res_str += f"\nErro: {error}"
                    
                return (success, res_str)
        except Exception as e:
            return (False, str(e))

    def _eval_risk_custom_cmd(self, cmd_list: List[str]) -> int:
        """Avalia heurísticamente comandos customizados da IA."""
        cmd_str = " ".join(cmd_list).lower()
        if "rm -rf /" in cmd_str or "mkfs" in cmd_str or "dd if=" in cmd_str:
            return RiskLevel.CRITICO
        if "rm " in cmd_str or "kill" in cmd_str or "chmod" in cmd_str or "chown" in cmd_str:
            return RiskLevel.ALTO
        if "pacman -s" in cmd_str or "apt install" in cmd_str or "systemctl" in cmd_str or "dnf" in cmd_str:
            return RiskLevel.MODERADO
        return RiskLevel.SEGURO

    # -----------------------------------------------------------------
    # Handlers Específicos
    # -----------------------------------------------------------------

    def handle_abrir_programa(self, nome: str) -> str:
        """Nível 0 - Abrir programas comuns do Linux (nohup / detached)."""
        nome_lower = nome.lower()
        mapping = {
            "chrome": "google-chrome-stable",
            "google chrome": "google-chrome-stable",
            "vscode": "code",
            "code": "code",
            "discord": "discord",
            "spotify": "spotify",
            "steam": "steam",
            "firefox": "firefox",
            "brave": "brave-browser",
            "libreoffice": "libreoffice",
            "gimp": "gimp",
            "blender": "blender",
            "obs": "obs",
            "dolphin": "dolphin",
            "nautilus": "nautilus",
            "kitty": "kitty",
            "alacritty": "alacritty",
            "intellij": "idea",
            "pycharm": "pycharm-community",
            "calculadora": "gnome-calculator",
        }
        
        exe = mapping.get(nome_lower, nome_lower)
        cmd_list = [exe]

        if not self._ask_confirmation(f"Abrir {nome}", cmd_list, RiskLevel.SEGURO):
            return f"Abertura de {nome} cancelada."
            
        try:
            # Popen para não travar a IA
            subprocess.Popen(
                cmd_list,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            self.register_history(f"abriu {nome}")
            return f"[OK] '{nome}' aberto com sucesso."
        except FileNotFoundError:
            return f"[ERRO] Programa '{exe}' não encontrado no sistema."
        except Exception as e:
            return f"[ERRO] Erro ao abrir '{nome}': {e}"

    def handle_instalar_pacote(self, pacote: str) -> str:
        """Nível 1 - Instalar programas nativos."""
        if self.pkg_mgr == "pacman":
            cmd = ["sudo", "pacman", "-S", "--noconfirm", pacote]
        elif self.pkg_mgr == "apt":
            cmd = ["sudo", "apt", "install", "-y", pacote]
        elif self.pkg_mgr == "dnf":
            cmd = ["sudo", "dnf", "install", "-y", pacote]
        elif self.pkg_mgr == "zypper":
            cmd = ["sudo", "zypper", "in", "-y", pacote]
        else:
            return "[ERRO] Gerenciador de pacotes desconhecido."

        if not self._ask_confirmation(f"Instalar {pacote}", cmd, RiskLevel.MODERADO):
            return "[Aviso] Instalação cancelada pelo usuário."
            
        print(f"\n{COR_SUCESSO}Instalando {pacote}...{RESET}")
        success, output = self._execute_command(cmd, capture=False)
        if success:
            self.register_history(f"instalou {pacote}")
            return f"[OK] {pacote} instalado com sucesso."
        else:
            return f"[ERRO] Falha ao instalar {pacote}."

    def handle_atualizar_sistema(self) -> str:
        """Nível 1 - Atualizar sistema."""
        if self.pkg_mgr == "pacman":
            cmd = ["sudo", "pacman", "-Syu", "--noconfirm"]
        elif self.pkg_mgr == "apt":
            # APT requer update e upgrade, para simplificar vamos fazer os dois
            cmd = ["sudo", "bash", "-c", "apt update && apt upgrade -y"]
        elif self.pkg_mgr == "dnf":
            cmd = ["sudo", "dnf", "upgrade", "-y"]
        elif self.pkg_mgr == "zypper":
            cmd = ["sudo", "zypper", "dup", "-y"]
            
        if not self._ask_confirmation("Atualizar Sistema", cmd, RiskLevel.MODERADO):
            return "Atualização cancelada."
            
        print(f"\n{COR_SUCESSO}Atualizando sistema...{RESET}")
        success, output = self._execute_command(cmd, capture=False)
        if success:
            self.register_history("atualizou o sistema")
            return "[OK] Sistema atualizado."
        return "[ERRO] Falha ao atualizar o sistema."

    def handle_controle_processos(self, acao: str, alvo: str) -> str:
        """Nível 1 ou 2 - Matar processos."""
        if acao == "fechar" or acao == "matar":
            # se for string (nome)
            if not alvo.isdigit():
                cmd = ["pkill", alvo]
                risk = RiskLevel.MODERADO
            else:
                cmd = ["kill", "-9", alvo]
                risk = RiskLevel.ALTO
                
            if not self._ask_confirmation(f"Fechar processo {alvo}", cmd, risk):
                return "Ação cancelada."
                
            succ, out = self._execute_command(cmd)
            if succ:
                self.register_history(f"fechou o processo {alvo}")
                return f"[OK] Processo {alvo} fechado."
            return f"[ERRO] Falha ao fechar {alvo}."
            
        return "[ERRO] Ação de processo desconhecida."

    def handle_gerenciar_arquivos(self, acao: str, origem: str, destino: str = "") -> str:
        """Níveis variáveis para arquivos."""
        if acao == "criar_pasta":
            cmd = ["mkdir", "-p", origem]
            risk = RiskLevel.SEGURO
        elif acao == "mover":
            cmd = ["mv", origem, destino]
            risk = RiskLevel.SEGURO
        elif acao == "renomear":
            cmd = ["mv", origem, destino]
            risk = RiskLevel.SEGURO
        elif acao == "copiar":
            cmd = ["cp", "-r", origem, destino]
            risk = RiskLevel.SEGURO
        elif acao == "apagar":
            cmd = ["rm", "-rf", origem]
            risk = RiskLevel.ALTO
        else:
            return f"[ERRO] Ação de arquivo desconhecida: {acao}"

        if not self._ask_confirmation(f"{acao.title()} arquivo/pasta {origem}", cmd, risk):
            return "Ação cancelada."

        succ, out = self._execute_command(cmd)
        if succ:
            self.register_history(f"executou arquivo: {acao} {origem}")
            return f"[OK] Operação '{acao}' realizada."
        return f"[ERRO] Falha na operação: {out}"

    def handle_comando_customizado(self, cmd_str: str) -> str:
        """Executa comandos customizados (qualquer coisa que a IA inferir)."""
        import shlex
        try:
            cmd_list = shlex.split(cmd_str)
        except Exception:
            # Caso dê erro de shlex, fallback básico
            cmd_list = cmd_str.split()
            
        risk = self._eval_risk_custom_cmd(cmd_list)
        if risk == RiskLevel.CRITICO:
            return "[BLOQUEADO] Essa ação possui risco crítico para o sistema. Por segurança, a GathaAI não executa esse tipo de operação automaticamente."

        if not self._ask_confirmation(f"Executar Comando", cmd_list, risk):
            return "Comando cancelado."

        succ, out = self._execute_command(cmd_list)
        if succ:
            self.register_history(f"executou comando custom: {cmd_str}")
            return f"[OK] Comando executado. Saída:\n{out}"
        return f"[ERRO] Falha no comando. Erro:\n{out}"

    def handle_controle_energia(self, acao: str) -> str:
        if acao == "desligar":
            cmd = ["systemctl", "poweroff"]
        elif acao == "reiniciar":
            cmd = ["systemctl", "reboot"]
        elif acao == "hibernar":
            cmd = ["systemctl", "hibernate"]
        elif acao == "suspender":
            cmd = ["systemctl", "suspend"]
        else:
            return "[ERRO] Ação de energia desconhecida."
            
        if not self._ask_confirmation(f"Energia: {acao.upper()}", cmd, RiskLevel.ALTO):
            return "Ação de energia cancelada."
            
        succ, out = self._execute_command(cmd)
        return "[OK] Executado." if succ else f"[ERRO] {out}"

    def processar_acao_ia(self, acao: Dict[str, Any]) -> str:
        """
        Recebe o dicionário de ação da IA e roteia para o handler apropriado.
        """
        tipo = acao.get("tipo", "").lower().strip()
        
        try:
            if tipo == "abrir_programa":
                return self.handle_abrir_programa(acao.get("alvo", ""))
            
            elif tipo == "abrir_url" or tipo == "abrir_site":
                url = acao.get("url", acao.get("alvo", ""))
                if not url.startswith("http"): url = "https://" + url
                import webbrowser
                webbrowser.open(url)
                return f"[OK] URL {url} aberta no navegador."
                
            elif tipo == "instalar_programa":
                return self.handle_instalar_pacote(acao.get("pacote", ""))
                
            elif tipo == "atualizar_sistema":
                return self.handle_atualizar_sistema()
                
            elif tipo == "controle_processo":
                return self.handle_controle_processos(acao.get("acao", ""), acao.get("alvo", ""))
                
            elif tipo == "gerenciar_arquivos":
                return self.handle_gerenciar_arquivos(acao.get("acao", ""), acao.get("origem", ""), acao.get("destino", ""))
                
            elif tipo == "controle_energia":
                return self.handle_controle_energia(acao.get("acao", ""))
                
            elif tipo == "executar_comando_linux":
                cmd = acao.get("comando_str", "")
                if cmd:
                    return self.handle_comando_customizado(cmd)
                return "[ERRO] Comando customizado não fornecido."
                
            else:
                # Fallback genérico - tenta executar como comando linux se 'comando_str' existir
                cmd = acao.get("comando_str", "")
                if cmd:
                    return self.handle_comando_customizado(cmd)
                    
                return f"[ERRO] Ação desconhecida: {tipo}"
                
        except Exception as e:
            return f"[ERRO_FATAL] Erro ao processar a ação '{tipo}': {str(e)}"

# Singleton
agent = SystemAgent()
