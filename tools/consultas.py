"""Funções de consulta sobre os dados da cooperativa (Integrante 4).

Padrão de retorno:
- Sucesso: um dict com os campos do contrato (seção 3 do plano).
- Entrada inválida (produtor, produto ou mês que não existe, produto ambíguo):
  {"erro": "mensagem clara"}. A função nunca inventa uma resposta.

Nenhuma função devolve CPF, telefone, e-mail, endereço ou dados bancários.
"""

import math
from datetime import date

from tools import dados

# Nomes que os compradores usam -> nome usado nas tabelas.
# O "tomate" comum é o santa cruz; o cereja precisa ser pedido pelo nome.
SINONIMOS = {
    "banana": "banana prata",
    "manga": "manga tommy",
    "aipim": "macaxeira",
    "mandioca": "macaxeira",
    "tapioca": "tapioca/goma",
    "goma": "tapioca/goma",
    "mel de abelha jandaira": "mel de jandaira",
    "mel jandaira": "mel de jandaira",
    "jandaira": "mel de jandaira",
    "tomate": "tomate santa cruz",
    "ovos": "ovos caipira",
    "ovo caipira": "ovos caipira",
    "frango": "frango caipira",
    "queijo de coalho": "queijo coalho",
    "mel": "mel silvestre",
}

MESES_NOMES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}

# Regra de safra (critério de aceite do plano): "baixa" também gera alerta,
# porque a sazonalidade marca a goiaba como "baixa" em jun-ago e a observação
# diz "fora de safra".
ALERTAS_SAFRA = {
    "nenhuma": "Produto fora de safra neste mês: não há produção.",
    "baixa": "Baixa disponibilidade neste mês (pode estar fora de safra): confirmar com o produtor antes de aceitar.",
}


def _palavras(texto: str) -> set:
    return set(dados.normalizar(texto).replace("/", " ").split())


def _encontrar_produto(produto: str, nomes: list) -> dict:
    """Acha o nome de produto de uma tabela que corresponde ao que foi pedido.

    Ordem: sinônimo -> nome exato -> todas as palavras de um contidas no outro.
    Devolve {"nome": ...} ou {"erro": ...} (não encontrado ou ambíguo).
    """
    pedido = dados.normalizar(produto)
    if not pedido:
        return {"erro": "Nenhum produto informado."}

    candidatos = [pedido]
    if pedido in SINONIMOS:
        candidatos.insert(0, SINONIMOS[pedido])

    for c in candidatos:
        if c in nomes:
            return {"nome": c}

    for c in candidatos:
        pc = _palavras(c)
        parecidos = [n for n in nomes if pc <= _palavras(n) or _palavras(n) <= pc]
        # Prefere os que começam com a mesma palavra: "goiaba" -> "goiaba paluma",
        # e não "doce de goiaba", que é outro produto.
        primeira = c.replace("/", " ").split()[0]
        mesmo_inicio = [n for n in parecidos if n.replace("/", " ").split()[0] == primeira]
        if mesmo_inicio:
            parecidos = mesmo_inicio
        if len(parecidos) == 1:
            return {"nome": parecidos[0]}
        if len(parecidos) > 1:
            return {"erro": f"Produto '{produto}' é ambíguo. Opções: {', '.join(sorted(parecidos))}."}

    return {"erro": f"Produto '{produto}' não encontrado."}


def _produtor_produz(produtos_lista: list, produto: str) -> bool:
    pedido = _palavras(SINONIMOS.get(dados.normalizar(produto), produto))
    pedido_original = _palavras(produto)
    for item in produtos_lista:
        pi = _palavras(item)
        if pi <= pedido or pedido <= pi or pi <= pedido_original or pedido_original <= pi:
            return True
    return False


