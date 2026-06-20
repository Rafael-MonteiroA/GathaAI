import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = os.path.join(BASE_DIR, "dados", "fatos.json")

os.makedirs(os.path.dirname(ARQUIVO), exist_ok=True)

if not os.path.exists(ARQUIVO):

    with open(
        ARQUIVO,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump([], f)


def carregar():

    with open(
        ARQUIVO,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def salvar(fato):

    fatos = carregar()

    fatos.append(fato)

    with open(
        ARQUIVO,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            fatos,
            f,
            ensure_ascii=False,
            indent=4
        )


def listar():

    return carregar()


def apagar():

    with open(
        ARQUIVO,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump([], f)
