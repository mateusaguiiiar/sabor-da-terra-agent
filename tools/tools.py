from typing import Optional
from rag.busca import buscar, formatar_contexto


def buscar_documentos(
    pergunta: str,
    produtor: Optional[str] = None,
    tipo_doc: Optional[str] = None,
) -> str:
    """
    Busca trechos relevantes nos documentos oficiais da cooperativa Sabor da Terra
    (estatuto, atas, regulamentos, fichas de produtores e certificações).

    Args:
        pergunta: A dúvida ou tema a ser pesquisado nos documentos.
        produtor: Nome ou identificador opcional do produtor para filtrar a busca.
        tipo_doc: Tipo opcional do documento para filtrar (ex: ata, estatuto, certificacao).

    Returns:
        Trechos encontrados com fonte (arquivo e seção) ou mensagem informando ausência.
    """
    trechos = buscar(pergunta=pergunta, produtor=produtor, tipo_doc=tipo_doc)
    return formatar_contexto(trechos)