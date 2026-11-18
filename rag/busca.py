import chromadb

from rag import config, embeddings
from rag.funcao_mascara import mascarar_texto

def buscar(pergunta, top_k = config.TOP_K_PADRAO, produtor = None, tipo_doc = None):

    produtor_norm = produtor.strip().upper() if produtor else None  

    vetor_pergunta = embeddings.gerar_embeddings([pergunta], "RETRIEVAL_QUERY")[0]

    cliente_chroma = chromadb.PersistentClient(path=str(config.PASTA_CHROMA))

    try:
        colecao = cliente_chroma.get_collection(name=config.NOME_COLECAO)
    except Exception:
        raise RuntimeError("Índice não encontrado. Rode python INICIARBANCO.py antes de buscar.")

    total = colecao.count()
    
    if total == 0:
        return []

    resultado = colecao.query(
        query_embeddings=[vetor_pergunta],
        n_results=total if produtor_norm else min(config.CANDIDATOS_BUSCA, total),  
        where={"tipo_doc": tipo_doc} if tipo_doc else None,
        include=["documents", "metadatas", "distances"],
    )

    ids = resultado["ids"][0]
    documentos = resultado["documents"][0]
    metadados = resultado["metadatas"][0]
    distancias = resultado["distances"][0]

    trechos_encontrados = []
    contagem_por_arquivo = {}

    for i in range(len(ids)):
        similaridade = 1 - distancias[i]
        if similaridade < config.SIMILARIDADE_MINIMA:
            continue

        if produtor_norm:
            codigos = metadados[i]["produtores"]
            if codigos != "" and produtor_norm not in codigos.split(","):
                continue

        arquivo = metadados[i]["arquivo"]
        if contagem_por_arquivo.get(arquivo, 0) >= config.MAX_TRECHOS_POR_ARQUIVO:
            continue

        trechos_encontrados.append({
            "arquivo": arquivo,
            "tipo_doc": metadados[i]["tipo_doc"],
            "secao": metadados[i]["secao"],
            "produtores": metadados[i]["produtores"],
            "texto": mascarar_texto(documentos[i]),
            "similaridade": round(similaridade, 4),
        })
        contagem_por_arquivo[arquivo] = contagem_por_arquivo.get(arquivo, 0) + 1

        if len(trechos_encontrados) >= top_k:
            break
        
    return trechos_encontrados


def formatar_contexto(trechos):
    if not trechos:
        return "Nenhuma informação relevante foi encontrada nos documentos da cooperativa."

    blocos = []
    for item in trechos:
        fonte = f"Fonte: {item['arquivo']} | Seção: {item['secao']}"
        if item["produtores"]:
            fonte += f" | Produtores: {item['produtores']}"
        blocos.append(f"[{fonte}]\n{item['texto']}")

    return "\n\n---\n\n".join(blocos)


