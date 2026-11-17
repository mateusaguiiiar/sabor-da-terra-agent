from tools import dados


def test_normalizar():
    assert dados.normalizar("  Maracujá ") == "maracuja"
    assert dados.normalizar("RÚCULA") == "rucula"
    assert dados.normalizar(None) == ""


def test_carrega_os_cinco_csvs():
    assert len(dados.produtores()) == 18
    assert len(dados.financeiro()) == 30
    assert len(dados.lotes()) == 20
    assert len(dados.sazonalidade()) == 50
    assert len(dados.precos()) == 53


def test_produtores_tipos():
    prod = dados.produtores().set_index("id")
    assert prod.loc["P008", "organico"]
    assert str(prod.loc["P008", "validade_certificacao"].date()) == "2026-09-30"
    assert not prod.loc["P015", "ativo"]
    assert "goiaba" in prod.loc["P001", "produtos_lista"]


def test_precos_nd_vira_vazio():
    p = dados.precos().set_index("produto_norm")
    assert p.loc["banana prata", "preco_organico"] != p.loc["banana prata", "preco_organico"]  # NaN
    assert p.loc["queijo coalho", "preco_convencional"] == 32.0


def test_copias_nao_alteram_o_cache():
    df = dados.produtores()
    df.loc[0, "nome_completo"] = "ALTERADO"
    assert dados.produtores().loc[0, "nome_completo"] != "ALTERADO"


def test_sem_sensiveis():
    limpo = dados.sem_sensiveis(dados.produtores())
    for col in ["cpf", "chave_pix", "agencia", "conta_corrente", "telefone", "email"]:
        assert col not in limpo.columns
    assert "nome_completo" in limpo.columns
