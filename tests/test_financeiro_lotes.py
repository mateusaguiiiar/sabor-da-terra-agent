"""Testes de vendas, saldo e lotes.

Gabarito calculado à mão a partir do financeiro.csv (data de referência 30/10/2026):
  P001: 540 + 400 + 150 = 1090,00 vendidos, tudo pago, tudo em setembro.
  P003: 1440 + 4500 + 1520 = 7460,00 vendidos; 4500 + 1520 = 6020,00 pendentes,
        vencidos em 18/10 (12 dias de atraso).
  P004: 750 + 270 = 1020,00 vendidos, tudo pendente, vencido em 23/10 (7 dias).
  P007: 675 + 2480 = 3155,00 vendidos; 2480,00 a vencer em 09/12 (40 dias).
"""

from tools.consultas import rastrear_lote, saldo_a_receber, vendas_do_produtor
from tools.mascarar import mascarar

SENSIVEIS = {"cpf", "produtor_cpf", "chave_pix", "chave_pix_deposito", "conta_corrente", "agencia"}



def test_vendas_p001_soma_manual():
    r = vendas_do_produtor("P001")
    assert r["total_vendido"] == 1090.00
    assert r["total_recebido"] == 1090.00
    assert r["total_pendente"] == 0.00
    assert r["quantidade_vendas"] == 3


def test_vendas_p003_soma_manual():
    r = vendas_do_produtor("P003")
    assert r["total_vendido"] == 7460.00
    assert r["total_recebido"] == 1440.00
    assert r["total_pendente"] == 6020.00


def test_vendas_p007_soma_manual():
    r = vendas_do_produtor("P007")
    assert r["total_vendido"] == 3155.00
    assert r["total_pendente"] == 2480.00


def test_vendas_por_periodo_ped012():
    outubro = vendas_do_produtor("P001", "mes_atual")
    assert outubro["periodo"] == "out/2026"
    assert outubro["total_vendido"] == 0.00
    assert outubro["vendas"] == []
    assert vendas_do_produtor("P001", "2026-09")["total_vendido"] == 1090.00
    assert vendas_do_produtor("P001", "setembro")["total_vendido"] == 1090.00


def test_pagamento_bom_preco_setembro_ped012():
    vendas = vendas_do_produtor("P001", "2026-09")["vendas"]
    bom_preco = [v for v in vendas if v["comprador"] == "Mercado Bom Preço"]
    assert len(bom_preco) == 2
    assert all(v["status_pagamento"] == "pago" and v["data_pagamento"] == "2026-10-01" for v in bom_preco)


def test_vendas_por_comprador_e_produto():
    r = vendas_do_produtor("P003")
    compradores = {c["comprador"]: c["total"] for c in r["por_comprador"]}
    assert compradores == {"Rede SuperBom Atacado": 6020.00, "Restaurante Raízes": 1440.00}
    produtos = {p["produto"]: p["quantidade"] for p in r["por_produto"]}
    assert produtos["queijo coalho"] == 195  # 45 + 150 kg


def test_vendas_intervalo_e_erros():
    assert vendas_do_produtor("P007", "2026-10-01:2026-10-31")["total_vendido"] == 2480.00
    assert "erro" in vendas_do_produtor("P099")
    assert "erro" in vendas_do_produtor("P001", "mês que vem")
    assert "erro" in vendas_do_produtor("P001", "2026-10-31:2026-10-01")


def test_saldo_p003_vencido():
    r = saldo_a_receber("P003")
    assert r["total_a_receber"] == 6020.00
    assert r["total_vencido"] == 6020.00
    assert r["total_a_vencer"] == 0.00
    assert all(p["situacao"] == "vencido" and p["dias"] == 12 for p in r["pendencias"])


def test_saldo_p004_vencido_sem_observacao():
    r = saldo_a_receber("P004")
    assert r["total_vencido"] == 1020.00
    assert r["pendencias"][0]["dias"] == 7


def test_saldo_p007_a_vencer():
    r = saldo_a_receber("P007")
    assert r["total_a_receber"] == 2480.00
    assert r["total_a_vencer"] == 2480.00
    assert r["pendencias"][0]["dias"] == 40


def test_saldo_p001_zerado():
    r = saldo_a_receber("P001")
    assert r["total_a_receber"] == 0.00
    assert r["pendencias"] == []


def test_saldo_produtor_inexistente():
    assert "erro" in saldo_a_receber("P099")


def test_lote_0089_criterio_de_aceite():
    r = rastrear_lote("LOT-2026-0089")
    assert r["produtor_id"] == "P003"
    assert r["produtor"] == "Cícero Romão de Almeida"
    assert r["produto"] == "queijo coalho"
    assert r["quantidade"] == 45
    assert r["comprador"] == "Restaurante Raízes"
    assert r["validade"] == "2026-10-02"


def test_lote_formatos_e_temperatura():
    assert rastrear_lote("lot-2026-0089")["lote_id"] == "LOT-2026-0089"
    assert rastrear_lote("89")["lote_id"] == "LOT-2026-0089"
    assert rastrear_lote("89")["temperatura_transporte"] == "8 °C"
    assert rastrear_lote("90")["temperatura_transporte"] == "ambiente"


def test_lote_inexistente():
    assert "erro" in rastrear_lote("LOT-2026-9999")
    assert "erro" in rastrear_lote("")


def _tem_chave_sensivel(obj):
    if isinstance(obj, dict):
        return bool(SENSIVEIS & set(obj)) or any(_tem_chave_sensivel(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_tem_chave_sensivel(v) for v in obj)
    return False


def test_nenhum_dado_sensivel_nos_retornos():
    for pid in [f"P{i:03d}" for i in range(1, 19)]:
        for r in (vendas_do_produtor(pid), saldo_a_receber(pid)):
            assert not _tem_chave_sensivel(r)
            assert mascarar(str(r)) == str(r)  # nada para mascarar = nada sensível no texto
    r = rastrear_lote("89")
    assert not _tem_chave_sensivel(r)
    assert mascarar(str(r)) == str(r)
