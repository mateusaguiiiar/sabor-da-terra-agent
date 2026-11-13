import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERRO: A chave GEMINI_API_KEY não foi encontrada no .env!")
    exit(1)

client = genai.Client(api_key=api_key)

max_tentativas = 3
sucesso = False

for tentativa in range(1, max_tentativas + 1):
    try:
        print(f"Tentativa {tentativa} de {max_tentativas} - Enviando requisição para o Gemini...")
        resposta = client.models.generate_content(
            model="gemini-3.8-flash",
            contents="Diga 'Teste de infraestrutura concluído com sucesso' em português.",
        )
        print("\nResposta recebida com sucesso!")
        print(resposta.text)
        sucesso = True
        break
    except Exception as e:
        print(f"Servidor ocupado (tentativa {tentativa}): {e}")
        if tentativa < max_tentativas:
            print("Aguardando 3 segundos para tentar novamente...\n")
            time.sleep(3)

if not sucesso:
    print("\nOs servidores continuam com alta demanda. Tente rodar o script novamente em alguns minutos.")