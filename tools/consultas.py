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

#financeiro 
def _intervalo(periodo):
    """Transforma o período pedido em (inicio, fim, descricao), datas inclusivas.

    Aceita: None ou '' (todo o histórico), 'AAAA-MM' (um mês), 'AAAA' (um ano),
    'AAAA-MM-DD:AAAA-MM-DD' (intervalo), nome ou abreviação de mês com ou sem ano
    ('outubro', 'out/2026', 'setembro de 2026') e 'mes_atual' (mês da data de referência).
    Levanta ValueError se não entender.
    """
    import calendar

    def mes_inteiro(ano, mes):
        ultimo = calendar.monthrange(ano, mes)[1]
        return date(ano, mes, 1), date(ano, mes, ultimo)

    if periodo is None or str(periodo).strip() == "":
        return None, None, "todo o histórico"

    p = dados.normalizar(periodo).replace(" de ", " ").replace("/", " ")
    ref = dados.DATA_REFERENCIA

    if p in ("mes atual", "mes_atual", "esse mes", "este mes"):
        ini, fim = mes_inteiro(ref.year, ref.month)
        return ini, fim, f"{dados.MESES[ref.month - 1]}/{ref.year}"

    if ":" in p:
        a, b = [x.strip() for x in p.split(":", 1)]
        ini, fim = date.fromisoformat(a), date.fromisoformat(b)
        if ini > fim:
            raise ValueError
        return ini, fim, f"{ini:%d/%m/%Y} a {fim:%d/%m/%Y}"

    if len(p) == 7 and p[4] == "-":  # AAAA-MM
        ano, mes = int(p[:4]), int(p[5:])
        ini, fim = mes_inteiro(ano, mes)
        return ini, fim, f"{dados.MESES[mes - 1]}/{ano}"

    if p.isdigit() and len(p) == 4:  # AAAA
        ano = int(p)
        return date(ano, 1, 1), date(ano, 12, 31), str(ano)

    partes = p.split()
    nome_mes = partes[0]
    ano = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else ref.year
    if nome_mes in MESES_NOMES:
        mes = MESES_NOMES[nome_mes]
    elif nome_mes in dados.MESES:
        mes = dados.MESES.index(nome_mes) + 1
    else:
        raise ValueError
    ini, fim = mes_inteiro(ano, mes)
    return ini, fim, f"{dados.MESES[mes - 1]}/{ano}"


def _transacoes_do_produtor(produtor_id: str, periodo):
    """Devolve (produtor, transações filtradas, descricao_periodo) ou {"erro": ...}."""
    pid = str(produtor_id).strip().upper()
    prod = dados.produtores()
    linha = prod[prod["id"] == pid]
    if linha.empty:
        return {"erro": f"Produtor {produtor_id} não encontrado."}

    try:
        ini, fim, descricao = _intervalo(periodo)
    except (ValueError, TypeError):
        return {"erro": f"Período '{periodo}' inválido. Use, por exemplo, '2026-10', 'outubro' "
                        "ou '2026-09-01:2026-10-31'."}

    fin = dados.financeiro()
    fin = fin[fin["produtor_id"] == pid]
    if ini is not None:
        fin = fin[(fin["data"].dt.date >= ini) & (fin["data"].dt.date <= fim)]
    return linha.iloc[0], fin.sort_values("data"), descricao


def _data_ou_none(valor):
    return None if valor is None or str(valor) == "NaT" else valor.date().isoformat()


def vendas_do_produtor(produtor_id: str, periodo: str = None) -> dict:
    """Resume as vendas de um produtor no período, calculadas a partir do financeiro.

    Args:
        produtor_id: id do produtor, ex.: 'P001'. Em perfil de produtor, deve vir da sessão.
        periodo: opcional. 'AAAA-MM' (ex.: '2026-10'), 'outubro', 'out/2026', 'mes_atual',
                 'AAAA' ou 'AAAA-MM-DD:AAAA-MM-DD'. Vazio = todo o histórico (set-out/2026).

    Returns:
        {"produtor_id", "produtor", "periodo", "total_vendido", "total_recebido",
        "total_pendente", "quantidade_vendas", "por_comprador", "por_produto", "vendas"},
        com valores em reais, ou {"erro": str}. Nunca inclui CPF, PIX ou conta.
    """
    r = _transacoes_do_produtor(produtor_id, periodo)
    if isinstance(r, dict):
        return r
    p, fin, descricao = r

    pagos = fin[fin["status_pagamento"] == "pago"]
    pendentes = fin[fin["status_pagamento"] != "pago"]

    por_comprador = (fin.groupby("comprador")["valor_total"].sum().round(2)
                     .sort_values(ascending=False))
    por_produto = (fin.groupby("produto").agg(quantidade=("quantidade_kg", "sum"),
                                              total=("valor_total", "sum"))
                   .sort_values("total", ascending=False))

    return {
        "produtor_id": p["id"],
        "produtor": p["nome_completo"],
        "periodo": descricao,
        "total_vendido": round(float(fin["valor_total"].sum()), 2),
        "total_recebido": round(float(pagos["valor_total"].sum()), 2),
        "total_pendente": round(float(pendentes["valor_total"].sum()), 2),
        "quantidade_vendas": int(len(fin)),
        "por_comprador": [{"comprador": c, "total": float(v)} for c, v in por_comprador.items()],
        "por_produto": [{"produto": prod_, "quantidade": float(l["quantidade"]),
                         "total": round(float(l["total"]), 2)}
                        for prod_, l in por_produto.iterrows()],
        "vendas": [{
            "id_transacao": t["id_transacao"],
            "data": _data_ou_none(t["data"]),
            "comprador": t["comprador"],
            "produto": t["produto"],
            "quantidade": float(t["quantidade_kg"]),
            "valor_total": float(t["valor_total"]),
            "forma_pagamento": t["forma_pagamento"],
            "status_pagamento": t["status_pagamento"],
            "data_vencimento": _data_ou_none(t["data_vencimento"]),
            "data_pagamento": _data_ou_none(t["data_pagamento"]),
        } for _, t in fin.iterrows()],
    }


