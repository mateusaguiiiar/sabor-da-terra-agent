import chromadb

cliente = chromadb.PersistentClient(path="textoMentira")
colecao = cliente.get_or_create_collection(
    name="teste", metadata={"hnsw:space": "cosine"}
)

colecao.add(
    ids=["a", "b", "c"],
    documents=["texto sobre mel", "texto sobre queijo", "texto sobre goiaba"],
    embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    metadatas=[{"arquivo": "mel.txt"}, {"arquivo": "queijo.txt"}, {"arquivo": "goiaba.txt"}],
)

resultado = colecao.query(query_embeddings=[[0.9, 0.1, 0.0]], n_results=1)
print(resultado["documents"])
print(resultado["metadatas"])
print(resultado["distances"])