def consultar_produtores(produto: str = None, municipio: str = None,
                         organico: bool = None, apenas_ativos: bool = True) -> dict:
    """Lista os produtores da cooperativa, com filtros opcionais.

    Args:
        produto: só produtores que produzem este produto, ex.: 'queijo coalho'.
        municipio: só produtores deste município, ex.: 'Garanhuns'.
        organico: True = só com certificação orgânica válida; False = só sem; None = todos.
        apenas_ativos: se True (padrão), ignora produtores inativos.

    Returns:
        {"produtores": [{"id", "nome", "municipio", "produtos", "organico",
        "certificacao_valida", "validade_certificacao", "status"}, ...]}.
        Nunca inclui CPF, contato ou dados bancários.
    """
    prod = dados.produtores()
    if apenas_ativos:
        prod = prod[prod["ativo"]]
    if municipio:
        prod = prod[prod["municipio_norm"] == dados.normalizar(municipio)]
    if produto:
        prod = prod[prod["produtos_lista"].apply(lambda lista: _produtor_produz(lista, produto))]

    resultado = []
    for _, p in prod.iterrows():
        cert = verificar_certificacao(p["id"])
        if organico is True and not cert["valida"]:
            continue
        if organico is False and cert["valida"]:
            continue
        resultado.append({
            "id": p["id"],
            "nome": p["nome_completo"],
            "municipio": p["municipio"],
            "produtos": p["produtos_lista"],
            "organico": bool(p["organico"]),
            "certificacao_valida": cert["valida"],
            "validade_certificacao": cert["validade"],
            "status": p["status"],
        })
    return {"produtores": resultado}


def _para_data(valor):
    """Aceita date ou texto 'AAAA-MM-DD' (o agente passa datas como texto)."""
    if valor is None or valor == "":
        return dados.DATA_REFERENCIA
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor).strip()[:10])


def verificar_certificacao(produtor_id: str, produto: str = None, data_ref: str = None) -> dict:
    """Verifica se a certificação orgânica de um produtor está válida.

    Args:
        produtor_id: id do produtor, ex.: 'P008'.
        produto: opcional. Se informado, verifica também se o produtor produz esse produto.
        data_ref: data usada como "hoje", no formato 'AAAA-MM-DD'. Padrão: dados.DATA_REFERENCIA.

    Returns:
        {"valida": bool, "validade": "AAAA-MM-DD" ou None, "motivo": str},
        ou {"erro": str} se o produtor não existir ou a data for inválida.
    """
    try:
        data_ref = _para_data(data_ref)
    except ValueError:
        return {"erro": f"Data '{data_ref}' inválida. Use o formato AAAA-MM-DD."}
    prod = dados.produtores()

    linha = prod[prod["id"] == str(produtor_id).strip().upper()]
    if linha.empty:
        return {"erro": f"Produtor {produtor_id} não encontrado."}
    p = linha.iloc[0]
    nome = p["nome_completo"]

    if produto and not _produtor_produz(p["produtos_lista"], produto):
        return {"valida": False, "validade": None,
                "motivo": f"{nome} ({p['id']}) não produz '{produto}'."}

    if not p["organico"]:
        return {"valida": False, "validade": None,
                "motivo": f"{nome} ({p['id']}) não possui certificação orgânica."}

    validade = p["validade_certificacao"].date()
    if validade < data_ref:
        return {"valida": False, "validade": validade.isoformat(),
                "motivo": f"Certificação de {nome} ({p['id']}) VENCIDA em {validade:%d/%m/%Y}."}

    dias = (validade - data_ref).days
    motivo = f"Certificação de {nome} ({p['id']}) válida até {validade:%d/%m/%Y}."
    if dias <= 60:
        motivo += f" Atenção: vence em {dias} dias."
    if not p["ativo"]:
        motivo += " Atenção: produtor inativo na cooperativa."
    return {"valida": True, "validade": validade.isoformat(), "motivo": motivo}


