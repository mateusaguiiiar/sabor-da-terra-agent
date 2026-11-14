from dotenv import load_dotenv
from google import genai
from google.genai import types
import ragTeste

load_dotenv()
cliente = genai.Client()

resposta = cliente.models.embed_content(
    model="gemini-embedding-001",
    contents= frases,
    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
)
vetor = resposta.embeddings[0].values
print(len(vetor))
print(vetor[0:5])