import json
import time
from pathlib import Path

# Definir caminhos
PASTA_EVAL = Path(__file__).parent
ARQUIVO_GABARITO = PASTA_EVAL / "gabarito_v0.json"
ARQUIVO_RELATORIO = PASTA_EVAL / "relatorio_rodada1.txt"

def carregar_gabarito():
    with open(ARQUIVO_GABARITO, "r", encoding="utf-8") as f:
        return json.load(f)

def simular_chamada_agente(mensagem):
    """Substituir pela chamada real do agente quando o Integrante 1 entregar."""
    inicio = time.time()
    time.sleep(1.5)  # Simula latência
    # Resposta estática de mock para não quebrar o teste
    resposta = "Mock: Resposta simulada para a avaliação."
    tempo_execucao = time.time() - inicio
    return resposta, tempo_execucao

def rodar_testes():
    dados = carregar_gabarito()
    resultados = []
    tempo_total = 0
    total_casos = 0

    print("🚀 A iniciar avaliação do Assistente...\n")

    # 1. Testar Pedidos
    print("📦 A avaliar Pedidos...")
    for pedido in dados.get("pedidos", []):
        resposta, tempo = simular_chamada_agente(pedido["mensagem"])
        tempo_total += tempo
        total_casos += 1
        resultados.append(f"[PEDIDO] {pedido['id']} | Tempo: {tempo:.2f}s | Status: Executado")

    # 2. Testar Perguntas Documentais
    print("📄 A avaliar Perguntas sobre Documentos...")
    for pergunta in dados.get("perguntas_documentais_e_dados", []):
        resposta, tempo = simular_chamada_agente(pergunta["pergunta"])
        tempo_total += tempo
        total_casos += 1
        resultados.append(f"[DOCS] '{pergunta['pergunta'][:30]}...' | Tempo: {tempo:.2f}s | Status: Executado")

    # 3. Testar Segurança
    print("🔒 A avaliar Segurança...")
    for seguranca in dados.get("seguranca", []):
        resposta, tempo = simular_chamada_agente(seguranca["cenario"])
        tempo_total += tempo
        total_casos += 1
        resultados.append(f"[SEGURANÇA] Cenário: '{seguranca['cenario'][:30]}...' | Tempo: {tempo:.2f}s | Status: Executado")

    # Gerar Relatório
    tempo_medio = tempo_total / total_casos if total_casos > 0 else 0
    
    resumo = (
        "=======================================\n"
        "📊 RELATÓRIO DE AVALIAÇÃO - RODADA 1\n"
        "=======================================\n"
        f"Total de casos testados: {total_casos}\n"
        f"Tempo total de execução: {tempo_total:.2f}s\n"
        f"Tempo médio por resposta: {tempo_medio:.2f}s\n\n"
        "DETALHES:\n"
    )
    resumo += "\n".join(resultados)

    with open(ARQUIVO_RELATORIO, "w", encoding="utf-8") as f:
        f.write(resumo)

    print("\n✅ Avaliação concluída!")
    print(f"Relatório guardado em: {ARQUIVO_RELATORIO}")

if __name__ == "__main__":
    rodar_testes()