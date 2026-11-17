# sabor-da-terra-agent

## Como rodar o projeto

**1. Crie e ative o ambiente virtual:**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # No Windows (PowerShell)
# ou: source .venv/bin/activate # No Linux/Mac

pip install streamlit
# (Em breve: pip install -r requirements.txt)

# Para abrir a interface do chat:
streamlit run ui/app.py

# Para rodar os testes automatizados:
python eval/rodar_avaliacao.py

