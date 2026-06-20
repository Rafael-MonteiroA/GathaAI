"""
leitor_arquivos.py

Responsavel por ler e interpretar arquivos enviados pelo usuario:
- Arquivos de texto puro (.txt, .md, .json, .yaml, .csv, .log, ...)
- PDFs (extracao de texto)
- ZIPs (lista o conteudo e le os arquivos de texto/codigo de dentro)
- Codigos-fonte (C, C++, Python, Java e varias outras linguagens)

Tudo aqui le do disco local (caminho informado pelo usuario no terminal).
Nao ha upload remoto envolvido.
"""

import os
import zipfile
import tempfile

# Limite de caracteres enviados para o contexto da IA por arquivo.
# Evita estourar o tamanho do prompt em arquivos gigantes.
LIMITE_CARACTERES = 12000

# Limite de arquivos lidos ao analisar uma pasta ou um zip inteiro.
LIMITE_ARQUIVOS_PROJETO = 40

EXTENSOES_CODIGO = {
    ".py": "Python",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++ Header",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript (React)",
    ".tsx": "TypeScript (React)",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".asm": "Assembly",
    ".s": "Assembly",
    ".sh": "Shell",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
}

EXTENSOES_TEXTO = {
    ".txt", ".md", ".json", ".yaml", ".yml",
    ".csv", ".log", ".ini", ".cfg", ".toml",
    ".xml",
}

EXTENSOES_IGNORADAS_EM_PROJETO = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".pyc",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".bmp",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".pdf", ".db", ".index", ".pkl", ".lock",
}

PASTAS_IGNORADAS_EM_PROJETO = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    "dist", "build", "target", ".idea", ".vscode",
}


class ErroLeitura(Exception):
    pass


def _truncar(texto):
    if len(texto) > LIMITE_CARACTERES:
        return texto[:LIMITE_CARACTERES], True
    return texto, False


