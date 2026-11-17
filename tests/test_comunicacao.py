"""Testes de resumos e notificações.

Os testes NÃO chamam o Gemini de verdade (não gastam cota e rodam sem internet):
o Gemini é "falsificado" com o monkeypatch do pytest.
"""

import pytest

from tools import comunicacao
from tools.comunicacao import brl, gerar_notificacao_novo_pedido, gerar_resumo_produtor

PEDIDO_015 = {  # formato de exemplo de um pedido estruturado pela triagem
    "id": "PED-2026-001",
    "comprador": "Restaurante Raízes",
    "data_entrega": "2026-11-01",
    "itens": [
        {"produto": "queijo coalho", "quantidade": 30, "unidade": "kg"},
        {"produto": "manteiga de garrafa", "quantidade": 10, "unidade": "kg"},
        {"produto": "mel silvestre", "quantidade": 5, "unidade": "kg"},
        {"produto": "ricota", "quantidade": 5, "unidade": "kg"},
    ],
}


@pytest.fixture
def sem_gemini(monkeypatch):
    monkeypatch.setenv("SABOR_SEM_LLM", "1")


@pytest.fixture
def gemini_falso(monkeypatch):
    """Liga um Gemini de mentira. O teste define o que ele responde."""
    monkeypatch.delenv("SABOR_SEM_LLM", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    comunicacao._chamar_gemini.cache_clear()
    respostas = {}

    def falso(prompt):
        r = respostas["texto"]
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(comunicacao, "_chamar_gemini", falso)
    monkeypatch.setattr(comunicacao.time, "sleep", lambda s: None)  # não esperar nos testes
    return respostas


def test_brl():
    assert brl(1090) == "R$ 1.090,00"
    assert brl(6020.5) == "R$ 6.020,50"
    assert brl(0) == "R$ 0,00"


# ---------- resumo ----------

def test_resumo_sem_gemini_usa_numeros_certos(sem_gemini):
    r = gerar_resumo_produtor("P003")
    assert r["origem"] == "texto_padrao"
    assert "Cícero" in r["texto"]
    assert "R$ 7.460,00" in r["texto"]       # vendido
    assert "R$ 6.020,00" in r["texto"]       # a receber, tudo vencido
    assert r["dados"]["entregas"] == 3        # lotes 0089, 0100 e 0101


def test_resumo_maria_outubro(sem_gemini):
    # PED-012: em outubro a Maria não vendeu nada e não tem nada a receber
    r = gerar_resumo_produtor("P001", "mes_atual")
    assert r["dados"]["total_vendido"] == 0
    assert r["dados"]["total_a_receber"] == 0
    assert "não tem valores pendentes" in r["texto"]


def test_resumo_nunca_tem_dados_sensiveis(sem_gemini):
    prod = comunicacao.dados.produtores()
    for _, p in prod[prod["ativo"]].iterrows():
        texto = gerar_resumo_produtor(p["id"])["texto"]
        for sensivel in (p["cpf"], p["chave_pix"], p["conta_corrente"]):
            assert sensivel not in texto


def test_resumo_usa_texto_do_gemini(gemini_falso):
    gemini_falso["texto"] = "Oi, Cícero! Você vendeu R$ 7.460,00 e tem R$ 6.020,00 vencidos."
    r = gerar_resumo_produtor("P003")
    assert r["origem"] == "gemini"
    assert r["texto"] == gemini_falso["texto"]


def test_resumo_rejeita_valor_inventado(gemini_falso):
    gemini_falso["texto"] = "Oi, Cícero! Você vendeu R$ 9.999,00 este mês!"
    r = gerar_resumo_produtor("P003")
    assert r["origem"] == "texto_padrao"
    assert "9.999" not in r["texto"]


def test_resumo_mascara_dado_sensivel_do_gemini(gemini_falso):
    gemini_falso["texto"] = "Oi, Cícero! Seu PIX 723.016.498-55 recebe R$ 6.020,00."
    r = gerar_resumo_produtor("P003")
    assert "723.016.498-55" not in r["texto"]


def test_resumo_gemini_com_erro_429(gemini_falso):
    gemini_falso["texto"] = Exception("429 RESOURCE_EXHAUSTED")
    r = gerar_resumo_produtor("P003")
    assert r["origem"] == "texto_padrao"
    assert "R$ 6.020,00" in r["texto"]


def test_resumo_erros(sem_gemini):
    assert "erro" in gerar_resumo_produtor("P099")
    assert "erro" in gerar_resumo_produtor("P001", "mês que vem")


# ---------- notificação ----------

def test_notificacao_so_itens_do_produtor(sem_gemini):
    # Cícero (P003) produz queijo coalho e ricota; não produz manteiga de garrafa nem mel
    r = gerar_notificacao_novo_pedido("P003", PEDIDO_015)
    produtos = {i["produto"] for i in r["itens"]}
    assert produtos == {"queijo coalho", "ricota"}
    assert "Restaurante Raízes" in r["texto"]
    assert "01/11/2026" in r["texto"]
    assert "mel" not in r["texto"]


def test_notificacao_sem_precos(sem_gemini):
    r = gerar_notificacao_novo_pedido("P007", PEDIDO_015)
    assert "R$" not in r["texto"]


def test_notificacao_gemini_com_preco_e_descartada(gemini_falso):
    gemini_falso["texto"] = "Oi! Pedido de 30 kg de queijo coalho a R$ 32,00 o kg."
    r = gerar_notificacao_novo_pedido("P003", PEDIDO_015)
    assert r["origem"] == "texto_padrao"
    assert "R$" not in r["texto"]


def test_notificacao_alerta_certificacao_vencida(sem_gemini):
    pedido = {"comprador": "Prefeitura de Garanhuns - PNAE", "prazo": "04/11 a 08/11",
              "itens": [{"produto": "mel silvestre", "quantidade": 20, "unidade": "kg",
                         "exige_organico": True}]}
    r = gerar_notificacao_novo_pedido("P008", pedido)  # Josefa: certificação vencida
    assert r["alertas"]
    assert "certificação" in r["texto"]


def test_notificacao_aceita_json_em_texto(sem_gemini):
    import json
    r = gerar_notificacao_novo_pedido("P003", json.dumps(PEDIDO_015))
    assert "erro" not in r


def test_notificacao_erros(sem_gemini):
    assert "erro" in gerar_notificacao_novo_pedido("P099", PEDIDO_015)
    assert "erro" in gerar_notificacao_novo_pedido("P015", PEDIDO_015)  # inativo
    assert "erro" in gerar_notificacao_novo_pedido("P014", PEDIDO_015)  # morango: nada do pedido
    assert "erro" in gerar_notificacao_novo_pedido("P003", "isto não é json")


def test_resumo_aceita_formato_diferente_mas_rejeita_valor_errado(gemini_falso):
    gemini_falso["texto"] = "Oi, Cícero! Vendas de R$7460,00 e R$ 6020 a receber."
    assert gerar_resumo_produtor("P003")["origem"] == "gemini"      # mesmo valor, outro formato
    gemini_falso["texto"] = "Oi, Cícero! Vendas de R$ 9999,00."
    assert gerar_resumo_produtor("P003")["origem"] == "texto_padrao"  # valor inventado
