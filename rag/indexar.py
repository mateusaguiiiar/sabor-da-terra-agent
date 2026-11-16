import chromadb
from rag import config, trechos, embeddings




def indexar():
    # gera os embeddings dos trechos e grava tudo no Chroma, do zero.
    lista = trechos.montar_trechos()

    textos = []
    for trecho in lista:
        textos.append(trecho["texto_para_embedding"])
    vetores = embeddings.gerar_embeddings(textos, "RETRIEVAL_DOCUMENT")

    cliente_chroma = chromadb.PersistentClient(path=str(config.PASTA_CHROMA))

    # apaga a coleção antiga (na primeira vez ela não existe, então ignorar o erro)
    try:
        cliente_chroma.delete_collection(config.NOME_COLECAO)
    except Exception:
        pass

    colecao = cliente_chroma.create_collection(
        name=config.NOME_COLECAO,
        metadata={"hnsw:space": "cosine"},
    )

    ids = []
    documentos = []
    metadados = []
    for trecho in lista:
        ids.append(trecho["id"])
        documentos.append(trecho["texto"])
        metadados.append({
            "arquivo": trecho["arquivo"],
            "tipo_doc": trecho["tipo_doc"],
            "secao": trecho["secao"],
            "produtores": trecho["produtores"],
        })

    colecao.add(ids=ids, documents=documentos, embeddings=vetores, metadatas=metadados)
    return len(lista)