def saldo_a_receber(produtor_id: str, periodo: str = None) -> dict:
    """Informa quanto um produtor ainda tem a receber (vendas com pagamento pendente).

    Os vencidos são calculados pela data de vencimento comparada à data de referência,
    e não pela observação do financeiro.

    Args:
        produtor_id: id do produtor, ex.: 'P003'. Em perfil de produtor, deve vir da sessão.
        periodo: opcional, filtra pela data da venda (mesmos formatos de vendas_do_produtor).
                 Vazio = todas as pendências.

    Returns:
        {"produtor_id", "produtor", "periodo", "data_referencia", "total_a_receber",
        "total_vencido", "total_a_vencer", "pendencias": [{"id_transacao", "comprador",
        "produto", "valor", "data_venda", "vencimento", "situacao", "dias", "observacao"}]},
        ou {"erro": str}. Nunca inclui CPF, PIX ou conta.
    """
    r = _transacoes_do_produtor(produtor_id, periodo)
    if isinstance(r, dict):
        return r
    p, fin, descricao = r
    ref = dados.DATA_REFERENCIA

    pendencias = []
    total_vencido = total_a_vencer = 0.0
    for _, t in fin[fin["status_pagamento"] != "pago"].sort_values("data_vencimento").iterrows():
        valor = float(t["valor_total"])
        venc = t["data_vencimento"].date()
        dias = (venc - ref).days
        if dias < 0:
            situacao, total_vencido = "vencido", total_vencido + valor
        else:
            situacao, total_a_vencer = "a vencer", total_a_vencer + valor
        pendencias.append({
            "id_transacao": t["id_transacao"],
            "comprador": t["comprador"],
            "produto": t["produto"],
            "valor": valor,
            "data_venda": _data_ou_none(t["data"]),
            "vencimento": venc.isoformat(),
            "situacao": situacao,
            "dias": abs(dias),  # dias de atraso (vencido) ou até vencer (a vencer)
            "observacao": t["observacao"],
        })

    return {
        "produtor_id": p["id"],
        "produtor": p["nome_completo"],
        "periodo": descricao,
        "data_referencia": ref.isoformat(),
        "total_a_receber": round(total_vencido + total_a_vencer, 2),
        "total_vencido": round(total_vencido, 2),
        "total_a_vencer": round(total_a_vencer, 2),
        "pendencias": pendencias,
    }


def rastrear_lote(lote_id: str) -> dict:
    """Mostra a rastreabilidade de um lote entregue: produtor, produto, datas e comprador.

    Args:
        lote_id: código do lote, ex.: 'LOT-2026-0089' (aceita também só o número, '0089' ou '89').

    Returns:
        {"lote_id", "produtor_id", "produtor", "produto", "quantidade", "comprador",
        "pedido_id", "data_colheita", "data_entrega", "validade", "temperatura_transporte",
        "inspecao_visual", "observacao"}, ou {"erro": str}. Não inclui o CPF do produtor.
    """
    texto = str(lote_id or "").strip().upper()
    if not texto:
        return {"erro": "Nenhum lote informado."}
    if texto.isdigit():
        texto = f"LOT-{dados.DATA_REFERENCIA.year}-{int(texto):04d}"

    lotes = dados.lotes()
    linha = lotes[lotes["lote_id"] == texto]
    if linha.empty:
        return {"erro": f"Lote {lote_id} não encontrado."}
    l = linha.iloc[0]

    temp = l["temperatura_transporte_c"]
    temperatura = "ambiente" if dados.normalizar(temp) == "ambiente" else f"{temp} °C"

    return {
        "lote_id": l["lote_id"],
        "produtor_id": l["produtor_id"],
        "produtor": l["produtor_nome"],
        "produto": l["produto"],
        "quantidade": float(l["quantidade_kg"]),
        "comprador": l["comprador"],
        "pedido_id": l["pedido_id"],
        "data_colheita": _data_ou_none(l["data_colheita"]),
        "data_entrega": _data_ou_none(l["data_entrega"]),
        "validade": _data_ou_none(l["validade"]),
        "temperatura_transporte": temperatura,
        "inspecao_visual": l["inspecao_visual"],
        "observacao": l["observacao"],
    }
