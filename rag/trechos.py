import re

from rag import leitura, secoes
from rag.funcao_mascara import mascarar_texto  

# código de produtor: letra P seguida de 3 números (ex: P008)
# os (?<!...) e (?!...) garantem que nao é parte de outra palavra ou número
PADRAO_PRODUTOR = re.compile(r"(?<![A-Za-z0-9])P\d{3}(?![0-9])")


def achar_codigos(texto):
    # devolve a lista de códigos de produtor (P001, P002...) achados no texto, sem repetir.
    codigos = []
    for codigo in PADRAO_PRODUTOR.findall(texto):
        if codigo not in codigos:
            codigos.append(codigo)
    return codigos


def achar_titulo_documento(texto_cabecalho):
    # monta o título do documento com as linhas do cabeçalho que estão em MAIÚSCULAS
    partes = []
    for linha in texto_cabecalho.splitlines():
        linha = linha.strip()
        if linha != "" and linha.isupper():
            partes.append(linha)
    return " - ".join(partes)


def montar_trechos():
    # le os 20 documentos e devolve uma lista de trechos (um por seção).

    trechos = []

    for item in leitura.listar_arquivos():
        texto_documento = leitura.ler_texto(item["caminho"])
        lista_secoes = secoes.dividir_em_secoes(texto_documento)

        codigos_do_arquivo = achar_codigos(item["caminho"].name)
        titulo_documento = achar_titulo_documento(lista_secoes[0]["texto"])

        numero = 0
        for secao in lista_secoes:
            numero = numero + 1
            
            texto = mascarar_texto(secao["texto"])

            # produtores: os que aparecem na própria seção; se nenhum, os do nome do arquivo
            codigos = achar_codigos(texto)
            if len(codigos) == 0:
                codigos = codigos_do_arquivo
            produtores = ",".join(codigos)

            # texto usado só para gerar o embedding: o trecho com um prefixo de contexto
            prefixo = "Documento: " + titulo_documento
            prefixo = prefixo + " | Arquivo: " + item["arquivo"]
            if produtores != "":
                prefixo = prefixo + " | Produtores: " + produtores
            prefixo = prefixo + " | Seção: " + secao["nome"]
            texto_para_embedding = prefixo + "\n" + texto

            trecho = {
                "id": item["arquivo"] + "::" + str(numero).zfill(2),
                "arquivo": item["arquivo"],
                "tipo_doc": item["pasta"],
                "secao": secao["nome"],
                "texto": texto,
                "produtores": produtores,
                "titulo_documento": titulo_documento,
                "texto_para_embedding": texto_para_embedding,
            }
            trechos.append(trecho)

    return trechos