from dotenv import load_dotenv
from google import genai
from google.genai import types
from rag import config
import time

load_dotenv()

def gerar_embeddings(textos, tipo_tarefa):
    """Recebe uma lista de textos e devolve uma lista de vetores (um por texto).

    tipo_tarefa: "RETRIEVAL_DOCUMENT" para os trechos guardados,
                 "RETRIEVAL_QUERY" para as perguntas.
    """
    cliente_gemini = genai.Client()
    vetores = []

    for inicio in range(0, len(textos), config.TAMANHO_LOTE_EMBEDDING):
        # a conta gratuita aceita 100 textos por minuto: espera entre os lotes
        if inicio > 0:
            print("Aguardando 65 segundos (limite da conta gratuita)")
            time.sleep(65)

        lote = textos[inicio: inicio + config.TAMANHO_LOTE_EMBEDDING]
        resposta = cliente_gemini.models.embed_content(
            model=config.MODELO_EMBEDDING,
            contents=lote,
            config=types.EmbedContentConfig(task_type = tipo_tarefa),
        )
        for item in resposta.embeddings:
            vetores.append(item.values)

    return vetores
