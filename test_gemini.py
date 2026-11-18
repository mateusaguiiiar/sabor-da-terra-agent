import os
import sys
import time
from dotenv import load_dotenv
from google import genai

print("1. Carregando variáveis do .env...")
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERRO: A chave GEMINI_API_KEY não foi encontrada!")
    sys.exit(1)
else:
    print(f"2. Chave encontrada com sucesso! (Início: {api_key[:5]}...)")

print("3. Inicializando o cliente GenAI...")
client = genai.Client(api_key=api_key)

max_tentativas = 3
sucesso = False

for tentativa in range(1, max_tentativas + 1):
    try:
        print(f"4. Tentativa {tentativa} de {max_tentativas} - Enviando requisição...")
        resposta = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents="Responda apenas: OK",
        )
        print("\n5. Sucesso absoluto!")
        print("Resposta do Gemini:", resposta.text)
        sucesso = True
        break
    except Exception as e:
        print(f"Servidor ocupado na tentativa {tentativa}: {e}")
        if tentativa < max_tentativas:
            print("Aguardando 3 segundos para tentar novamente...\n")
            time.sleep(3)

if not sucesso:
    print("\nERRO: Os servidores continuam com alta demanda após 3 tentativas.")