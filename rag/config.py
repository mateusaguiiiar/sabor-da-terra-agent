from pathlib import Path


PASTA_RAIZ = Path(__file__).resolve().parent.parent


PASTA_DADOS = PASTA_RAIZ / "dados"
PASTA_CHROMA = PASTA_DADOS / "chroma"

# Pastas com os documentos que entram na busca
PASTAS_DOCUMENTOS = ["certificacoes", "contratos", "fichas_tecnicas"]

# Chroma e Gemini
NOME_COLECAO = "sabor_da_terra_docs"
MODELO_EMBEDDING = "gemini-embedding-001"
TAMANHO_LOTE_EMBEDDING = 100

# Busca
TOP_K_PADRAO = 5
CANDIDATOS_BUSCA = 20
MAX_TRECHOS_POR_ARQUIVO = 3 #aumentar 
SIMILARIDADE_MINIMA = 0.70  # provisório: calibrar na Etapa 8