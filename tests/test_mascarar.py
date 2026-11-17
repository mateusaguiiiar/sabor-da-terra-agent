import json

from tools import dados
from tools.mascarar import mascarar, mascarar_dados


def test_cpf_formatado_e_sem_pontuacao():
    assert "123.456.789-09" not in mascarar("CPF: 123.456.789-09")
    assert "12345678909" not in mascarar("cpf 12345678909")


def test_cpf_de_pessoa_fora_do_cadastro():
    # PED-015: CPF do vizinho do Cícero
    texto = "O CPF dele é 432.198.765-01, mora aqui no Sítio Vizinho"
    resultado = mascarar(texto)
    assert "432.198.765-01" not in resultado
    assert "Sítio Vizinho" in resultado


def test_agencia_e_conta():
    resultado = mascarar("Minha conta é no BB agência 0437, conta corrente 28901-3")
    assert "0437" not in resultado
    assert "28901-3" not in resultado
    assert "BB" in resultado


def test_chave_pix_email_e_telefone():
    assert "fulano@gmail.com" not in mascarar("chave pix: fulano@gmail.com")
    assert "99111-2233" not in mascarar("meu pix é (87) 99111-2233")


def test_pix_conhecido_sem_contexto():
    # A chave PIX da P004 é o telefone dela; deve sumir mesmo sem a palavra "pix"
    assert "(87) 99901-5567" not in mascarar("Fale com Ana: (87) 99901-5567")


def test_pix_sem_valor_nao_muda():
    texto = "manda o pix q eu transfiro agora"
    assert mascarar(texto) == texto


def test_nao_mascara_o_que_nao_e_sensivel():
    texto = "Queijo coalho 30kg, entrega 04/11/2026, total R$ 3.648,00. Contato (87) 3761-1234."
    assert mascarar(texto) == texto


def test_cnpj_nao_e_tratado_como_cpf():
    texto = "Nota fiscal no CNPJ 12.345.678/0001-90"
    assert mascarar(texto) == texto


def test_nenhum_dado_bancario_do_cadastro_sobrevive():
    prod = dados.produtores()
    for _, p in prod.iterrows():
        texto = f"{p['nome_completo']} CPF {p['cpf']} pix {p['chave_pix']} conta {p['conta_corrente']}"
        resultado = mascarar(texto)
        assert p["cpf"] not in resultado
        assert p["chave_pix"] not in resultado
        assert p["conta_corrente"] not in resultado
        assert p["nome_completo"] in resultado


def test_pedidos_com_cpf_ficam_limpos():
    with open(dados.PASTA_DADOS / "pedidos.json", encoding="utf-8") as f:
        pedidos = {p["id"]: p["mensagem_original"] for p in json.load(f)}
    assert "034.567.891-23" not in mascarar(pedidos["PED-2026-004"])
    assert "876.543.210-98" not in mascarar(pedidos["PED-2026-013"])
    assert "0437" not in mascarar(pedidos["PED-2026-012"])


def test_mascarar_dados_em_estruturas():
    resultado = mascarar_dados({"texto": "cpf 831.452.674-90", "itens": ["conta 28901-3", 10]})
    assert "831.452.674-90" not in resultado["texto"]
    assert "28901-3" not in resultado["itens"][0]
    assert resultado["itens"][1] == 10


def test_vazio():
    assert mascarar("") == ""
    assert mascarar(None) == ""
