frases = ["o certificado da Josefa venceu em 30/09/2026", "o queijo coalho deve ser guardado entre 2°C e 8°C", "o PNAE paga em até 45 dias."]



from dotenv import load_dotenv
from google import genai
from google.genai import types
import chromadb

load_dotenv()
cliente = genai.Client()

resposta = cliente.models.embed_content(
    model="gemini-embedding-001",
    contents= frases,
    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
)


vetor_frases = []

for item in resposta.embeddings:
    vetor_frases.append(item.values)

CLIENTES = chromadb.PersistentClient(path="teste_chroma")
colecao = CLIENTES.get_or_create_collection(
    name="teste", metadata={"hnsw:space": "cosine"}
)

colecao.add(
    ids=["a", "b", "c"],
    documents= frases,
    embeddings= vetor_frases,
    metadatas=[{"arquivo": "josefa.txt"}, {"arquivo": "queijo.txt"}, {"arquivo": "PNAE.txt"}],
)


pergunta = "A certificação da Josefa está vencida?"
resposta_pergunta = cliente.models.embed_content(
    model="gemini-embedding-001",
    contents=[pergunta],
    config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
)


vetor_pergunta = resposta_pergunta.embeddings[0].values

# 4) Consultar e imprimir
resultado = colecao.query(query_embeddings=[vetor_pergunta], n_results=3)

total = len(resultado["documents"][0])
for posicao in range(total):
    texto = resultado["documents"][0][posicao]
    arquivo = resultado["metadatas"][0][posicao]["arquivo"]
    distancia = resultado["distances"][0][posicao]
    similaridade = 1 - distancia
    print(posicao + 1, arquivo, round(similaridade, 3), texto)