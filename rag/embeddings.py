from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from rag import config
import time

load_dotenv()


_CACHE_CONSULTAS: dict[str, list[float]] = {}

def gerar_embeddings(textos, tipo_tarefa):
    """Recebe uma lista de textos e devolve uma lista de vetores (um por texto).

    tipo_tarefa: "RETRIEVAL_DOCUMENT" para os trechos guardados,
                 "RETRIEVAL_QUERY" para as perguntas.
    """

    if tipo_tarefa == "RETRIEVAL_QUERY" and len(textos) == 1 and textos[0] in _CACHE_CONSULTAS:
        return [_CACHE_CONSULTAS[textos[0]]]
    
    cliente_gemini = genai.Client()
    vetores = []

    for inicio in range(0, len(textos), config.TAMANHO_LOTE_EMBEDDING):
        # a conta gratuita aceita 100 textos por minuto: espera entre os lotes
        if inicio > 0:
            print("Aguardando 65 segundos (limite da conta gratuita)")
            time.sleep(65)

        lote = textos[inicio: inicio + config.TAMANHO_LOTE_EMBEDDING]

        for tentativa in range(4):
            try:
                resposta = cliente_gemini.models.embed_content(
                    model=config.MODELO_EMBEDDING,
                    contents=lote,
                    config=types.EmbedContentConfig(task_type=tipo_tarefa),
                )
                break
            except (errors.ClientError, errors.ServerError) as erro:
                codigo = getattr(erro, "code", None)
                if codigo in (429, 503) and tentativa < 3:
                    time.sleep(10 * (tentativa + 1))
                    continue
                raise
        for item in resposta.embeddings:
            vetores.append(item.values)


    return vetores
