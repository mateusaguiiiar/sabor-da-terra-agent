"""
Script de avaliacao e integracao do modulo de triagem (Integrante 3 - Etapas D2, D3, D4 e D5).
Executa os 15 pedidos de data/pedidos.json em 3 rodadas seguidas (criterio de aceite da secao 7),
com cache em disco, reaplicando as validacoes em codigo e verificando conformidade com o schema
Pydantic congelado, gabarito das armadilhas da secao 9 e ausencia de dados sensiveis.

Uso:
    python test_triagem_15_pedidos.py               (executa 3 rodadas seguidas com cache da extracao)
    python test_triagem_15_pedidos.py --rodadas 1   (executa 1 rodada)
    python test_triagem_15_pedidos.py --sem-cache   (forca chamadas reais a API)
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

from tools.triagem import (
    TriagemResultado,
    _sem_acento,
    aplicar_validacoes_em_codigo,
    mascarar_saida,
    obter_metadados_congelamento,
    triar_pedido,
)

RAIZ_PROJETO = Path(__file__).resolve().parent
DATA_PATH = RAIZ_PROJETO / "data" / "pedidos.json"
CACHE_PATH = RAIZ_PROJETO / ".cache_triagem" / "cache_v1.json"

DADOS_SENSIVEIS_PROIBIDOS = (
    "034.567.891-23",
    "876.543.210-98",
    "432.198.765-01",
    "0437",
)

GABARITO_15_PEDIDOS: Dict[str, Dict[str, Any]] = {
    "PED-2026-001": {
        "tipos_esperados": {"pedido de compra"},
        "qtd_itens_esperada": 6,
        "deve_conter_alerta_data": True,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("p007", "domingo"),
    },
    "PED-2026-002": {
        "tipos_esperados": {"pedido de compra"},
        "qtd_itens_esperada": 8,
        "deve_conter_alerta_data": True,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("tercas e sextas", "abaixo da faixa"),
    },
    "PED-2026-003": {
        "tipos_esperados": {"pedido de compra"},
        "qtd_itens_esperada": 2,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": True,
        "armadilhas_esperadas": ("lotes.csv", "pix"),
    },
    "PED-2026-004": {
        "tipos_esperados": {"pedido de compra"},
        "qtd_itens_esperada": 9,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("p008", "contrato pnae"),
    },
    "PED-2026-005": {
        "tipos_esperados": {"pedido de compra"},
        "qtd_itens_esperada": 2,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": True,
        "armadilhas_esperadas": ("lotes.csv",),
    },
    "PED-2026-006": {
        "tipos_esperados": {"pedido de compra"},
        "qtd_itens_esperada": 4,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("nao existe contrato vigente", "capacidade", "p008"),
    },
    "PED-2026-007": {
        "tipos_esperados": {"cotacao", "pedido de compra"},
        "qtd_itens_esperada": 9,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("alerta de safra", "orcamento preliminar calculado em codigo"),
    },
    "PED-2026-008": {
        "tipos_esperados": {"cotacao", "consulta documental"},
        "qtd_itens_esperada": 2,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("p014",),
    },
    "PED-2026-009": {
        "tipos_esperados": {"cotacao"},
        "qtd_itens_esperada": 4,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("indisponibilidade de certificacao organica", "p008"),
    },
    "PED-2026-010": {
        "tipos_esperados": {"consulta documental", "cotacao"},
        "qtd_itens_esperada": 0,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("p008", "p004"),
    },
    "PED-2026-011": {
        "tipos_esperados": {"cotacao", "consulta documental"},
        "qtd_itens_esperada": 3,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("certificacao internacional", "indisponibilidade de certificacao organica", "ingles"),
    },
    "PED-2026-012": {
        "tipos_esperados": {"mensagem de produtor"},
        "qtd_itens_esperada": 0,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("bancarios", "financeiro.csv"),
    },
    "PED-2026-013": {
        "tipos_esperados": {"cotacao"},
        "qtd_itens_esperada": 7,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("safra de janeiro", "dap/caf", "capacidade"),
    },
    "PED-2026-014": {
        "tipos_esperados": {"notificacao oficial"},
        "qtd_itens_esperada": 0,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("cpf", "checklist para a equipe"),
    },
    "PED-2026-015": {
        "tipos_esperados": {"mensagem de produtor"},
        "qtd_itens_esperada": 2,
        "deve_conter_alerta_data": False,
        "deve_ter_pergunta": False,
        "armadilhas_esperadas": ("segunda intencao", "cruzamento de estoque", "cpf"),
    },
}


def _gerar_chave_cache(pid: str, texto: str, canal: str, remetente: str) -> str:
    payload = json.dumps(
        {"id": pid, "texto": texto, "canal": canal, "remetente": remetente},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _carregar_cache() -> Dict[str, Any]:
    if not CACHE_PATH.exists():
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _salvar_cache(cache: Dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def executar_avaliacao(usar_cache: bool = True, rodadas: int = 3) -> None:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        pedidos = json.load(f)

    cache = _carregar_cache() if usar_cache else {}
    meta_congelamento = obter_metadados_congelamento()
    rodadas = max(1, int(rodadas))

    print("------------------------------------------------------------")
    print("Avaliacao da triagem nos 15 pedidos (Integrante 3 - D2 a D5)")
    print(f"Modo cache: {'ativo' if usar_cache else 'ignorado (--sem-cache)'} | Rodadas seguidas: {rodadas}")
    print(
        f"Schema v{meta_congelamento['versao_schema']} (SHA-256: {meta_congelamento['hash_schema_sha256'][:12]}...) | "
        f"Prompt v{meta_congelamento['versao_prompt']} (SHA-256: {meta_congelamento['hash_prompt_sha256'][:12]}...)"
    )
    print("------------------------------------------------------------\n")

    metricas = {
        "total": len(pedidos),
        "rodadas": rodadas,
        "rodadas_100pct": 0,
        "schema_valido": 0,
        "sem_vazamento": 0,
        "tipo_correto": 0,
        "qtd_itens_correta": 0,
        "alerta_data_ok": 0,
        "alerta_data_total": 0,
        "pergunta_ok": 0,
        "pergunta_total": 0,
        "armadilhas_ok": 0,
        "armadilhas_total": 0,
        "chamadas_api": 0,
        "tempo_total": 0.0,
    }
    falhas = []

    for num_rodada in range(1, rodadas + 1):
        if rodadas > 1:
            print(f"=== Rodada {num_rodada}/{rodadas} ===")

        falhas_antes_rodada = len(falhas)

        for idx, p in enumerate(pedidos, start=1):
            pid = p.get("id", "")
            canal = p.get("canal", "")
            remetente = p.get("remetente") or p.get("comprador") or ""
            msg = p.get("mensagem_original", "")
            esperado = GABARITO_15_PEDIDOS[pid]

            chave = _gerar_chave_cache(pid, msg, canal, remetente)
            t0 = time.time()

            cache_valido = (
                usar_cache
                and chave in cache
                and "Falha de comunicacao com o servico de extracao." not in cache[chave].get("problemas", [])
            )
            if cache_valido:
                res_cache = TriagemResultado.model_validate(cache[chave])
                res_validado = aplicar_validacoes_em_codigo(
                    res_cache,
                    msg,
                    canal=canal,
                    remetente=remetente,
                )
                triagem = mascarar_saida(res_validado.model_dump())
                cache[chave] = triagem
                origem = "cache"
            else:
                triagem = triar_pedido(texto=msg, canal=canal, remetente=remetente)
                if "Falha de comunicacao com o servico de extracao." not in triagem.get("problemas", []):
                    cache[chave] = triagem
                metricas["chamadas_api"] += 1
                origem = "api"
                time.sleep(1.5)

            duracao = time.time() - t0
            metricas["tempo_total"] += duracao

            # 1. Validacao de schema Pydantic
            try:
                TriagemResultado.model_validate(triagem)
                schema_ok = True
                if num_rodada == 1:
                    metricas["schema_valido"] += 1
            except Exception as exc:
                schema_ok = False
                falhas.append(f"[R{num_rodada}] {pid}: schema invalido ({exc})")

            # 2. Verificacao de vazamento de dados sensiveis
            serializado = json.dumps(triagem, ensure_ascii=False)
            vazamentos = [d for d in DADOS_SENSIVEIS_PROIBIDOS if d in serializado]
            if not vazamentos:
                if num_rodada == 1:
                    metricas["sem_vazamento"] += 1
            else:
                falhas.append(f"[R{num_rodada}] {pid}: dado sensivel exposto na saida ({vazamentos})")

            # 3. Verificacao contra gabarito
            tipo = triagem.get("tipo_mensagem", "")
            itens = triagem.get("itens", [])
            problemas = triagem.get("problemas", [])
            perguntas = triagem.get("perguntas_de_esclarecimento", [])

            tipo_ok = tipo in esperado["tipos_esperados"]
            if tipo_ok:
                if num_rodada == 1:
                    metricas["tipo_correto"] += 1
            else:
                falhas.append(f"[R{num_rodada}] {pid}: tipo='{tipo}', esperado={sorted(esperado['tipos_esperados'])}")

            qtd_ok = len(itens) == esperado["qtd_itens_esperada"]
            if qtd_ok:
                if num_rodada == 1:
                    metricas["qtd_itens_correta"] += 1
            else:
                falhas.append(f"[R{num_rodada}] {pid}: qtd_itens={len(itens)}, esperado={esperado['qtd_itens_esperada']}")

            if esperado["deve_conter_alerta_data"]:
                if num_rodada == 1:
                    metricas["alerta_data_total"] += 1
                tem_alerta_data = any(
                    "inconsistencia" in _sem_acento(prob) or "divergencia" in _sem_acento(prob)
                    for prob in problemas
                )
                if tem_alerta_data:
                    if num_rodada == 1:
                        metricas["alerta_data_ok"] += 1
                else:
                    falhas.append(f"[R{num_rodada}] {pid}: nao sinalizou inconsistencia de data")

            if esperado["deve_ter_pergunta"]:
                if num_rodada == 1:
                    metricas["pergunta_total"] += 1
                if len(perguntas) > 0:
                    if num_rodada == 1:
                        metricas["pergunta_ok"] += 1
                else:
                    falhas.append(f"[R{num_rodada}] {pid}: nao gerou pergunta de esclarecimento esperada")

            armadilhas_esperadas = esperado.get("armadilhas_esperadas", ())
            if armadilhas_esperadas:
                if num_rodada == 1:
                    metricas["armadilhas_total"] += 1
                problemas_concat = _sem_acento(" | ".join(problemas))
                faltantes = [t for t in armadilhas_esperadas if _sem_acento(t) not in problemas_concat]
                if not faltantes:
                    if num_rodada == 1:
                        metricas["armadilhas_ok"] += 1
                    armadilha_ok = True
                else:
                    armadilha_ok = False
                    falhas.append(f"[R{num_rodada}] {pid}: armadilha(s) D3/D4 ausente(s) em 'problemas': {faltantes}")
            else:
                armadilha_ok = True

            if num_rodada == 1 or not (schema_ok and tipo_ok and qtd_ok and armadilha_ok and not vazamentos):
                print(
                    f"[{idx:02d}/15] {pid} | origem={origem} | tempo={duracao:.2f}s | "
                    f"tipo={tipo} ({'OK' if tipo_ok else 'FALHA'}) | "
                    f"itens={len(itens)}/{esperado['qtd_itens_esperada']} ({'OK' if qtd_ok else 'FALHA'}) | "
                    f"regras={'OK' if armadilha_ok else 'FALHA'} | "
                    f"schema={'OK' if schema_ok else 'FALHA'} | vazamento={'NAO' if not vazamentos else 'SIM'}"
                )

        if len(falhas) == falhas_antes_rodada:
            metricas["rodadas_100pct"] += 1
            if rodadas > 1:
                print(f"-> Rodada {num_rodada}/{rodadas}: 15/15 JSON validos e 100% aprovados.\n")

    _salvar_cache(cache)

    total = metricas["total"]
    print("------------------------------------------------------------")
    print("Resumo da avaliacao contra gabarito (D2 a D5):")
    print("------------------------------------------------------------")
    print(f"Rodadas seguidas 100% OK:   {metricas['rodadas_100pct']}/{rodadas} ({metricas['rodadas_100pct'] * total}/{rodadas * total} execucoes)")
    print(f"Schema JSON valido:         {metricas['schema_valido']}/{total}")
    print(f"Sem vazamento de sensiveis: {metricas['sem_vazamento']}/{total}")
    print(f"Tipo de mensagem correto:   {metricas['tipo_correto']}/{total}")
    print(f"Contagem de itens exata:    {metricas['qtd_itens_correta']}/{total}")
    print(f"Alertas de data:            {metricas['alerta_data_ok']}/{metricas['alerta_data_total']}")
    print(f"Perguntas de ambiguidade:   {metricas['pergunta_ok']}/{metricas['pergunta_total']}")
    print(f"Armadilhas D3/D4 sinaliz.:  {metricas['armadilhas_ok']}/{metricas['armadilhas_total']}")
    print(f"Chamadas reais a API:       {metricas['chamadas_api']}")
    print(f"Tempo total:                {metricas['tempo_total']:.2f}s")

    if falhas:
        print("\nDivergencias encontradas:")
        for falha in falhas:
            print(f"  - {falha}")
        print("------------------------------------------------------------")
        sys.exit(1)
    else:
        print("\nTodas as verificacoes foram aprovadas.")
        print("------------------------------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Avaliacao do modulo de triagem nos 15 pedidos.")
    parser.add_argument("--sem-cache", action="store_true", help="Ignora o cache local e consulta a API.")
    parser.add_argument(
        "--rodadas",
        type=int,
        default=3,
        help="Numero de rodadas consecutivas sobre os 15 pedidos (padrao: 3).",
    )
    args = parser.parse_args()
    executar_avaliacao(usar_cache=not args.sem_cache, rodadas=args.rodadas)
