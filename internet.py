def pesquisar(texto):

    try:
        from ddgs import DDGS
    except ImportError:
        return "(busca na internet indisponivel: instale a biblioteca 'ddgs')"

    resultados = []

    try:
        with DDGS() as ddgs:

            busca = ddgs.text(
                texto,
                max_results=5
            )

            for item in busca:
                resultados.append(
                    item["body"]
                )

    except Exception as erro:
        return f"(falha ao pesquisar na internet: {erro})"

    return "\n".join(resultados)
