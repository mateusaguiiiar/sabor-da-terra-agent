EXCLUIR_TITULOS = ["CPF", "CNPJ", "CREA-PE"]


def verificar_se_e_titulo(linha):
    if not linha:
        return False
    
    elif linha[0] in (" ", "=", "_", "\t"):
        return False

    
    titulo = ""
    for i in linha:
        if i == ":" or i == "(":
            break
        titulo += i
    titulo = titulo.strip()

    letras = 0 
    for j in titulo:
        if j.isalpha():
            letras += 1

    if letras < 3:
        return False

    if not titulo.isupper():
        return False

    if titulo in EXCLUIR_TITULOS:
        return False
    
    return True


def separar_titulo(linha):
    # separa a linha de título em (nome, resto).
    # o nome é o que vem antes do primeiro ":" ou "(" e o resto é o que sobra na linha
    for posicao, caractere in enumerate(linha):
        if caractere == ":":
            return linha[:posicao].strip(), linha[posicao + 1:].strip()
        if caractere == "(":
            return linha[:posicao].strip(), linha[posicao:].strip().rstrip(":").strip()
    return linha.strip(), ""


def dividir_em_secoes(texto):
    secoes = []
    nome_atual = "Cabeçalho"
    linhas_atuais = []

    for linha in texto.splitlines():
        if verificar_se_e_titulo(linha):
             # guarda a seção que tava sendo montada
            secao = {
                "nome": nome_atual,
                "texto": "\n".join(linhas_atuais).strip(),
            }
            secoes.append(secao)

            nome_atual, resto = separar_titulo(linha)
            linhas_atuais = []

            # se tem texto na mesma linha do título, ele é o começo da seção
            if resto != "":
                linhas_atuais.append(resto)
        else:
            # ignora linhas vazias e linhas de separação
            if linha.strip() == "":
                continue
            if linha[0] in ("=", "_"):
                continue
            linhas_atuais.append(linha)

    # guarda a última seção (depois do laço)
    secao = {
        "nome": nome_atual,
        "texto": "\n".join(linhas_atuais).strip(),
    }
    secoes.append(secao)

    return secoes



