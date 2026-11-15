from rag import config


def listar_arquivos():
    # Devolve uma lista com todos os .txt das pastas de documentos
    lista = []
    for nome_pasta in config.PASTAS_DOCUMENTOS:
        pasta = config.PASTA_DADOS / nome_pasta
        for caminho in sorted(pasta.glob("*.txt")):
            item = {
                "caminho": caminho,
                "pasta": nome_pasta,
                "arquivo": nome_pasta + "/" + caminho.name,
            }
            lista.append(item)
    return lista


def ler_texto(caminho):
    # le o arquivo
    with open(caminho, encoding="utf-8-sig") as arquivo:
        texto = arquivo.read()
    return texto