def _ler_texto_simples(caminho):
    with open(caminho, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _ler_pdf(caminho):
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ErroLeitura(
            "A biblioteca 'pypdf' nao esta instalada. "
            "Rode: pip install pypdf"
        )

    leitor = PdfReader(caminho)

    partes = []

    for pagina in leitor.pages:
        texto_pagina = pagina.extract_text() or ""
        partes.append(texto_pagina)

    return "\n".join(partes)


def _identificar_linguagem(caminho):
    _, ext = os.path.splitext(caminho)
    ext = ext.lower()
    return EXTENSOES_CODIGO.get(ext)


def ler_arquivo(caminho):
    """
    Le um unico arquivo (texto, codigo ou pdf) e retorna uma tupla:
    (conteudo_formatado, truncado)
    """

    if not os.path.exists(caminho):
        raise ErroLeitura(f"Arquivo nao encontrado: {caminho}")

    if os.path.isdir(caminho):
        raise ErroLeitura(
            f"'{caminho}' e uma pasta. Use /analisar para ler um projeto inteiro."
        )

    _, ext = os.path.splitext(caminho)
    ext = ext.lower()

    if ext == ".zip":
        return ler_zip(caminho)

    if ext == ".pdf":
        bruto = _ler_pdf(caminho)
        cabecalho = f"[PDF] {os.path.basename(caminho)}\n\n"
        conteudo, truncado = _truncar(bruto)
        return cabecalho + conteudo, truncado

    linguagem = _identificar_linguagem(caminho)

    if linguagem:
        bruto = _ler_texto_simples(caminho)
        cabecalho = f"[Codigo {linguagem}] {os.path.basename(caminho)}\n\n"
        conteudo, truncado = _truncar(bruto)
        return cabecalho + conteudo, truncado

    if ext in EXTENSOES_TEXTO or ext == "":
        bruto = _ler_texto_simples(caminho)
        cabecalho = f"[Texto] {os.path.basename(caminho)}\n\n"
        conteudo, truncado = _truncar(bruto)
        return cabecalho + conteudo, truncado

    raise ErroLeitura(
        f"Extensao '{ext}' nao suportada para leitura direta. "
        "Arquivos de texto, codigo (.py .c .cpp .java ...), .pdf e .zip sao suportados."
    )


def ler_zip(caminho_zip):
    """
    Extrai um .zip em uma pasta temporaria, le os arquivos de texto/codigo
    relevantes de dentro dele e retorna um resumo consolidado.
    """

    if not zipfile.is_zipfile(caminho_zip):
        raise ErroLeitura(f"'{caminho_zip}' nao e um arquivo .zip valido.")

    pasta_temp = tempfile.mkdtemp(prefix="gathaai_zip_")

    with zipfile.ZipFile(caminho_zip, "r") as z:
        nomes = z.namelist()
        z.extractall(pasta_temp)

    resultado = analisar_pasta(pasta_temp, origem=f"ZIP: {os.path.basename(caminho_zip)}")

    cabecalho = (
        f"[ZIP] {os.path.basename(caminho_zip)} "
        f"({len(nomes)} itens no arquivo)\n\n"
    )

    conteudo, truncado = _truncar(cabecalho + resultado)
    return conteudo, truncado


def analisar_pasta(caminho_pasta, origem=None):
    """
    Percorre uma pasta (projeto de codigo), monta uma arvore de arquivos
    e concatena o conteudo dos arquivos de codigo/texto encontrados,
    respeitando limites de tamanho e quantidade.
    """

    if not os.path.isdir(caminho_pasta):
        raise ErroLeitura(f"Pasta nao encontrada: {caminho_pasta}")

    arvore = []
    conteudos = []
    contador = 0

    for raiz, pastas, arquivos in os.walk(caminho_pasta):
        pastas[:] = [p for p in pastas if p not in PASTAS_IGNORADAS_EM_PROJETO]

        for nome_arquivo in sorted(arquivos):
            caminho_relativo = os.path.relpath(
                os.path.join(raiz, nome_arquivo), caminho_pasta
            )
            arvore.append(caminho_relativo)

    titulo_origem = origem or os.path.basename(caminho_pasta.rstrip(os.sep))

    partes = [
        f"Projeto: {titulo_origem}",
        f"Total de arquivos encontrados: {len(arvore)}",
        "",
        "Estrutura de arquivos:",
    ]
    partes.extend(f"  - {item}" for item in arvore[:200])

    if len(arvore) > 200:
        partes.append(f"  ... e mais {len(arvore) - 200} arquivo(s)")

    partes.append("")
    partes.append("Conteudo dos arquivos relevantes:")

    for caminho_relativo in arvore:
        if contador >= LIMITE_ARQUIVOS_PROJETO:
            partes.append(
                f"\n(limite de {LIMITE_ARQUIVOS_PROJETO} arquivos lidos atingido, "
                "os demais nao foram incluidos no contexto)"
            )
            break

        _, ext = os.path.splitext(caminho_relativo)
        ext = ext.lower()

        if ext in EXTENSOES_IGNORADAS_EM_PROJETO:
            continue

        e_codigo = ext in EXTENSOES_CODIGO
        e_texto = ext in EXTENSOES_TEXTO

        if not (e_codigo or e_texto):
            continue

        caminho_completo = os.path.join(caminho_pasta, caminho_relativo)

        try:
            bruto = _ler_texto_simples(caminho_completo)
        except OSError:
            continue

        # Para projetos, cada arquivo individual ganha um teto menor
        # para nao monopolizar o contexto.
        fatia = bruto[:3000]
        sufixo = "\n... (truncado)" if len(bruto) > 3000 else ""

        rotulo = EXTENSOES_CODIGO.get(ext, "Texto")

        partes.append(f"\n--- {caminho_relativo} [{rotulo}] ---\n{fatia}{sufixo}")

        contador += 1

    return "\n".join(partes)
