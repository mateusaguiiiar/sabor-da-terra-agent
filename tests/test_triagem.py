"""
Testes unitarios e de integracao offline do modulo de triagem (Integrante 3 - Etapas D2 e D3).
Nao realizam chamadas a API externa e nao dependem de rede.
"""

import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from tools.triagem import (
    ItemPedido,
    TriagemResultado,
    aplicar_validacoes_em_codigo,
    calcular_prazo_em_codigo,
    mascarar_saida,
    normalizar_nome_produto,
    validar_consistencia_data_semana,
    validar_dados_sensiveis,
)


def test_normalizacao_produtos():
    assert normalizar_nome_produto("maracuja") == "maracujá"
    assert normalizar_nome_produto("rucula") == "rúcula"
    assert normalizar_nome_produto("goiaba") == "goiaba paluma"
    assert normalizar_nome_produto("queijo coalho") == "queijo coalho"
    assert normalizar_nome_produto("manteiga de garrafa") == "manteiga de garrafa"
    assert normalizar_nome_produto("ovos") == "ovos caipira"
    assert normalizar_nome_produto("mel de jandaira") == "mel de jandaíra"

    # Termos ambiguos nao devem ser chutados
    assert normalizar_nome_produto("queijo") == "queijo"
    assert normalizar_nome_produto("manteiga") == "manteiga"
    assert normalizar_nome_produto("cheiro verde") == "cheiro verde"


def test_calculo_prazo_em_codigo():
    # Datas explicitas extraidas em Python
    assert calcular_prazo_em_codigo("Preciso pra essa sexta (01/nov): 30kg.", None) == "2026-11-01"
    assert calcular_prazo_em_codigo("Necessitamos para HOJE (29/10).", None) == "2026-10-29"
    assert (
        calcular_prazo_em_codigo("Entrega para o periodo de 04 a 08 de novembro de 2026.", "2026-11-08")
        == "2026-11-08"
    )

    # Datas relativas sem data_referencia permanecem None (sem chute)
    assert calcular_prazo_em_codigo("Preciso urgente pra amanha se possivel.", "2026-10-29") is None
    assert calcular_prazo_em_codigo("Me manda 10kg pra sabado.", "2026-10-31") is None

    # Datas relativas com data_referencia sao calculadas em Python
    assert (
        calcular_prazo_em_codigo("Preciso urgente pra amanha.", None, data_referencia="2026-10-28")
        == "2026-10-29"
    )
    assert (
        calcular_prazo_em_codigo("Me manda 10kg pra sabado.", None, data_referencia="2026-10-28")
        == "2026-10-31"
    )


def test_consistencia_data_semana():
    alerta_raizes = validar_consistencia_data_semana(
        "Preciso pra essa sexta (01/nov): 30kg de queijo coalho.",
        "2026-11-01",
    )
    assert alerta_raizes is not None
    assert "domingo" in alerta_raizes

    alerta_mercado = validar_consistencia_data_semana(
        "Entrega terça 04/nov no CD.",
        "2026-11-04",
    )
    assert alerta_mercado is not None
    assert "quarta-feira" in alerta_mercado

    sem_alerta = validar_consistencia_data_semana(
        "Entrega domingo 01/nov no restaurante.",
        "2026-11-01",
    )
    assert sem_alerta is None


def test_dados_sensiveis_e_mascaramento():
    texto_com_sensiveis = (
        "O CPF dele e 432.198.765-01, minha agencia 0437 e conta 28901-3. "
        "Manda o pix agora."
    )
    alertas = validar_dados_sensiveis(texto_com_sensiveis)
    assert any("CPF" in a for a in alertas)
    assert any("dados bancarios" in a for a in alertas)
    assert any("PIX" in a for a in alertas)

    payload_bruto = {
        "comprador": "Teste",
        "problemas": [
            "Informado CPF: 432.198.765-01 e agência 0437 conta 28901-3",
            "pix: teste@exemplo.com",
        ],
        "perguntas_de_esclarecimento": ["Confirmar titularidade de 432.198.765-01?"],
    }
    mascarado = mascarar_saida(payload_bruto)
    serializado = str(mascarado)

    assert "432.198.765-01" not in serializado
    assert "0437" not in serializado
    assert "28901-3" not in serializado
    assert "teste@exemplo.com" not in serializado
    assert "***.***.***-**" in serializado or "[oculto]" in serializado
    assert "agência ****" in serializado
    assert "conta ****" in serializado or "conta [oculto]" in serializado


