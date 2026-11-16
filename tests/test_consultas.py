from datetime import date

from tools.consultas import (
    consultar_produtores,
    obter_preco,
    verificar_certificacao,
    verificar_sazonalidade,
)


# ---------- verificar_certificacao ----------

def test_p008_vencida():
    # Critério de aceite do plano: P008 venceu em 30/09/2026
    r = verificar_certificacao("P008")
    assert r["valida"] is False
    assert r["validade"] == "2026-09-30"
    assert "VENCIDA" in r["motivo"]


def test_p001_valida():
    r = verificar_certificacao("P001")
    assert r["valida"] is True
    assert r["validade"] == "2027-06-15"


def test_sem_certificacao():
    r = verificar_certificacao("P003")
    assert r["valida"] is False
    assert r["validade"] is None


def test_produto_que_o_produtor_nao_produz():
    r = verificar_certificacao("P002", "queijo coalho")
    assert r["valida"] is False
    assert "não produz" in r["motivo"]


def test_produto_com_nome_diferente_do_cadastro():
    # Cadastro diz "goiaba"; a triagem pode perguntar "goiaba paluma"
    assert verificar_certificacao("P001", "goiaba paluma")["valida"] is True


def test_vencimento_proximo():
    # P004 vence em 01/12/2026: a 32 dias da data de referência
    r = verificar_certificacao("P004")
    assert r["valida"] is True
    assert "vence em 32 dias" in r["motivo"]


def test_data_de_referencia_configuravel():
    assert verificar_certificacao("P004", data_ref=date(2026, 12, 2))["valida"] is False


def test_produtor_inexistente():
    assert "erro" in verificar_certificacao("P099")


# ---------- verificar_sazonalidade ----------

def test_goiaba_baixa_gera_alerta():
    # Critério de aceite: "baixa" gera alerta. No CSV a goiaba é "baixa" em mai-jul
    # (o plano fala em jun-ago, mas agosto está "media" nos dados).
    for mes in [5, 6, 7]:
        r = verificar_sazonalidade("goiaba paluma", mes)
        assert r["nivel"] == "baixa"
        assert r["alerta"] is not None


def test_goiaba_em_novembro_sem_alerta():
    r = verificar_sazonalidade("goiaba", "novembro")
    assert r["nivel"] == "alta"
    assert r["alerta"] is None


def test_manga_nenhuma_em_junho():
    r = verificar_sazonalidade("manga", "jun")
    assert r["nivel"] == "nenhuma"
    assert "fora de safra" in r["alerta"]


def test_morango_em_novembro():
    # PED-008 (Sorveteria): morango em novembro tem nível "media"
    assert verificar_sazonalidade("morango", 11)["nivel"] == "media"


def test_sazonalidade_produto_inexistente_e_mes_invalido():
    assert "erro" in verificar_sazonalidade("abacaxi", 5)
    assert "erro" in verificar_sazonalidade("goiaba", 13)
    assert "erro" in verificar_sazonalidade("goiaba", "marçoo")


# ---------- obter_preco ----------

def test_queijo_coalho_120kg_com_atacado():
    # Critério de aceite: 120 kg x R$ 32,00 com 5% de desconto = R$ 3.648,00
    r = obter_preco("queijo coalho", organico=False, quantidade_kg=120)
    assert r["preco_unitario"] == 32.0
    assert r["desconto_atacado"] == 5.0
    assert r["total"] == 3648.00


def test_abaixo_do_minimo_sem_desconto():
    r = obter_preco("queijo coalho", quantidade_kg=30)
    assert r["desconto_atacado"] == 0.0
    assert r["total"] == 960.00


def test_preco_organico():
    r = obter_preco("mel silvestre", organico=True, quantidade_kg=20)
    # 20 kg x 58,00 = 1160,00, com 8% de atacado (mínimo 20 kg) = 1067,20
    assert r["total"] == 1067.20


def test_organico_que_nao_existe():
    r = obter_preco("banana prata", organico=True, quantidade_kg=10)
    assert "erro" in r
    assert "orgânica" in r["erro"]


def test_produto_ambiguo():
    r = obter_preco("goiaba", quantidade_kg=50)
    assert "erro" in r
    assert "ambíguo" in r["erro"]


def test_produto_inexistente():
    assert "erro" in obter_preco("abacaxi", quantidade_kg=10)


def test_sinonimo_e_acento():
    assert obter_preco("Maracuja", quantidade_kg=1)["preco_unitario"] == 6.0
    assert obter_preco("banana", quantidade_kg=1)["produto"] == "banana prata"


# ---------- consultar_produtores ----------

def test_produtores_de_queijo_coalho():
    ids = {p["id"] for p in consultar_produtores(produto="queijo coalho")["produtores"]}
    assert ids == {"P003", "P007", "P011"}


def test_mel_organico_exclui_certificacao_vencida():
    ids = {p["id"] for p in consultar_produtores(produto="mel silvestre", organico=True)["produtores"]}
    assert ids == {"P002", "P018"}  # P008 tem certificação vencida


def test_inativo_fica_de_fora():
    ids = {p["id"] for p in consultar_produtores(produto="macaxeira")["produtores"]}
    assert "P015" not in ids
    ids_todos = {p["id"] for p in consultar_produtores(produto="macaxeira", apenas_ativos=False)["produtores"]}
    assert "P015" in ids_todos


def test_nao_devolve_dados_sensiveis():
    for p in consultar_produtores()["produtores"]:
        assert not {"cpf", "telefone", "email", "chave_pix", "conta_corrente", "agencia"} & set(p)


# ---------- tipos que o agente envia (texto e número) ----------

def test_data_ref_como_texto():
    assert verificar_certificacao("P004", data_ref="2026-12-02")["valida"] is False
    assert "erro" in verificar_certificacao("P004", data_ref="02/12/2026")


def test_mes_como_texto_numero_e_float():
    assert verificar_sazonalidade("manga", "6")["nivel"] == "nenhuma"
    assert verificar_sazonalidade("manga", 6.0)["nivel"] == "nenhuma"


def test_valor_do_desconto():
    r = obter_preco("queijo coalho", quantidade_kg=120)
    assert r["valor_desconto"] == 192.00  # 3840,00 - 3648,00
