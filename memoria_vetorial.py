import os
import pickle

import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DIM = 384

INDEX_FILE = os.path.join(BASE_DIR, "vetores", "memoria.index")
TEXT_FILE = os.path.join(BASE_DIR, "vetores", "textos.pkl")

os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)

# O modelo de embeddings e o FAISS sao carregados sob demanda (lazy load),
# assim a GathaAI inicia rapido mesmo se a memoria vetorial nao for usada
# logo de cara, e o programa nao quebra caso essas libs nao estejam instaladas.
_modelo = None
_index = None
_faiss = None
textos = []
_carregado = False


def _garantir_carregado():
    global _modelo, _index, _faiss, textos, _carregado

    if _carregado:
        return

    import faiss
    from sentence_transformers import SentenceTransformer

    _faiss = faiss
    _modelo = SentenceTransformer("all-MiniLM-L6-v2")

    try:
        if os.path.exists(INDEX_FILE):
            _index = faiss.read_index(INDEX_FILE)
        else:
            raise FileNotFoundError()
    except Exception:
        _index = faiss.IndexFlatL2(DIM)

    try:
        if os.path.exists(TEXT_FILE):
            with open(TEXT_FILE, "rb") as f:
                textos = pickle.load(f)
        else:
            raise FileNotFoundError()
    except Exception:
        textos = []

    _carregado = True


def salvar_memoria(texto):

    _garantir_carregado()

    vetor = _modelo.encode([texto])
    vetor = np.array(vetor, dtype=np.float32)

    _index.add(vetor)
    textos.append(texto)

    _faiss.write_index(_index, INDEX_FILE)

    with open(TEXT_FILE, "wb") as f:
        pickle.dump(textos, f)


def buscar_memoria(pergunta, k=5):

    _garantir_carregado()

    if len(textos) == 0:
        return []

    vetor = _modelo.encode([pergunta])
    vetor = np.array(vetor, dtype=np.float32)

    distancias, indices = _index.search(vetor, min(k, len(textos)))

    resultado = []

    for idx in indices[0]:
        if 0 <= idx < len(textos):
            resultado.append(textos[idx])

    return resultado


def apagar_memoria_vetorial():

    global _index, textos

    _garantir_carregado()

    _index = _faiss.IndexFlatL2(DIM)
    textos = []

    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)

    if os.path.exists(TEXT_FILE):
        os.remove(TEXT_FILE)

    return True