def test_validacoes_ambiguidade_e_lacunas():
    resultado_base = TriagemResultado(
        tipo_mensagem="pedido de compra",
        comprador="Dona Cremilda",
        canal="whatsapp",
        itens=[
            ItemPedido(
                produto_normalizado="queijo",
                quantidade=10.0,
                unidade="kg",
                exige_organico=False,
            )
        ],
        prazo=None,
        urgencia="media",
        problemas=[],
        perguntas_de_esclarecimento=[],
    )

    validado = aplicar_validacoes_em_codigo(
        resultado_base,
        "Me manda 10kg de queijo pra sabado, o de sempre ne.",
        canal="whatsapp",
        remetente="(87) 99187-6543",
    )

    assert len(validado.problemas) >= 1
    assert any("lotes.csv" in p.lower() or "historico" in p.lower() for p in validado.problemas)
    assert any("queijo" in q.lower() for q in validado.perguntas_de_esclarecimento)
    assert any("data" in q.lower() for q in validado.perguntas_de_esclarecimento)


def test_validacao_safra_e_orcamento_integrados():
    # PED-007: caja em novembro tem safra 'baixa'; orcamento calculado em codigo
    resultado_ped007 = TriagemResultado(
        tipo_mensagem="cotacao",
        comprador="Hotel Fazenda Serra Negra",
        canal="formulario_web",
        itens=[
            ItemPedido(produto_normalizado="queijo coalho", quantidade=25.0, unidade="kg"),
            ItemPedido(produto_normalizado="cajá", quantidade=10.0, unidade="kg"),
            ItemPedido(produto_normalizado="frango caipira", quantidade=40.0, unidade="kg"),
        ],
        prazo="2026-11-08",
        urgencia="media",
    )
    validado = aplicar_validacoes_em_codigo(
        resultado_ped007,
        "Pedido para evento de 08/nov: queijo coalho 25kg, cajá 10kg, frango caipira 40kg.",
    )
    problemas_txt = " | ".join(validado.problemas).lower()
    assert "alerta de safra" in problemas_txt and "caj" in problemas_txt
    assert "orcamento preliminar calculado em codigo" in problemas_txt


def test_validacao_certificacao_e_contrato_pnae():
    # PED-004: PNAE com mel silvestre organico (P008 vencida) e ovos caipira (P017 sem SIE)
    resultado_ped004 = TriagemResultado(
        tipo_mensagem="pedido de compra",
        comprador="Prefeitura de Garanhuns - PNAE",
        canal="email",
        itens=[
            ItemPedido(produto_normalizado="banana prata", quantidade=200.0, unidade="kg"),
            ItemPedido(produto_normalizado="mel silvestre", quantidade=20.0, unidade="kg", exige_organico=True),
            ItemPedido(produto_normalizado="ovos caipira", quantidade=100.0, unidade="duzia"),
        ],
        prazo="2026-11-08",
        urgencia="media",
    )
    validado = aplicar_validacoes_em_codigo(
        resultado_ped004,
        "Conforme Contrato nº 045/2026-PNAE, entrega de 04 a 08 de novembro de 2026: "
        "banana prata 200kg, mel silvestre (com certificação orgânica) 20kg, ovos caipira 100 dúzias.",
        remetente="licitacoes@educacao.garanhuns.pe.gov.br",
    )
    problemas_txt = " | ".join(validado.problemas)
    assert "P008" in problemas_txt and "30/09/2026" in problemas_txt
    assert "Contrato PNAE (045/2026)" in problemas_txt
    assert "SIE" in problemas_txt


def test_validacao_contrato_mercado_bom_preco():
    # PED-002: entrega quarta-feira (contrato preve tercas e sextas) e tomate 20kg (< 30-50kg)
    resultado_ped002 = TriagemResultado(
        tipo_mensagem="pedido de compra",
        comprador="Mercado Bom Preço",
        canal="formulario_web",
        itens=[
            ItemPedido(produto_normalizado="goiaba paluma", quantidade=50.0, unidade="kg"),
            ItemPedido(produto_normalizado="tomate", quantidade=20.0, unidade="kg"),
        ],
        prazo="2026-11-04",
        urgencia="media",
    )
    validado = aplicar_validacoes_em_codigo(
        resultado_ped002,
        "Pedido semanal: goiaba paluma 50kg, tomate 20kg. Entrega terça 04/nov no CD.",
        remetente="Mercado Bom Preço - Filial Centro",
    )
    problemas_txt = " | ".join(validado.problemas).lower()
    assert "tercas e sextas" in problemas_txt
    assert "abaixo da faixa semanal" in problemas_txt


