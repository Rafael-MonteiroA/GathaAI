<div align="left">

<img src="assets/logo.png" alt="GathaAI" width="800">

---
<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/SQLite-Memória-003B57?style=for-the-badge&logo=sqlite&logoColor=white">
  <img src="https://img.shields.io/badge/FAISS-Vetorial-FF6F00?style=for-the-badge">
  <img src="https://img.shields.io/badge/Ollama-Local-000000?style=for-the-badge">
</p>

<img src="https://img.shields.io/github/stars/Rafael-MonteiroA/GathaAI?style=flat-square">
<img src="https://img.shields.io/github/forks/Rafael-MonteiroA/GathaAI?style=flat-square">
<img src="https://img.shields.io/github/license/Rafael-MonteiroA/GathaAI?style=flat-square">

---

# 📖 Sobre

O **GathaAI** é um assistente de IA para terminal capaz de:

- 🧠 Lembrar conversas anteriores
- 📚 Aprender fatos sobre o usuário
- 📄 Ler arquivos e documentos
- 📂 Analisar projetos inteiros
- 🌐 Pesquisar na internet
- 🤖 Utilizar modelos locais ou APIs externas
- 📊 Exibir progresso em tempo real

---

# ✨ Funcionalidades

| Recurso | Descrição |
|----------|----------|
| 🧠 Memória Persistente | Armazena histórico usando SQLite |
| 🔍 Memória Vetorial | Busca contexto usando FAISS |
| 📚 Aprendizado de Fatos | Guarda preferências e informações |
| 📄 Leitura de Arquivos | TXT, PDF, PY, C, CPP, JAVA, ZIP |
| 📂 Análise de Projetos | Carrega pastas e projetos inteiros |
| 🌐 Busca Web | Pesquisa automática |
| 🤖 IA Local | Ollama |
| 🔑 IA Externa | OpenAI, Anthropic, Groq e Custom |
| 📊 Barra de Progresso | Feedback visual em tempo real |

---

# 🚀 Instalação

## Navegação

```bash
cd caminho/para/projeto
```

## Clonar repositório

```bash
git clone https://github.com/Rafael-MonteiroA/GathaAI.git
cd GathaAI
```

## Criar ambiente virtual

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux

```bash
source .venv/bin/activate
```

## Instalar dependências

```bash
pip install -r requirements.txt
```

---

# 🤖 Modelo Local

Instale o Ollama:

https://ollama.com

Baixe um modelo:

```bash
ollama pull qwen3:8b
```

---

# ▶️ Executando

## Navegação

```bash
cd GathaAI
```

## Executar

```bash
python chatbot.py
```

---

# 💬 Comandos

## Conversa

| Comando | Função |
|----------|----------|
| /ajuda | Lista comandos |
| /memoria | Histórico recente |
| /limpar | Limpa conversa |
| /apagar_memoria | Apaga tudo |
| /status | Estado atual |
| sair | Fecha o programa |

---

## Arquivos

| Comando | Função |
|----------|----------|
| /arquivo arquivo.py | Carrega arquivo |
| /analisar projeto.zip | Analisa projeto |
| /limpar_arquivo | Remove contexto |

---

## APIs

```bash
/logapi anthropic CHAVE MODELO
/logapi openai CHAVE MODELO
/logapi groq CHAVE MODELO
/logapi custom CHAVE MODELO URL
```

---

# 🔒 Segurança

✅ Chaves de API armazenadas localmente

✅ Arquivos sensíveis ignorados pelo Git

✅ Memórias armazenadas localmente

✅ Compatível com IA local sem envio de dados

---

# 📦 Dependências

- ollama
- requests
- pypdf
- sentence-transformers
- faiss-cpu
- numpy
- ddgs
- colorama

---
<div align="left">

## Created by Rafael Monteiro

⭐ Se gostou do projeto, deixe uma estrela no GitHub.

</div>