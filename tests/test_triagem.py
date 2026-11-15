"""
Testes unitarios offline do modulo de triagem (Integrante 3).
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
    assert "***.***.***-**" in serializado
    assert "agência ****" in serializado
    assert "conta ****" in serializado


def test_validacoes_ambiguidade_e_lacunas():
    resultado_base = TriagemResultado(
        tipo_mensagem="pedido de compra",
        comprador="Cliente Teste",
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
    )

    assert len(validado.problemas) >= 1
    assert any("historico" in p.lower() for p in validado.problemas)
    assert any("queijo" in q.lower() for q in validado.perguntas_de_esclarecimento)
    assert any("data" in q.lower() for q in validado.perguntas_de_esclarecimento)
    assert len(validado.perguntas_de_esclarecimento) == len(set(validado.perguntas_de_esclarecimento))


def test_urgencia_por_regra():
    resultado_base = TriagemResultado(
        tipo_mensagem="pedido de compra",
        comprador="Mercado",
        itens=[],
        urgencia="media",
    )
    validado = aplicar_validacoes_em_codigo(
        resultado_base,
        "PEDIDO URGENTE para entrega hoje.",
    )
    assert validado.urgencia == "alta"
    assert validado.justificativa_urgencia is not None


if __name__ == "__main__":
    testes = [
        test_normalizacao_produtos,
        test_consistencia_data_semana,
        test_dados_sensiveis_e_mascaramento,
        test_validacoes_ambiguidade_e_lacunas,
        test_urgencia_por_regra,
    ]
    for fn in testes:
        fn()
        print(f"[OK] {fn.__name__}")
    print(f"Total: {len(testes)}/{len(testes)} testes unitarios aprovados.")