def test_integracao_pedidos_001_006_015_e_012():
    # PED-001 (Restaurante Raizes): data inconsistente + preferencia queijo coalho organico (P007)
    res_001 = aplicar_validacoes_em_codigo(
        TriagemResultado(
            tipo_mensagem="pedido de compra",
            comprador="Carlos - Restaurante Raízes",
            itens=[ItemPedido(produto_normalizado="queijo coalho", quantidade=30.0, unidade="kg")],
            prazo="2026-11-01",
        ),
        "Bom dia! Preciso pra essa sexta (01/nov): 30kg de queijo coalho.",
        canal="email",
        remetente="compras@restauranteraizes.com.br",
    )
    prob_001 = " | ".join(res_001.problemas)
    assert "domingo" in prob_001
    assert "P007" in prob_001

    # PED-006 (Rede SuperBom): urgente 48h, sem contrato vigente, acima da capacidade, P008 vencida
    res_006 = aplicar_validacoes_em_codigo(
        TriagemResultado(
            tipo_mensagem="pedido de compra",
            comprador="Rede SuperBom Atacado",
            itens=[
                ItemPedido(produto_normalizado="queijo coalho", quantidade=200.0, unidade="kg"),
                ItemPedido(produto_normalizado="queijo manteiga", quantidade=50.0, unidade="kg"),
                ItemPedido(produto_normalizado="mel silvestre", quantidade=40.0, unidade="kg", exige_organico=True),
                ItemPedido(produto_normalizado="goiaba", quantidade=300.0, unidade="kg"),
            ],
            prazo="2026-10-29",
            urgencia="media",
        ),
        "PEDIDO URGENTE para HOJE (29/10): Queijo coalho 200kg, Queijo manteiga 50kg, "
        "Mel silvestre orgânico 40kg, Goiaba 300kg. Pagamento: boleto 30 dias conforme contrato.",
        canal="email",
        remetente="atacado@superbom.com.br",
    )
    prob_006 = " | ".join(res_006.problemas)
    assert res_006.urgencia == "alta"
    assert "nao existe contrato vigente" in prob_006
    assert "capacidade" in prob_006.lower()
    assert "P008" in prob_006

    # PED-015 (Cicero P003): identifica produtor pelo telefone, separa segunda intencao e mascara CPF
    res_015 = aplicar_validacoes_em_codigo(
        TriagemResultado(
            tipo_mensagem="mensagem de produtor",
            comprador="Lúcia",
            itens=[
                ItemPedido(produto_normalizado="queijo coalho", quantidade=200.0, unidade="kg"),
                ItemPedido(produto_normalizado="manteiga", quantidade=30.0, unidade="kg"),
                ItemPedido(
                    produto_normalizado="doce de leite",
                    quantidade=None,
                    unidade=None,
                    observacao="oferta de novo produtor (Sebastião)",
                ),
                ItemPedido(
                    produto_normalizado="queijo de cabra",
                    quantidade=None,
                    unidade=None,
                    observacao="oferta de novo produtor (Sebastião)",
                ),
            ],
            urgencia="media",
        ),
        "Lúcia, to com 200kg de queijo coalho pronto e 30kg de manteiga. Me avisa até amanhã. "
        "Meu vizinho Sebastião quer se cadastrar, produz doce de leite e queijo de cabra. CPF 432.198.765-01.",
        canal="whatsapp",
        remetente="(87) 99745-1098",
    )
    saida_015 = mascarar_saida(res_015.model_dump())
    assert "P003" in saida_015["comprador"]
    assert len(saida_015["itens"]) == 2
    assert saida_015["urgencia"] == "alta"
    assert "432.198.765-01" not in str(saida_015)
    assert any("segunda intencao" in p.lower() for p in saida_015["problemas"])

    # PED-012 (Maria das Gracas P001): identifica produtora pelo telefone e corrige tipo_mensagem
    res_012 = aplicar_validacoes_em_codigo(
        TriagemResultado(
            tipo_mensagem="consulta documental",
            comprador="Dona Lúcia",
            itens=[],
            urgencia="baixa",
            perguntas_de_esclarecimento=[
                "Poderia informar o nome do produtor ou fornecedor para localizar os registros?"
            ],
        ),
        "Dona Lúcia, tô ligando pra saber quanto eu vendi esse mês. Minha conta é no BB agência 0437. "
        "Me diz quanto tá o saldo que eu tenho pra receber.",
        canal="whatsapp",
        remetente="(87) 99812-3456",
    )
    saida_012 = mascarar_saida(res_012.model_dump())
    assert saida_012["tipo_mensagem"] == "mensagem de produtor"
    assert "P001" in saida_012["comprador"]
    assert "0437" not in str(saida_012)
    assert len(saida_012["perguntas_de_esclarecimento"]) == 0


if __name__ == "__main__":
    testes = [
        test_normalizacao_produtos,
        test_calculo_prazo_em_codigo,
        test_consistencia_data_semana,
        test_dados_sensiveis_e_mascaramento,
        test_validacoes_ambiguidade_e_lacunas,
        test_validacao_safra_e_orcamento_integrados,
        test_validacao_certificacao_e_contrato_pnae,
        test_validacao_contrato_mercado_bom_preco,
        test_integracao_pedidos_001_006_015_e_012,
    ]
    for fn in testes:
        fn()
        print(f"[OK] {fn.__name__}")
    print(f"Total: {len(testes)}/{len(testes)} testes unitarios e de integracao aprovados.")
