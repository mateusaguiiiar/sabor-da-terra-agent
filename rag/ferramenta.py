from rag import busca

NAO_ENCONTRADO = "Não encontrei essa informação nos documentos da cooperativa."


def juntar_fontes(trechos):
    # uma fonte por (documento, seção), sem repetir, da mais parecida para a menos
    melhores = {}
    for trecho in trechos:
        chave = (trecho["arquivo"], trecho["secao"])
        if chave not in melhores or trecho["similaridade"] > melhores[chave]["similaridade"]:
            melhores[chave] = {
                "arquivo": trecho["arquivo"],
                "secao": trecho["secao"],
                "similaridade": trecho["similaridade"],
            }
    return sorted(melhores.values(), key=lambda f: f["similaridade"], reverse=True)


def buscar_documentos(pergunta: str, produtor: str = "", tipo_doc: str = "") -> dict:
    """Busca trechos relevantes nos documentos da cooperativa (certificações orgânicas,
    laudos sanitários, inspeção ADAGRO, contratos e fichas técnicas) e devolve os
    trechos encontrados junto com as fontes (arquivo e seção).

    Use para perguntas sobre certificação, laudos, cláusulas de contrato, prazos de
    pagamento e entrega, preços de fichas e contratos, registros SIE.
    Não use para saldos, vendas, lotes ou sazonalidade: isso vem das tabelas.

    Devolve um dicionário com:
      status: "sucesso", "sem_resultado" ou "erro".
      resposta: trechos dos documentos encontrados (ou mensagem de erro/vazio).
      fontes: lista de {arquivo, secao, similaridade}; mostre-as ao usuário.

    Args:
        pergunta: a pergunta do usuário em português, com as palavras-chave importantes.
        produtor: opcional. Código do produtor, como P008. Deixe vazio se não souber o código.
        tipo_doc: opcional. certificacoes, contratos ou fichas_tecnicas. Vazio para buscar em todos.
    """
    try:
        trechos = busca.buscar(pergunta, produtor=produtor or None, tipo_doc=tipo_doc or None)
    except (ValueError, RuntimeError) as erro:
        return {"status": "erro", "resposta": str(erro), "fontes": []}
    except Exception as erro:
        return {"status": "erro", "resposta": f"Falha temporária na consulta aos documentos: {erro}", "fontes": []}

    # Sem trecho relevante: nem chama o Gemini (evita inventar e poupa a cota)
    if not trechos:
        return {"status": "sem_resultado", "resposta": NAO_ENCONTRADO, "fontes": []}

    return {
        "status": "sucesso",
        "resposta": busca.formatar_contexto(trechos),
        "fontes": juntar_fontes(trechos),
    }