def verificar_sazonalidade(produto: str, mes: str = None) -> dict:
    """Informa a disponibilidade de um produto em um mês, pela tabela de safra.

    Args:
        produto: nome do produto, ex.: 'goiaba paluma' ou 'goiaba'.
        mes: número ('11' ou 11), abreviação ('nov') ou nome ('novembro').
             Padrão: o mês da data de referência.

    Returns:
        {"produto", "mes", "nivel" ('alta', 'media', 'baixa' ou 'nenhuma'),
        "observacao", "alerta" (texto ou None)}, ou {"erro": str}.
        Regra: 'nenhuma' e 'baixa' geram alerta.
    """
    if mes is None:
        mes = dados.DATA_REFERENCIA.month
    if isinstance(mes, float) and mes.is_integer():
        mes = int(mes)
    if isinstance(mes, str):
        m = dados.normalizar(mes)
        if m.isdigit():
            mes = int(m)
        elif m in dados.MESES:
            mes = dados.MESES.index(m) + 1
        elif m in MESES_NOMES:
            mes = MESES_NOMES[m]
        else:
            return {"erro": f"Mês '{mes}' inválido."}
    if not isinstance(mes, int) or not 1 <= mes <= 12:
        return {"erro": f"Mês '{mes}' inválido. Use 1 a 12."}

    saz = dados.sazonalidade()
    achado = _encontrar_produto(produto, list(saz["produto_norm"]))
    if "erro" in achado:
        return achado

    linha = saz[saz["produto_norm"] == achado["nome"]].iloc[0]
    coluna = dados.MESES[mes - 1]
    nivel = linha[coluna]
    return {
        "produto": linha["produto"],
        "mes": coluna,
        "nivel": nivel,
        "observacao": linha["observacao"],
        "alerta": ALERTAS_SAFRA.get(nivel),
    }


def obter_preco(produto: str, organico: bool = False, quantidade_kg: float = 0) -> dict:
    """Calcula o preço de um produto pela tabela de outubro/2026, com desconto de atacado.

    O desconto vale quando a quantidade é maior ou igual ao volume mínimo de atacado.

    Args:
        produto: nome do produto, ex.: 'queijo coalho'.
        organico: True para o preço orgânico.
        quantidade_kg: quantidade pedida, na unidade da tabela (kg, unidade, maço, dúzia ou litro).

    Returns:
        {"produto", "unidade", "organico", "preco_unitario", "desconto_atacado"
        (percentual aplicado, 0 se não houver), "valor_desconto" (em R$), "total", "observacao"}, ou {"erro": str}
        se o produto não existir, for ambíguo ou não tiver preço na versão pedida.
    """
    try:
        quantidade = float(quantidade_kg or 0)
    except (TypeError, ValueError):
        return {"erro": f"Quantidade '{quantidade_kg}' inválida."}
    if quantidade < 0:
        return {"erro": "A quantidade não pode ser negativa."}

    precos = dados.precos()
    achado = _encontrar_produto(produto, list(precos["produto_norm"]))
    if "erro" in achado:
        return achado

    linha = precos[precos["produto_norm"] == achado["nome"]].iloc[0]
    coluna = "preco_organico" if organico else "preco_convencional"
    preco = linha[coluna]
    if preco is None or (isinstance(preco, float) and math.isnan(preco)):
        versao = "orgânica" if organico else "convencional"
        return {"erro": f"{linha['produto']} não está disponível na versão {versao}."}

    minimo = linha["volume_minimo_atacado_kg"]
    pct = linha["desconto_atacado_pct"]
    tem_desconto = (not math.isnan(minimo)) and minimo > 0 and quantidade >= minimo and pct > 0
    desconto = float(pct) if tem_desconto else 0.0

    bruto = round(float(preco) * quantidade, 2)
    total = round(bruto * (1 - desconto / 100), 2)
    return {
        "produto": linha["produto"],
        "unidade": linha["unidade"],
        "organico": organico,
        "preco_unitario": float(preco),
        "quantidade": quantidade,
        "desconto_atacado": desconto,
        "valor_desconto": round(bruto - total, 2),
        "total": total,
        "observacao": linha["observacao"],
    }
